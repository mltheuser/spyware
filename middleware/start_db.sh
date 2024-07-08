#!/bin/bash

# Path to your database
DB_PATH="db/test.db"

# Check if the database file exists
if [ -f "$DB_PATH" ]; then
    # Get a list of all tables
    TABLES=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table';")

    # Drop all tables
    for TABLE in $TABLES
    do
        sqlite3 "$DB_PATH" "DROP TABLE IF EXISTS $TABLE;"
    done
    echo "Existing tables dropped."
else
    echo "Database file does not exist. A new one will be created."
fi

# Apply the schema
sqlite3 "$DB_PATH" < db/schema.sql
echo "Schema applied."

# Open the SQLite shell
sqlite3 "$DB_PATH"