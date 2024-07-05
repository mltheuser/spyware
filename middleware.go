package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type task struct {
	Command string  `json:"command"`
	Power   float64 `json:"power"`
}

type powermetricsData struct {
	Tasks     []task     `json:"tasks"`
	StartTime customTime `json:"start_time"`
	StopTime  customTime `json:"stop_time"`
	OS        string     `json:"OS"`
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
	err := json.NewDecoder(req.Body).Decode(&p)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	// TODO: validate (timestamp?)
	// TODO: write to DB
	fmt.Fprintf(w, "payload: %v", p)
}

func main() {
	http.HandleFunc("/powermetrics", writePowermetricsToDB)
	http.ListenAndServe(":8090", nil)
}
