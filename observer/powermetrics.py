import os
import platform
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from battery_info import get_battery_info
from id import generate_encoded_device_id


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


def gather_metrics_per_task(report, total_power):
    metrics = []
    for task in report['tasks']:
        task_specific_metrics = {
            'task_name': task['name'].lower(),
            'energy_consumption': estimate_energy_impact_per_process(task, report, total_power)
        }
        metrics.append(task_specific_metrics)
    return metrics


def estimate_energy_impact_per_process(task, report, total_power):
    # Get the total CPU energy from the processor section
    total_energy_impact = report['all_tasks']['energy_impact']

    # Calculate the CPU time ratio for this task
    energy_impact_ratio = task['energy_impact'] / total_energy_impact

    # Estimate the energy impact for this task
    relative_energy_impact = energy_impact_ratio

    # Imagine this is in Joule then
    energy_impact = relative_energy_impact * total_power

    return energy_impact


def _has_powermetrics_sudo():
    # Check if sudo is available
    if shutil.which("sudo") is None:
        print("sudo not available, we won't use Apple PowerMetrics.")
        return False

    # Check if powermetrics is available
    if shutil.which("powermetrics") is None:
        print("Apple PowerMetrics not available. Please install it if you are using an Apple product.")
        return False

    # Check if the script runs with sudo privileges
    if os.geteuid() != 0:
        print("Needs to be run with sudo privileges.")
        return False

    # Try to run powermetrics with sudo
    try:
        process = subprocess.run(
            [
                "sudo", "-n",  # -n option to prevent prompting for password
                "powermetrics",
                "--samplers", "cpu_power",
                "-n", "1",
                "-i", "1",
                "-o", "/dev/null",
            ],
            capture_output=False,
            text=True,
            timeout=5  # Set a timeout to prevent hanging
        )

        # Check the return code
        if process.returncode != 0:
            print(f"Failed to execute powermetrics. Return code: {process.returncode}")
            return False

        return True

    except subprocess.TimeoutExpired:
        print("Timeout while executing powermetrics.")
        return False
    except Exception as e:
        print(f"An error occurred while checking PowerMetrics: {str(e)}")
        return False


def filter_tasks_in(report):
    # filter tasks
    current_pid = os.getpid()
    tasks = report.get('tasks', [])

    # Find the current task and remove it from the list
    current_task_data = None
    filtered_tasks = []
    for task in tasks:
        if task.get('pid') == current_pid:
            current_task_data = task
        else:
            filtered_tasks.append(task)

    # Sort the filtered tasks by 'energy_impact' in descending order
    filtered_tasks.sort(key=lambda x: x.get('energy_impact', 0), reverse=True)

    # Take the first 10 elements from the filtered tasks
    top_10_tasks = filtered_tasks[:10]

    # Append the current task data to the end if it exists
    if current_task_data:
        current_task_data['name'] = 'Power Observer'
        top_10_tasks.append(current_task_data)

    # Update the report with the new task list
    report['tasks'] = top_10_tasks

    return report


def compute_energy_consumption(start_battery, battery_info):
    # The amount of Joules consumed from the power socket
    power_from_wall = (battery_info['PowerTelemetryData']['AccumulatedWallEnergyEstimate'] -
                       start_battery['PowerTelemetryData']['AccumulatedWallEnergyEstimate']) * 3.6 / 1000

    # The amount of Joules reaching the system
    power_consumed = (battery_info['PowerTelemetryData']['AccumulatedSystemEnergyConsumed'] -
                      start_battery['PowerTelemetryData']['AccumulatedSystemEnergyConsumed']) * 3.6 / 1000

    # There is some small loss in between that we account for
    power_inefficiency = power_from_wall - power_consumed

    # in mAH * mV -> Joules
    new_battery_charge = battery_info['AppleRawCurrentCapacity'] * (battery_info['Voltage'] / 1000) * 3.6
    old_battery_charge = start_battery['AppleRawCurrentCapacity'] * (start_battery['Voltage'] / 1000) * 3.6
    power_diff_battery = new_battery_charge - old_battery_charge

    power_used_up = power_consumed - power_diff_battery

    print(
        f'Drew {power_from_wall} Joule from Wall. Of which {power_consumed} Joule reached the system and {power_inefficiency} Joule were lost. A change of {power_diff_battery} Joule are registered in the battery with {new_battery_charge} Joule remaining. While {power_used_up} Joule were used up.')

    return power_used_up + power_inefficiency


def powermetrics_daemon(callback, report_interval=60):
    if not _has_powermetrics_sudo():
        return

    pc_id = generate_encoded_device_id()

    interval_milli_seconds = report_interval * 1000
    process = subprocess.Popen(
        ['sudo', 'powermetrics', '-i', str(interval_milli_seconds), '--show-process-energy', '--format', 'plist'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    xml_output = []
    start_time = datetime.now()
    start_battery = get_battery_info()

    while True:
        line = process.stdout.readline()
        if not line:
            break

        xml_output.append(line)

        if line.strip().endswith('</plist>'):
            xml_string = ''.join(xml_output)

            stop_time = datetime.now()

            try:
                battery_info = get_battery_info()
                total_power_consumption = compute_energy_consumption(start_battery, battery_info)

                report = parse_xml(xml_string.lstrip('\x00').strip().encode('utf-8'))

                report = filter_tasks_in(report)

                task_metrics = gather_metrics_per_task(report, total_power_consumption)

                callback({
                    'pc_id': pc_id,
                    'total_energy_consumption': total_power_consumption,
                    'tasks': task_metrics,
                    'start_time': format_time(start_time),
                    'stop_time': format_time(stop_time),
                    'platform': platform.platform(),
                })

                pass
            except Exception as e:
                print(f"Unexpected error in sample: {e}")
                break

            finally:
                xml_output = []
                start_time = stop_time
                start_battery = get_battery_info()

    process.stdout.close()
    process.stderr.close()
    return_code = process.wait()

    if return_code != 0:
        print(f"powermetrics process exited with return code {return_code}")


def format_time(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")