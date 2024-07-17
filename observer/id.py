import hashlib
import uuid
import platform
import os
import psutil


def get_mac_address():
    return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2 * 6, 2)][::-1])


def get_system_specific_seed():
    # Collect various pieces of system-specific information
    system = platform.system()
    if system == "Windows":
        # Windows-specific information
        cpu_id = platform.processor()
        try:
            disk_serial = os.popen("wmic diskdrive get SerialNumber").read().split("\n")[1].strip()
        except:
            disk_serial = "unknown"
    elif system == "Linux":
        # Linux-specific information
        cpu_id = os.popen("cat /proc/cpuinfo | grep 'cpu MHz'").read()
        try:
            disk_serial = os.popen("lsblk --nodeps -no serial").read().strip()
        except:
            disk_serial = "unknown"
    elif system == "Darwin":  # macOS
        # macOS-specific information
        cpu_id = os.popen("sysctl -n machdep.cpu.brand_string").read().strip()
        try:
            disk_serial = os.popen("system_profiler SPHardwareDataType | grep 'Hardware UUID'").read().split(":")[
                1].strip()
        except:
            disk_serial = "unknown"
    else:
        cpu_id = "unknown"
        disk_serial = "unknown"

    # Add more system-specific information
    total_ram = str(psutil.virtual_memory().total)
    hostname = platform.node()

    mac_address = get_mac_address()

    # Combine all information into a single string
    return f"{mac_address}:{system}:{cpu_id}:{disk_serial}:{total_ram}:{hostname}".encode('utf-8')


def generate_encoded_device_id(iterations=1000):
    # Combine MAC address and salt
    seed = get_system_specific_seed()

    # Perform key stretching
    hash_object = hashlib.sha256(seed)
    for i in range(iterations):
        hash_object = hashlib.sha256(hash_object.digest())

    # Return the final hash
    return hash_object.hexdigest()
