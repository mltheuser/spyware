import os
import sqlite3

# TODO: this is mac specific!!!
# Define the application directory
app_dir = '/Library/Application Support/Power Observer'
# Create the application directory if it doesn't exist
os.makedirs(app_dir, exist_ok=True)
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
    c.execute("INSERT INTO MetaData (start_time, stop_time, platform, pc_id) VALUES (?, ?, ?, ?)",
              (report['start_time'], report['stop_time'], report['platform'], report['pc_id']))
    metadata_id = c.lastrowid

    # Insert the total consumption
    c.execute("INSERT INTO TotalConsumption (total_energy_consumption, metadata_id) VALUES (?, ?)",
              (report['total_energy_consumption'], metadata_id))

    # Insert the task consumption
    for task_data in report['tasks']:
        c.execute("INSERT INTO TaskConsumption (task_name, energy_consumption, metadata_id) VALUES (?, ?, ?)",
                  (task_data['task_name'], task_data['energy_consumption'], metadata_id))

    conn.commit()


MAC_URL = "http://localhost:8090/powermetrics"


def push(report):
    # r = requests.post(MAC_URL, data=json.dumps(report))
    # print(r.text)
    save(report)
