
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8501", timeout=120000)
        page.wait_for_load_state("networkidle", timeout=120000)

        # Wait for the iframe to be present
        iframe = page.wait_for_selector("iframe[title=\'streamlitApp\']", timeout=120000)
        frame = iframe.content_frame()

        # Wait for a specific element inside the iframe that indicates the app has loaded
        frame.wait_for_selector("h1:has-text('Vento em Osório, RS')", timeout=120000)

        page.screenshot(path="jules-scratch/verification/verification.png")
        browser.close()

run()
