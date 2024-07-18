import io
import os
import plistlib
import subprocess

from PIL import Image


def get_app_path(bundle_id):
    cmd = f"mdfind kMDItemCFBundleIdentifier == '{bundle_id}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    paths = result.stdout.strip().split('\n')
    return paths[0] if paths else None


def find_icon_file(app_path):
    info_plist_path = os.path.join(app_path, 'Contents', 'Info.plist')

    if not os.path.exists(info_plist_path):
        return None

    with open(info_plist_path, 'rb') as f:
        plist_data = plistlib.load(f)

    icon_file_name = None

    # First, check for CFBundleIconFile
    if 'CFBundleIconFile' in plist_data:
        icon_file_name = plist_data['CFBundleIconFile']
    else:
        # If not found, look for CFBundleTypeIconFile in document types
        for doc_type in plist_data.get('CFBundleDocumentTypes', []):
            if 'CFBundleTypeIconFile' in doc_type:
                icon_file_name = doc_type['CFBundleTypeIconFile']
                break

    if icon_file_name:
        # If the extension is not provided, add .icns
        if not icon_file_name.endswith('.icns'):
            icon_file_name += '.icns'

        icon_path = os.path.join(app_path, 'Contents', 'Resources', icon_file_name)
        if os.path.exists(icon_path):
            return icon_path

    return None


def extract_icon(icon_path, size=(64, 64)):
    # Convert .icns to png and return as bytes
    out_dir = '/Library/Application Support/PowerObserver'
    temp_output = os.path.join(out_dir, 'tmp_icon.png')
    os.makedirs(out_dir, exist_ok=True)

    cmd = f"sips -s format png '{icon_path}' --out '{temp_output}'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode == 0:
        with open(temp_output, 'rb') as f:
            icon_data = f.read()
        os.remove(temp_output)

        # Create a PIL Image object from the icon_data
        icon_image = Image.open(io.BytesIO(icon_data))

        # Resize the icon image to the specified size
        resized_icon = icon_image.resize(size, resample=Image.LANCZOS)

        # Convert the resized image to bytes
        resized_icon_data = io.BytesIO()
        resized_icon.save(resized_icon_data, format='PNG')
        resized_icon_data.seek(0)

        return resized_icon_data.getvalue()

    return None


def get_app_icon(bundle_id):
    app_path = get_app_path(bundle_id)
    if not app_path:
        print(f"Could not find app for {bundle_id}")
        return False

    icon_path = find_icon_file(app_path)
    if not icon_path:
        print(f"Could not find icon file for {bundle_id}")
        return False

    app_icon_data = extract_icon(icon_path)

    return app_icon_data
