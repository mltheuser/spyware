import os
import platform
import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import heapq
from reset import reset_measurements
from id import generate_encoded_device_id
from collections import defaultdict
import psutil

def collect_srumutil_data():
    report_path = os.path.join(os.environ['TEMP'], 'energy_report.xml')
    subprocess.check_call(['powercfg', '/srumutil', '/output', report_path, '/xml'])
    with open(report_path, 'r') as f:
        xml_content = f.read()
    return xml_content
 
    
def parse_xml_to_dict(xml_string):
    root = ET.fromstring(xml_string)    
    records = []
    for record in root.findall('Record'):        
        record_dict = record.attrib.copy()
        for child in record:
            if len(child.attrib) == 0:                
                record_dict[child.tag] = child.text.strip() if child.text else None
            elif len(child.attrib) == 1 and 'Value' in child.attrib:                
                record_dict[child.tag] = child.attrib['Value']
            else:                
                record_dict[child.tag] = child.attrib
        records.append(record_dict)
    return records
 
def merge_energy(records):
    merged_records = defaultdict(int)
    for res in records:
        app = res['AppId']
        energy = res['TotalEnergyConsumption']
        merged_records[app] += int(energy) 

    return [{'command': app, 'power': mwh_to_joules(power)} for app, power in merged_records.items()]

def get_top_tasks(merged_records):
    min_heap = []
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)
    process_name = current_process.name()
    current_record = None

    for merged_record in merged_records:   
        if process_name in merged_record['command']:
            current_record = merged_record 
        if len(min_heap) < 10:
            heapq.heappush(min_heap, (merged_record['power'], merged_record))
        elif min_heap[0][0] < merged_record['power']:
            heapq.heappop(min_heap)[1]['command']
            heapq.heappush(min_heap, (merged_record['power'], merged_record))

    top_tasks = [task[1] for task in sorted(min_heap, reverse=True)]

    is_in_top = False
    for top_task in top_tasks:
        if process_name in top_task['command']:
            is_in_top = True

    if not is_in_top:
        top_tasks.append(current_record) 

    return top_tasks

def mwh_to_joules(power_mwh):
    return power_mwh * 3.6  # 1 mWh = 3.6 J
 

def powercfg_daemon(callback, report_interval=60):
    if platform.system() != 'Windows':
        print("This script is designed to run on Windows systems only.")
        return
 
    pc_id = generate_encoded_device_id()
 
    def format_time(dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
 

    while True:
        start_time = datetime.now()
        # reset_measurements()
 
        # Wait for the specified interval
        time.sleep(report_interval)
 
        stop_time = datetime.now()
        srumutil_output = collect_srumutil_data()
        records = parse_xml_to_dict(srumutil_output) # a list of records (directionaries)
        merged_records = merge_energy(records)
        task_metrics = get_top_tasks(merged_records)
        combined_power = sum(merged_record['power'] for merged_record in merged_records)

        callback({
            'pc_id': pc_id,
            'combined_power': combined_power,
            'tasks': task_metrics,
            'start_time': format_time(start_time),
            'stop_time': format_time(stop_time),
            'platform': platform.platform(),
        })
 