import os
import json
from frappe_api import create_doctypes_and_data
from capture_screenshots import capture_all_screenshots
from generate_docx import create_sanskar_frs_docx

def run_pipeline(spec_json_file):
    with open(spec_json_file, "r") as f:
        spec_data = json.load(f)
        
    print("[1/4] Creating DocTypes and seed data in ERPNext...")
    create_doctypes_and_data(spec_data)
    
    print("[2/4] Capturing List, Form, and Report screenshots via Playwright...")
    screenshots_dir = "screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    capture_all_screenshots(spec_data, output_dir=screenshots_dir)
    
    print("[3/4] Compiling final Sanskar Technolab FRS Document (.docx)...")
    output_docx = f"{spec_data.get('module_name', 'Module')}-FRS-V1.0.docx"
    create_sanskar_frs_docx(spec_data, screenshots_dir, output_docx)
    
    print(f"[4/4] Pipeline completed successfully! Generated: {output_docx}")

if __name__ == "__main__":
    if os.path.exists("spec.json"):
        run_pipeline("spec.json")
    else:
        print("Please provide a spec.json configuration file to run the pipeline.")
