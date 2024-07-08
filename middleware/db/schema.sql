-- schema.sql
CREATE TABLE TotalConsumption
(
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    combined_power FLOAT        NOT NULL,
    start_time     DATETIME     NOT NULL,
    stop_time      DATETIME     NOT NULL,
    platform       VARCHAR(255) NOT NULL,
    pc_id          VARCHAR(255) NOT NULL
);

CREATE TABLE TaskConsumption
(
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name  VARCHAR(255) NOT NULL,
    power      FLOAT        NOT NULL,
    start_time DATETIME     NOT NULL,
    stop_time  DATETIME     NOT NULL,
    platform   VARCHAR(255) NOT NULL,
    pc_id      VARCHAR(255) NOT NULL
);

-- Insert example rows into TotalConsumption
INSERT INTO TotalConsumption (combined_power, start_time, stop_time, platform, pc_id)
VALUES (150.5, '2023-06-01 08:00:00', '2023-06-01 17:00:00', 'Windows', 'PC001'),
       (120.3, '2023-06-02 09:00:00', '2023-06-02 18:00:00', 'MacOS', 'PC002'),
       (180.7, '2023-06-03 07:30:00', '2023-06-03 16:30:00', 'Linux', 'PC003');

-- Insert example rows into TaskConsumption
INSERT INTO TaskConsumption (task_name, power, start_time, stop_time, platform, pc_id)
VALUES ('Compiling', 75.2, '2023-06-01 10:00:00', '2023-06-01 10:30:00', 'Windows', 'PC001'),
       ('Data Analysis', 50.8, '2023-06-02 11:00:00', '2023-06-02 12:00:00', 'MacOS', 'PC002'),
       ('Video Rendering', 100.5, '2023-06-03 09:00:00', '2023-06-03 10:00:00', 'Linux', 'PC003'),
       ('Web Browsing', 30.1, '2023-06-01 14:00:00', '2023-06-01 15:00:00', 'Windows', 'PC001'),
       ('Software Testing', 60.4, '2023-06-02 15:00:00', '2023-06-02 16:30:00', 'MacOS', 'PC002');