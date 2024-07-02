import subprocess
import xml.etree.ElementTree as ET


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


def estimate_energy_impact_per_process(data):
    # Get the total CPU energy from the processor section
    total_cpu_energy = data['processor']['cpu_energy']
    total_cpu_time = data['all_tasks']['cputime_ns']

    # Initialize a dictionary to store the energy impact per process
    energy_impact_per_process = {}

    # Iterate over the tasks
    for task in data['tasks']:
        # Calculate the CPU time ratio for this task
        cpu_time_ratio = task['cputime_ns'] / total_cpu_time

        # Estimate the energy impact for this task
        energy_impact = cpu_time_ratio * total_cpu_energy

        # Store the energy impact in the dictionary
        energy_impact_per_process[task['name']] = energy_impact

    return energy_impact_per_process


def powermetrics_deamon(callback, report_interval=60):
    process = subprocess.Popen(['powermetrics', '-i', str(report_interval * 1000), '--order', 'cputime', '--format', 'plist'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    xml_output = ''
    sample_count = 0
    while True:
        line = process.stdout.readline()
        if line:
            if xml_output.strip().endswith('</plist>'):  # assume this marks the end of a sample interval
                sample_count += 1
                print(f'Stats received for sample {sample_count}')

                try:
                    report = parse_xml(xml_output.lstrip('\x00').strip().encode('utf-8'))

                    report['tasks'] = report['tasks'][:10]
                    del report['network']
                    del report['disk']
                    del report['interrupts']
                    del report['processor']['clusters']
                    del report['gpu']

                    estimate = estimate_energy_impact_per_process(report)
                    callback(estimate)

                except Exception as e:
                    print(f"Unexpected error in sample {sample_count}: {e}")
                    break

                finally:
                    xml_output = ''

            xml_output += line
        else:
            break  # exit the loop if there's no more output
