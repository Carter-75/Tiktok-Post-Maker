import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv # Need to load dotenv here too
from colorama import init, Fore

init(autoreset=True)
load_dotenv() # Load environment variables

def upload_to_tiktok(description, hashtags, audio_path=None):
    print(Fore.CYAN + "\nStarting TikTok Uploader...")

    # 1. Setup Chrome Options
    chrome_options = Options()
    
    # 1.1 Support attaching to existing browser process
    debugger_port = os.getenv("TIKTOK_DEBUGGER_PORT")
    if debugger_port:
        print(Fore.YELLOW + f"Attaching to existing browser on port {debugger_port}...")
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debugger_port}")
    else:
        # Default behavior: launch new instance with local profile
        # Use a local profile to persist login cookies
        script_dir = os.path.dirname(os.path.abspath(__file__))
        profile_dir = os.path.join(script_dir, "chrome_profile")
        chrome_options.add_argument(f"user-data-dir={profile_dir}")
    
    # Suppress logging
    chrome_options.add_argument("--log-level=3")

    # Check for custom browser path (e.g., Comet)
    browser_path = os.getenv("TIKTOK_BROWSER_PATH")
    if browser_path and os.path.exists(browser_path):
        print(Fore.YELLOW + f"Using custom browser: {browser_path}")
        chrome_options.binary_location = browser_path
    
    print(Fore.YELLOW + "Launching Browser... (If this is your first time, you will need to log in)")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    except Exception as e:
        print(Fore.RED + "Failed to launch browser. Ensure you have the correct driver installed or use Google Chrome.")
        print(f"Error: {e}")
        return
    
    try:
        # 2. Go to Upload Page
        driver.get("https://www.tiktok.com/upload?lang=en")
        
        # 3. Check for Login
        print(Fore.WHITE + "Checking login status...")
        try:
            # Look for an element that indicates we are logged in, or wait for user to log in
            # This is a simple check; we rely on the user to log in interactively if needed.
            time.sleep(3)
            current_url = driver.current_url
            if "login" in current_url:
                print(Fore.RED + "You are not logged in!")
                print(Fore.YELLOW + "Please log in to TikTok in the browser window.")
                print(Fore.YELLOW + "Press Enter here once you are logged in and on the upload page...")
                input()
        except:
            pass

        # 4. Upload Images
        print(Fore.CYAN + "Preparing to upload images...")
        
        # Get absolute paths of images in output/ folder
        output_dir = os.path.join(script_dir, "output")
        if not os.path.exists(output_dir):
            print(Fore.RED + "No /output directory found!")
            return

        images = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        # Sort by slide number (assuming filename contains slide_N)
        images.sort(key=lambda x: int(x.split('slide_')[1].split('_')[0]) if 'slide_' in x else x)
        
        if not images:
            print(Fore.RED + "No images found in /output to upload.")
            return

        print(Fore.WHITE + f"Found {len(images)} images.")
        
        # Locate the file input (iframe handling might be needed depending on TikTok's current DOM)
        # TikTok's upload input is usually hidden.
        # We try to find the input[type='file']
        
        try:
            file_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
            )
            file_input.send_keys("\n".join(images))
            print(Fore.GREEN + "Images uploaded to browser.")
        except Exception as e:
            print(Fore.RED + f"Could not find file input element. TikTok UI might have changed.\nError: {e}")
            input("Press Enter to continue...")
            return

        # 5. Set Caption
        print(Fore.CYAN + "Setting caption...")
        time.sleep(5) # Wait for upload to process slightly
        
        full_caption = f"{description}\n\n{hashtags}"
        
        # Find the editor content editable div
        try:
            caption_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".public-DraftEditor-content"))
            )
            caption_box.click()
            caption_box.send_keys(full_caption) # This might be flaky with emojis/newlines, but basic text works
             # Alternatively, use clipboard or JS injection if send_keys is flaky
            print(Fore.GREEN + "Caption set.")
        except:
             print(Fore.RED + "Could not automatically set caption. Please paste it manually.")
             print(f"Caption: {full_caption}")

        # 6. Wait for User to Post
        print(Fore.MAGENTA + "\nSUCCESS! Images and caption are ready.")
        print(Fore.YELLOW + "Review the post in the browser.")
        print(Fore.YELLOW + "Click 'Post' in the browser when ready.")
        print(Fore.WHITE + "Press Enter here to close the browser and finish...")
        input()
        
    except Exception as e:
        print(Fore.RED + f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    # Test run
    upload_to_tiktok("Test Description", "#test")
