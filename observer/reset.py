import os
import subprocess
import time
 
def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error message: {e}")
 
def reset_measurements():
    # Stop the Diagnostic Policy Service
    run_command("sc stop dps")
    # Wait for the service to stop
    time.sleep(5)
    # Change directory and remove the SRU database file
    sru_path = r"C:\Windows\System32\sru"
    sru_file = os.path.join(sru_path, "SRUDB.dat")
    if os.path.exists(sru_file):
        try:
            os.remove(sru_file)
            print("SRUDB.dat file removed successfully.")
        except PermissionError:
            print("Permission denied. Make sure you're running the script as administrator.")
        except Exception as e:
            print(f"Error removing file: {e}")
    else:
        print("SRUDB.dat file not found.")
    # Start the Diagnostic Policy Service
    run_command("sc start dps")