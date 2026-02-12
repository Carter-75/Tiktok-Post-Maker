import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import os

def debug_dom():
    print("Launching browser to inspect TikTok DOM...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    profile_dir = os.path.join(script_dir, "chrome_profile")
    
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--log-level=3")
    
    driver = uc.Chrome(options=options)
    
    try:
        driver.get("https://www.tiktok.com/upload?lang=en")
        print("Please log in if needed. Waiting 10 seconds for page load...")
        time.sleep(10)
        
        # Dump all inputs
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"Found {len(inputs)} inputs.")
        
        with open("dom_dump.txt", "w", encoding="utf-8") as f:
            f.write("=== INPUTS ===\n")
            for i, inp in enumerate(inputs):
                try:
                    outer_html = inp.get_attribute("outerHTML")
                    f.write(f"Input {i}: {outer_html}\n")
                except:
                    f.write(f"Input {i}: Could not get HTML\n")
            
            f.write("\n=== IFRAMES ===\n")
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for i, frame in enumerate(iframes):
                try:
                    outer_html = frame.get_attribute("outerHTML")
                    f.write(f"Iframe {i}: {outer_html}\n")
                except:
                    pass

            f.write("\n=== BUTTONS ===\n")
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for i, btn in enumerate(buttons):
                try:
                     outer_html = btn.get_attribute("outerHTML")
                     f.write(f"Button {i}: {outer_html}\n")
                except:
                    pass

        print("DOM dumped to dom_dump.txt")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_dom()
