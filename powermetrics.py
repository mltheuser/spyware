import os
import platform
import shutil
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime


def parse_xml(xml_string):
    try:
        root = ET.fromstring(xml_string)

        result = parseXmlObjToDict(root[0])

        return result
    except ET.ParseError as e:
        print(f"Error parsing xml at line {e.position[0]}, column {e.position[1]}")
        raise e


def parseXmlObjToDict(xmlObj):
    result = {}

    pointer = 0
    while pointer < len(xmlObj):
        key_element = xmlObj[pointer]
        assert key_element.tag == 'key'

        value_element = xmlObj[pointer + 1]

        if value_element.tag in 'integer':
            result[key_element.text] = int(value_element.text)
        elif value_element.tag in 'real':
            result[key_element.text] = float(value_element.text)
        elif value_element.tag in 'string':
            result[key_element.text] = str(value_element.text)
        elif value_element.tag in 'array':
            result[key_element.text] = [parseXmlObjToDict(obj) for obj in value_element]
        elif value_element.tag in 'dict':
            result[key_element.text] = parseXmlObjToDict(value_element)
        else:
            result[key_element.text] = value_element.tag

        pointer += 2

    return result


def energy_impact_to_co2_emission(energy_impact):
    energy_impact_in_MWHr = energy_impact * 2.8 * 1e-13
    energy_impact_in_US_co2_emission = energy_impact_in_MWHr * 0.475

    return energy_impact_in_US_co2_emission


def powermetrics_daemon(callback, report_interval=60):
    process_map = defaultdict(lambda: {'power': 0, 'samples': 0})
    start_time = None

    def aggregate_and_callback():
        nonlocal start_time
        while True:
            if start_time is None:
                start_time = datetime.now()

            time.sleep(report_interval)
            stop_time = datetime.now()


            aggregated_task_data = [
                {'command': command, 'co2_emission': energy_impact_to_co2_emission(data['power'])}
                for command, data in process_map.items()
                if data['samples'] > 0 and data['power'] > 0
            ]
            callback({
                'tasks': aggregated_task_data,
                'start_time': start_time.strftime("%Y-%m-%d %H:%M:%S"),
                'stop_time': stop_time.strftime("%Y-%m-%d %H:%M:%S"),
                'OS': platform.platform(),
            })
            process_map.clear()
            start_time = stop_time  # Set start time for next interval to current stop time

    # Start the aggregation thread
    threading.Thread(target=aggregate_and_callback, daemon=True).start()

    # Run the top command
    cmd = ['top', '-stats', 'command,power', '-o', 'power', '-d']
    try:
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1,
                              universal_newlines=True) as process:
            # Skip header lines
            for _ in range(10):
                next(process.stdout, None)

            # Process the output
            for line in process.stdout:
                line = line.strip()
                if any(char in line for char in ',:/'):
                    continue

                parts = line.split()
                if len(parts) >= 2:
                    try:
                        command = ' '.join(parts[:-1])
                        power = float(parts[-1])
                        process_map[command]['power'] += power
                        process_map[command]['samples'] += 1
                    except ValueError:
                        continue  # Skip lines where power can't be converted to float

    except subprocess.CalledProcessError as e:
        print(f"Error running top command: {e}")
    except KeyboardInterrupt:
        print("Daemon stopped by user.")
    finally:
        print("Powermetrics daemon has stopped.")
