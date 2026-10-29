import requests

BASE_URL = "http://localhost:8000"
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"

HEADERS = {
    "Authorization": f"token {API_KEY}:{API_SECRET}",
    "Content-Type": "application/json"
}

def create_doctype(doctype_def):
    url = f"{BASE_URL}/api/resource/DocType"
    response = requests.post(url, headers=HEADERS, json=doctype_def)
    if response.status_code == 200:
        print(f"DocType '{doctype_def.get('name')}' created successfully.")
    else:
        print(f"Error creating DocType '{doctype_def.get('name')}': {response.text}")

def create_record(doctype_name, record_data):
    url = f"{BASE_URL}/api/resource/{doctype_name}"
    response = requests.post(url, headers=HEADERS, json=record_data)
    if response.status_code == 200:
        print(f"Record created in '{doctype_name}': {response.json().get('data', {}).get('name')}")
    else:
        print(f"Error creating record in '{doctype_name}': {response.text}")

def create_doctypes_and_data(spec_data):
    for dt in spec_data.get("doctypes", []):
        dt_def = {
            "doctype": "DocType",
            "name": dt.get("name"),
            "module": spec_data.get("module_name", "Custom"),
            "custom": 1,
            "is_submittable": dt.get("is_submittable", 0),
            "fields": dt.get("fields", [])
        }
        create_doctype(dt_def)
        
        for dummy in dt.get("dummy_records", []):
            create_record(dt.get("name"), dummy)
