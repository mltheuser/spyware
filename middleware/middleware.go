package main

import (
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"net/http"
	"strings"
	"time"

	_ "github.com/mattn/go-sqlite3"
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

type customTime time.Time

func (d customTime) MarshalJSON() ([]byte, error) {
	return []byte("\"" + time.Time(d).Format(formatString) + "\""), nil
}

func (d *customTime) UnmarshalJSON(b []byte) (err error) {
	t, err := time.ParseInLocation(parseJSONString, string(b), time.UTC)
	if err != nil {
		return
	}
	*d = customTime(t)
	return
}

func writePowermetricsToDB(w http.ResponseWriter, req *http.Request) {
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

	// TODO: Validate
	// ...

	// TODO: Write to DB
	// Implement your database write logic here

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

func main() {
	fmt.Println("started")

	// Open the database
	db, err := sql.Open("sqlite3", "./test.db")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	http.HandleFunc("/powermetrics", writePowermetricsToDB)
	http.ListenAndServe(":8090", nil)
}
