package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/jmoiron/sqlx"
)

type task struct {
	Command string  `json:"command"`
	Power   float32 `json:"power"`
}

type powermetricsData struct {
	PcId          string     `json:"pc_id"`
	CombinedPower float32    `json:"combined_power"`
	Tasks         []task     `json:"tasks"`
	StartTime     customTime `json:"start_time"`
	StopTime      customTime `json:"stop_time"`
	Platform      string     `json:"platform"`
}

const formatString = "2006-01-02 15:04:05"
const parseJSONString = "\"2006-01-02 15:04:05\""

type customTime struct {
	t time.Time
}

func (d customTime) MarshalJSON() ([]byte, error) {
	return []byte("\"" + d.t.Format(formatString) + "\""), nil
}

func (d *customTime) UnmarshalJSON(b []byte) (err error) {
	t, err := time.ParseInLocation(parseJSONString, string(b), time.UTC)
	if err != nil {
		return
	}
	*d = customTime{t}
	return
}

var (
	insertTotalConsumptionQuery = fmt.Sprintf(`
		INSERT INTO TotalConsumption (combined_power, start_time, stop_time, platform, pc_id)
		VALUES (@p1, @p2, @p3, @p4, @p5)
		`)
	insertTaskConsumptionQuery = fmt.Sprintf(`
		INSERT INTO TaskConsumption (task_name, power, start_time, stop_time, platform, pc_id)
		VALUES (@p1, @p2, @p3, @p4, @p5, @p6)
		`)
	entryWithSameStartTimeExistsQuery = fmt.Sprintf(`
		SELECT EXISTS(SELECT 1 FROM TotalConsumption WHERE pc_id=@p1 AND start_time=@p2);
		`)
)

type PowermetricsService struct {
	db *sqlx.DB
}

func (ps *PowermetricsService) writePowermetricsToDB(w http.ResponseWriter, req *http.Request) {
	var p powermetricsData

	// Check if the request body is empty
	if req.Body == nil {
		http.Error(w, "Request body is empty", http.StatusBadRequest)
		return
	}

	// Limit the size of the request body to prevent potential DoS attacks
	req.Body = http.MaxBytesReader(w, req.Body, 1048576) // 1 MB limit

	dec := json.NewDecoder(req.Body)
	dec.DisallowUnknownFields() // Stricter parsing

	err := dec.Decode(&p)
	if err != nil {
		var syntaxError *json.SyntaxError
		var unmarshalTypeError *json.UnmarshalTypeError
		var invalidUnmarshalError *json.InvalidUnmarshalError

		switch {
		case errors.As(err, &syntaxError):
			msg := fmt.Sprintf("Request body contains badly-formed JSON (at position %d)", syntaxError.Offset)
			http.Error(w, msg, http.StatusBadRequest)
		case errors.Is(err, io.ErrUnexpectedEOF):
			msg := "Request body contains badly-formed JSON"
			http.Error(w, msg, http.StatusBadRequest)
		case errors.As(err, &unmarshalTypeError):
			msg := fmt.Sprintf("Request body contains an invalid value for the %q field (at position %d)", unmarshalTypeError.Field, unmarshalTypeError.Offset)
			http.Error(w, msg, http.StatusBadRequest)
		case errors.As(err, &invalidUnmarshalError):
			panic(err) // This shouldn't happen if we provided a valid struct
		case strings.HasPrefix(err.Error(), "json: unknown field "):
			fieldName := strings.TrimPrefix(err.Error(), "json: unknown field ")
			msg := fmt.Sprintf("Request body contains unknown field %s", fieldName)
			http.Error(w, msg, http.StatusBadRequest)
		case errors.Is(err, io.EOF):
			msg := "Request body must not be empty"
			http.Error(w, msg, http.StatusBadRequest)
		case err.Error() == "http: request body too large":
			msg := "Request body must not be larger than 1MB"
			http.Error(w, msg, http.StatusRequestEntityTooLarge)
		default:
			log.Printf("Error decoding JSON: %v", err)
			http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
		}
		return
	}

	// Check for additional JSON data
	if dec.More() {
		msg := "Request body must only contain a single JSON object"
		http.Error(w, msg, http.StatusBadRequest)
		return
	}

	// Validate powermetric data
	validators := []func(powermetricsData) error{
		ValidateTimestamp,
		ValidateConsumption,
		ValidateTasks,
	}

	err = ValidatePowermetricsData(p, validators)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
	}

	// Start database transaction for write
	tx, err := ps.db.Beginx()
	if err != nil {
		if rollbackErr := tx.Rollback(); rollbackErr != nil {
			http.Error(w, rollbackErr.Error(), http.StatusInternalServerError)
		}
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Check for entry with same start time and pc id
	var entryWithSameStartTimeExists bool
	err = tx.QueryRow(entryWithSameStartTimeExistsQuery, p.PcId, p.StartTime.t).Scan(&entryWithSameStartTimeExists)
	if err != nil || entryWithSameStartTimeExists {
		log.Printf("entryWithSameStartTimeExists %v", entryWithSameStartTimeExists)
		if rollbackErr := tx.Rollback(); rollbackErr != nil {
			http.Error(w, rollbackErr.Error(), http.StatusInternalServerError)
		}
		if entryWithSameStartTimeExists {
			http.Error(w, fmt.Sprintf("Exists powermetrics entry with the same start time"), http.StatusBadRequest)
		}
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
		}
		return
	}

	// Insert into TotalConsumption table
	tx.MustExec(insertTotalConsumptionQuery, p.CombinedPower, p.StartTime.t, p.StopTime.t, p.Platform, p.PcId)

	// Insert into TaskConsumption table
	for _, task := range p.Tasks {
		tx.MustExec(insertTaskConsumptionQuery, task.Command, task.Power, p.StartTime.t, p.StopTime.t, p.Platform, p.PcId)
	}

	// Commit transaction
	err = tx.Commit()
	if err != nil {
		if rollbackErr := tx.Rollback(); rollbackErr != nil {
			http.Error(w, rollbackErr.Error(), http.StatusInternalServerError)
		}
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Respond with success
	w.WriteHeader(http.StatusCreated)

	// Create a human-readable JSON representation of the powermetricsData
	prettyJSON, err := json.MarshalIndent(p, "", "  ")
	if err != nil {
		log.Printf("Error creating pretty JSON: %v", err)
		http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
		return
	}
	// Print the pretty JSON to the console
	fmt.Println("Decoded and validated powermetricsData:")
	fmt.Println(string(prettyJSON))
}
