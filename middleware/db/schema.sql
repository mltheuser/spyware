-- schema.sql
CREATE TABLE TotalConsumption (
                                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                                  combined_power FLOAT NOT NULL,
                                  start_time DATETIME NOT NULL,
                                  stop_time DATETIME NOT NULL,
                                  platform VARCHAR(255) NOT NULL
);