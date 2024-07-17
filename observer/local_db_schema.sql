-- schema.sql
CREATE TABLE IF NOT EXISTS TotalConsumption
(
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    total_energy_consumption FLOAT   NOT NULL,
    metadata_id    INTEGER NOT NULL,
    FOREIGN KEY (metadata_id) REFERENCES MetaData (id)
);

CREATE TABLE IF NOT EXISTS TaskConsumption
(
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name     VARCHAR(255) NOT NULL,
    energy_consumption FLOAT        NOT NULL,
    metadata_id   INTEGER      NOT NULL,
    FOREIGN KEY (metadata_id) REFERENCES MetaData (id)
);

CREATE TABLE IF NOT EXISTS MetaData
(
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME     NOT NULL,
    stop_time  DATETIME     NOT NULL,
    platform   VARCHAR(255) NOT NULL,
    pc_id      VARCHAR(255) NOT NULL
);