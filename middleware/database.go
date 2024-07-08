package main

import (
	"fmt"
	"log"
	"net/url"

	"github.com/jmoiron/sqlx"
)

const sqliteDB = "db/test.db"

func GetSqliteConnection() *sqlx.DB {
	db, err := sqlx.Open("sqlite3", sqliteDB)
	if err != nil {
		log.Fatal(err)
	}
	log.Println("Connected to Sqlite database")
	return db
}

// TODO: get from env var
const (
	sqlServer_driver        = "sqlserver"
	sqlServer_database_name = ""
	sqlServer_user          = ""
	sqlServer_password      = ""
	sqlServer_host          = ""
	sqlServer_port          = ""
)

func GetSqlServerConnection() *sqlx.DB {
	query := url.Values{}
	query.Add("database", sqlServer_database_name)

	connectionURL := &url.URL{
		Scheme:   sqlServer_driver,
		User:     url.UserPassword(sqlServer_user, sqlServer_password),
		Host:     fmt.Sprintf("%s:%s", sqlServer_host, sqlServer_port),
		RawQuery: query.Encode(),
	}
	db, err := sqlx.Open(sqlServer_driver, connectionURL.String())
	if err != nil {
		log.Fatal(err)
	}
	log.Println("Connected to Sql Server database")
	return db
}
