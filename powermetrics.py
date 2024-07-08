import os
import platform
import select
import shutil
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime

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


def gather_metrics_per_task(report):
    metrics = []
    for task in report['tasks']:
        task_specific_metrics = {'command': task['name']}
        task_specific_metrics['power'] = estimate_energy_impact_per_process(task, report)
        metrics.append(task_specific_metrics)
    return metrics


def estimate_energy_impact_per_process(task, report):
    # Get the total CPU energy from the processor section
    total_cpu_time = report['all_tasks']['cputime_ns']

    # Calculate the CPU time ratio for this task
    cpu_time_ratio = task['cputime_ns'] / total_cpu_time

    # Estimate the energy impact for this task
    relative_energy_impact = cpu_time_ratio

    # Imagine this is in mj then
    energy_impact = relative_energy_impact * get_combined_power_from(report)

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


def mw_to_joules(power_mw, interval_seconds):
    power_w = power_mw / 1000  # Convert mW to W
    return power_w * interval_seconds


def get_interval_seconds_from(report):
    return report['elapsed_ns'] * 1e-9


def get_combined_power_from(report):
    return mw_to_joules(report['processor']['combined_power'], get_interval_seconds_from(report))


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

    # Take the first 10 elements from the filtered tasks
    top_10_tasks = filtered_tasks[:10]

    # Append the current task data to the end if it exists
    if current_task_data:
        top_10_tasks.append(current_task_data)

    # Update the report with the new task list
    report['tasks'] = top_10_tasks

    return report


def powermetrics_daemon(callback, report_interval=60):
    if not _has_powermetrics_sudo():
        return

    pc_id = generate_encoded_device_id()

    interval_seconds = report_interval * 1000

    process = subprocess.Popen(
        ['sudo', 'powermetrics', '-i', str(interval_seconds), '--order', 'cputime', '--format', 'plist'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    xml_output = ''
    sample_count = 0
    start_time = datetime.now()

    def format_time(dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    # Set up select for non-blocking reads
    readable = [process.stdout]

    while True:
        # Wait for data to be available, with a timeout
        ready, _, _ = select.select(readable, [], [], interval_seconds)

        if ready:
            line = process.stdout.readline()
            if not line:  # EOF
                break

            xml_output += line

            if xml_output.strip().endswith('</plist>'):
                sample_count += 1
                stop_time = datetime.now()
                print(f'Stats received for sample {sample_count}')

                try:
                    report = parse_xml(xml_output.lstrip('\x00').strip().encode('utf-8'))

                    report = filter_tasks_in(report)

                    task_metrics = gather_metrics_per_task(report)

                    callback({
                        'pc_id': pc_id,
                        'combined_power': get_combined_power_from(report),
                        'tasks': task_metrics,
                        'start_time': format_time(start_time),
                        'stop_time': format_time(stop_time),
                        'platform': platform.platform(),
                    })

                except Exception as e:
                    print(f"Unexpected error in sample {sample_count}: {e}")
                    break

                finally:
                    xml_output = ''
                    start_time = stop_time  # Set the start_time for the next sample

        # Check if the process has terminated
        if process.poll() is not None:
            break

    # Clean up
    process.terminate()
    process.wait()
