-- schema.sql
CREATE TABLE IF NOT EXISTS Interval
(
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    pc_id                    VARCHAR(255) NOT NULL,
    start_time               DATETIME     NOT NULL,
    stop_time                DATETIME     NOT NULL,
    total_energy_consumption FLOAT        NOT NULL,
    platform                 VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS Task
(
    task_name VARCHAR(255) PRIMARY KEY,
    icon      BLOB
);

CREATE TABLE IF NOT EXISTS TaskConsumption
(
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name          VARCHAR(255) NOT NULL,
    interval_id        INTEGER      NOT NULL,
    energy_consumption FLOAT        NOT NULL,
    FOREIGN KEY (task_name) REFERENCES Task (task_name),
    FOREIGN KEY (interval_id) REFERENCES Interval (id)
);