import time
import os
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8000"
USERNAME = "Administrator"
PASSWORD = "admin_password"

def capture_all_screenshots(spec_data, output_dir="screenshots"):
    os.makedirs(output_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        
        # Login
        page.goto(f"{BASE_URL}/#login")
        page.fill("#login_email", USERNAME)
        page.fill("#login_password", PASSWORD)
        page.click("button.btn-login")
        page.wait_for_timeout(3000)
        
        # Capture DocType Screenshots
        for dt in spec_data.get("doctypes", []):
            dt_slug = dt.get("name").lower().replace(" ", "-")
            file_prefix = dt.get("name").lower().replace(" ", "_")
            
            # List View
            page.goto(f"{BASE_URL}/app/{dt_slug}")
            page.wait_for_timeout(2500)
            page.screenshot(path=os.path.join(output_dir, f"{file_prefix}_list_view.png"))
            
            # Form View (New)
            page.goto(f"{BASE_URL}/app/{dt_slug}/new-{dt_slug}")
            page.wait_for_timeout(2500)
            page.screenshot(path=os.path.join(output_dir, f"{file_prefix}_form_view.png"))
            
        # Capture Report Screenshots
        for rep in spec_data.get("reports", []):
            rep_slug = rep.get("name").lower().replace(" ", "-")
            file_prefix = rep.get("name").lower().replace(" ", "_")
            
            page.goto(f"{BASE_URL}/app/query-report/{rep_slug}")
            page.wait_for_timeout(3000)
            page.screenshot(path=os.path.join(output_dir, f"{file_prefix}_report.png"))
            
        browser.close()
    print("Screenshots captured successfully.")
