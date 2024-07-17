import json
import re
import subprocess


def get_battery_info():
    ioreg_output = subprocess.check_output(["ioreg", "-rc", "AppleSmartBattery"]).decode("utf-8")

    battery_info = {}

    # Extract AppleRawCurrentCapacity
    current_capacity_match = re.search(r'"AppleRawCurrentCapacity"\s*=\s*(\d+)', ioreg_output)
    if current_capacity_match:
        battery_info['AppleRawCurrentCapacity'] = int(current_capacity_match.group(1))
    else:
        raise Exception('')

    voltage_match = re.search(r'"Voltage"\s*=\s*(\d+)', ioreg_output)
    if current_capacity_match:
        battery_info['Voltage'] = int(voltage_match.group(1))
    else:
        raise Exception('')

    # Extract IsCharging
    is_charging_match = re.search(r'"IsCharging"\s*=\s*(\w+)', ioreg_output)
    if is_charging_match:
        battery_info['IsCharging'] = is_charging_match.group(1).lower() == 'yes'
    else:
        raise Exception('')

    # Extract "PowerTelemetryData" object as a string
    power_telemetry_match = re.search(r'"PowerTelemetryData"\s*=\s*({.*?})', ioreg_output, re.DOTALL)
    if power_telemetry_match:
        telemetry_data = power_telemetry_match.group(1).replace('=', ':')
        battery_info['PowerTelemetryData'] = json.loads(telemetry_data)
    else:
        raise Exception('')

    return battery_info


if __name__ == "__main__":
    try:
        info = get_battery_info()
        print(info)
    except Exception as e:
        print(f"An error occurred: {e}")
