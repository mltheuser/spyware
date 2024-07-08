package main

import (
	"fmt"
	"net/http"

	_ "github.com/mattn/go-sqlite3"
)

func main() {
	fmt.Println("started")

	// Open the database
	db := GetSqliteConnection()
	defer db.Close()

	powermetricsService := PowermetricsService{db}

	http.HandleFunc("/powermetrics", powermetricsService.writePowermetricsToDB)
	http.ListenAndServe(":8090", nil)
}
