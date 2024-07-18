import os
import sqlite3
import stat

# TODO: this is mac specific!!!
# Define the application directory
app_dir = '/Library/Application Support/PowerObserver'
# Create the application directory if it doesn't exist
os.makedirs(app_dir, exist_ok=True)
os.chmod(app_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
# Define the database file path
db_path = os.path.join(app_dir, 'energy_measurements.db')

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Create the tables
with open('local_db_schema.sql', 'r') as schema_file:
    schema_sql = schema_file.read()
    c.executescript(schema_sql)
    conn.commit()


# Function to save a measurement
def save(report):
    # Insert the metadata
    c.execute("INSERT INTO Interval (pc_id, start_time, stop_time, total_energy_consumption, platform) VALUES (?, ?, ?, ?, ?)",
              (report['pc_id'], report['start_time'], report['stop_time'], report['total_energy_consumption'], report['platform']))
    interval_id = c.lastrowid

    # Insert the total consumption
    for task_data in report['tasks']:
        c.execute(f"SELECT * from Task WHERE task_name = '{task_data['task_name']}'")
        existing_task = c.fetchone()

        if not existing_task:
            c.execute("INSERT INTO Task (task_name, icon) VALUES (?, ?)", (task_data['task_name'], task_data['details']['icon']))

        c.execute("INSERT INTO TaskConsumption (energy_consumption, task_name, interval_id) VALUES (?, ?, ?)",
                  (task_data['energy_consumption'], task_data['task_name'], interval_id))

    conn.commit()


MAC_URL = "http://localhost:8090/powermetrics"


def push(report):
    print(report)
    # r = requests.post(MAC_URL, data=json.dumps(report))
    # print(r.text)
    save(report)
