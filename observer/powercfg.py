import subprocess
import xml.etree.ElementTree as ET
import time
import os


def parse_xml(xml_string):
    try:
        root = ET.fromstring(xml_string)
        result = parseXmlObjToDict(root)
        return result
    except ET.ParseError as e:
        print(f"Error parsing xml: {e}")
        raise e


def parseXmlObjToDict(xmlObj):
    result = {}
    for child in xmlObj:
        if child.tag == 'System':
            result['System'] = parseXmlObjToDict(child)
        elif child.tag == 'ProcessorUtilization':
            result['ProcessorUtilization'] = parseXmlObjToDict(child)
        elif child.tag == 'Process':
            if 'Processes' not in result:
                result['Processes'] = []
            result['Processes'].append(parseXmlObjToDict(child))
        else:
            result[child.tag] = child.text
    return result


def estimate_energy_impact_per_process(data):
    total_cpu_time = sum(float(process['CPUTime']) for process in data['Processes'])

    energy_impact_per_process = {}

    for process in data['Processes']:
        cpu_time_ratio = float(process['CPUTime']) / total_cpu_time
        energy_impact = cpu_time_ratio * 100  # Using percentage as a proxy for energy impact
        energy_impact_per_process[process['Name']] = energy_impact

    return energy_impact_per_process


def powercfg_daemon(callback, report_interval=60):
    while True:
        # Generate a new report
        report_path = os.path.join(os.environ['TEMP'], 'energy_report.xml')
        subprocess.run(['powercfg', '/srumutil', '/output', report_path, '/xml', '/duration', str(report_interval)],
                       check=True)

        # Read and parse the report
        with open(report_path, 'r') as f:
            xml_content = f.read()

        try:
            report = parse_xml(xml_content)
            estimate = estimate_energy_impact_per_process(report)
            callback(estimate)
        except Exception as e:
            print(f"Unexpected error: {e}")

        # Clean up
        os.remove(report_path)

        # Wait before generating the next report
        time.sleep(report_interval)
