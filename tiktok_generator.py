import os
import json
import base64
import requests
import shutil # For cleanup
from openai import OpenAI
from dotenv import load_dotenv
from colorama import init, Fore, Style
from datetime import datetime
import msvcrt
import sys
import re # For sanitization
import tiktok_uploader # Import the uploader module
from PIL import Image, ImageDraw, ImageFont # For text rendering
import textwrap # For wrapping text

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print(Fore.RED + "Error: OPENAI_API_KEY not found in .env file.")
    print(Fore.YELLOW + "Please structure your .env file like this:")
    print("OPENAI_API_KEY=sk-...")
    input("Press Enter to exit...")
    exit()

client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = """You are my dedicated generator for promotional vertical carousel content for a paid digital product called 30 Day AI Mastery.
This content is used to create TikTok / Reels style carousel posts.
━━━━━━━━━━━━━━━━━━━━
WHEN I SAY: GENERATE
━━━━━━━━━━━━━━━━━━━━
You must output ONLY a JSON object inside a code block.
No explanations. No extra text.
Structure:
{
"images": [
{
"slide_number": 1,
"prompt": "",
"on_screen_caption": ""
}
],
"post_description": "",
"hashtags": []
}
Rules:
• Exactly 5 slides
• Vertical 9:16
• Each slide must follow a different psychological angle:

Relatable struggle / credibility
Realization / mechanism
Structured progression
Lifestyle improvement / workflow shift
Product reveal + CTA

• Prompts must:

Be detailed and ready for an image generator (DALL-E 3)
Be realistic and grounded
No luxury bait (no mansions, supercars, piles of cash)
Feel like a real workflow
Explicitly mention empty space in the LOWER HALF of the frame for captions.
The prompt must describe ONLY the visual scene (objects, lighting, setting).
Do NOT include the text of the slogan, hook, or caption in the image prompt.
Do NOT describe words. Describe the physical objects. 
Example bad prompt: "A screen saying 30 Day AI Mastery"
Example good prompt: "A close up of a laptop screen displaying code with a coffee cup nearby"

• Captions:

1–2 short lines
Conversational tone (like someone explaining what helped them)
1–2 short lines
Conversational tone (like someone explaining what helped them)
The `on_screen_caption` is the ONLY text field for the slide. 
It must contain the FULL message: The Hook/Headline + The Explainer/Body text.
Do not split them. Put everything you want to appear on the image in this one field.
It should be punchy, engaging, and drive curiosity.
Different wording every generation
Slide 5 MUST end with:
Link in bio
Slide 5 MUST end with:
Link in bio
(Example for Slide 5: "Start building your empire today. Link in bio")
Do NOT make the Slide 5 caption ONLY "Link in bio". It must have a sentence before it.
The "on_screen_caption" field should contain the ENTIRE text (The hook + "Link in bio").

• Post description:

Exactly 2 short paragraphs
Explain learning → building → automating
Grounded tone
Include this link:
https://gum.new/gum/cmlcwqp86001m04jl2xu9b8oq

• Hashtags:

8–14 hashtags
Mix of AI, productivity, building, creator economy, learning
No spam tags
Different every generation

Never reuse previous hooks, captions, prompts, or hashtag patterns.
━━━━━━━━━━━━━━━━━━━━
AFTER GENERATE
━━━━━━━━━━━━━━━━━━━━
If I say:
#1
#2
#3
#4
#5
You must generate the image for that specific slide using the stored prompt and caption.
Do NOT regenerate the JSON unless I say GENERATE again.
If I say:
Desc
Return ONLY the formatted TikTok caption with:
• The two-paragraph description
• The link
• The hashtags
No extra commentary.
"""

# Global state to store the last generated content
last_generated_content = None

def generate_carousel():
    global last_generated_content
    print(Fore.CYAN + "\nGenerating carousel concept...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": "GENERATE"}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        try:
            data = json.loads(content)
            last_generated_content = data
            
            # Clean workspace logic - Optional: Ask user or just do it? 
            # User requested "clear up old jobs if not cleared".
            # We'll stick to a manual clear or clear-on-generate if we want to be aggressive.
            # Let's clean output folder silently on a NEW generation to keep things fresh.
            clean_workspace()
            
            print(Fore.GREEN + "\nSuccessfully generated carousel concept!")
            print(Fore.YELLOW + "Slides:")
            for slide in data.get("images", []):
                print(f"  #{slide['slide_number']}: {slide['on_screen_caption']} (Prompt: {slide['prompt'][:50]}...)")
            
            print(Fore.YELLOW + "\nDescription Preview:")
            print(f"  {data.get('post_description', '')[:100]}...")
            
        except json.JSONDecodeError:
            print(Fore.RED + "Failed to parse JSON response from OpenAI.")
            print(content)
            
    except Exception as e:
        print(Fore.RED + f"Error during generation: {e}")

def generate_image(slide_number):
    global last_generated_content
    if not last_generated_content:
        print(Fore.RED + "No content generated yet. Type 'GENERATE' first.")
        return

    slides = last_generated_content.get("images", [])
    target_slide = next((s for s in slides if s["slide_number"] == slide_number), None)
    
    if not target_slide:
        print(Fore.RED + f"Slide #{slide_number} not found.")
        return

    prompt = target_slide["prompt"]
    caption = target_slide.get("on_screen_caption", "")
    
    # ---------------------------------------------------------
    # PROMPT SANITIZATION
    # ---------------------------------------------------------
    # Remove the caption text from the prompt if it exists there
    # This ensures DALL-E doesn't see the text instructions
    clean_visual_prompt = prompt
    if caption:
        # Case-insensitive remove
        pattern = re.compile(re.escape(caption), re.IGNORECASE)
        clean_visual_prompt = pattern.sub("", clean_visual_prompt)
        
        # Also remove common "text saying" phrases just in case
        clean_visual_prompt = clean_visual_prompt.replace("text saying", "")
        clean_visual_prompt = clean_visual_prompt.replace("caption:", "")
        clean_visual_prompt = clean_visual_prompt.replace("words:", "")
        
    print(Fore.BLUE + f"DEBUG: Cleaned Prompt: {clean_visual_prompt}")
    
    # Request CLEAN image from DALL-E
    full_prompt = f"I NEED A TEXTLESS IMAGE. {clean_visual_prompt}. Do not render any text, numbers, or letters. Purely visual composition."

    print(Fore.CYAN + f"\nGenerating image for Slide #{slide_number}...")
    print(Fore.WHITE + f"Prompt: {full_prompt}")

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1024x1792",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url
        
        # Ensure output directory exists
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Download and save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/slide_{slide_number}_{timestamp}.png"
        
        img_data = requests.get(image_url).content
        with open(filename, 'wb') as handler:
            handler.write(img_data)
            
        print(Fore.GREEN + f"Raw image saved to: {filename}")
        
        # Apply Text Overlay
        if caption:
            print(Fore.CYAN + f"Overlaying caption: \"{caption}\"")
            overlay_text_on_image(filename, caption)
            print(Fore.GREEN + f"Caption applied.")
            
    except Exception as e:
        print(Fore.RED + f"Error generating image: {e}")

def overlay_text_on_image(image_path, text):
    """Draws the caption on the lower half of the image using PIL."""
    try:
        if not text:
            return

        print(Fore.BLUE + f"DEBUG: Overlaying exact text: '{text}'")

        with Image.open(image_path) as img:
            draw = ImageDraw.Draw(img)
            width, height = img.size
            
            # Font settings
            # Try to load Arial, fallback to default
            try:
                # Calculate size based on image width (approx 5% of width)
                font_size = int(width * 0.05) 
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
                font_size = 20
            
            # Wrap text
            # Estimate chars per line? 
            # 1024 width / (font_size * 0.6 approx width per char)
            chars_per_line = int(width / (font_size * 0.6))
            lines = textwrap.wrap(text, width=chars_per_line)
            
            # Calculate text block height and width for background
            line_heights = [draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in lines]
            total_text_height = sum(line_heights) + (len(lines) * 10) # 10px padding between lines
            
            # Position: Lower Third (approx 75% down)
            start_y = int(height * 0.75) - (total_text_height // 2)
            
            # Calculate max width for background
            max_line_width = 0
            for line in lines:
                w = draw.textlength(line, font=font)
                if w > max_line_width:
                    max_line_width = w
            
            # Draw Background Rectangle
            padding = 2
            bg_x1 = (width - max_line_width) // 2 - padding
            bg_y1 = start_y - padding
            bg_x2 = (width + max_line_width) // 2 + padding
            bg_y2 = start_y + total_text_height + padding
            
            draw.rectangle((bg_x1, bg_y1, bg_x2, bg_y2), fill="white")

            current_y = start_y
            for line in lines:
                # Center text horizontally
                text_width = draw.textlength(line, font=font)
                x = (width - text_width) // 2
                
                # Draw Text (Black, no outline)
                draw.text((x, current_y), line, font=font, fill="black")
                
                # Move to next line
                bbox = draw.textbbox((0, 0), line, font=font)
                line_height = bbox[3] - bbox[1]
                current_y += line_height + 10
                
            img.save(image_path)
            
    except Exception as e:
        print(Fore.RED + f"Failed to overlay text: {e}")

def get_uppercase_input(prompt):
    """Custom input function that force-echoes uppercase characters."""
    print(prompt, end='', flush=True)
    line = []
    while True:
        ch = msvcrt.getch()
        if ch in (b'\r', b'\n'): # Enter
            print() # Newline
            return ''.join(line)
        elif ch == b'\x08': # Backspace
            if line:
                line.pop()
                sys.stdout.write('\b \b')
                sys.stdout.flush()
        elif ch == b'\x03': # Ctrl+C
            raise KeyboardInterrupt
        elif ch in (b'\x00', b'\xe0'): # Special keys (arrows, F-keys)
            msvcrt.getch() # Ignore the second byte
            continue
        else:
            try:
                decoded = ch.decode('utf-8')
                if decoded.isprintable():
                    upper = decoded.upper()
                    line.append(upper)
                    # Force Yellow/Orange for the typed character
                    sys.stdout.write(Fore.YELLOW + upper + Style.RESET_ALL)
                    sys.stdout.flush()
            except:
                pass

def clean_workspace():
    """Deletes all files in the output directory."""
    output_dir = "output"
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(Fore.RED + f"Failed to delete {file_path}. Reason: {e}")
    print(Fore.YELLOW + "Workspace cleaned (previous output files removed).")

def generate_all_images():
    """Generates slides 1 through 5 sequentially."""
    if not last_generated_content:
        print(Fore.RED + "No content generated yet. Type 'GENERATE' first.")
        return
    
    print(Fore.MAGENTA + "\nGenerating ALL slides (1-5)...")
    for i in range(1, 6):
        generate_image(i)
        
def upload_post():
    """Triggers the Selenium uploader."""
    global last_generated_content
    if not last_generated_content:
        print(Fore.RED + "No content generated yet.")
        return
        
    print(Fore.CYAN + "\n=== AUTO-POSTING TO TIKTOK ===")
    
    desc = last_generated_content.get("post_description", "")
    hashtags = " ".join(last_generated_content.get("hashtags", []))
    
    # Check if images exist
    output_dir = "output"
    if not os.path.exists(output_dir) or not os.listdir(output_dir):
        print(Fore.RED + "No images found in output/ folder! Generate images first.")
        return

    tiktok_uploader.upload_to_tiktok(desc, hashtags)
    
    # Optional: Clear after successful post? User said "clear up the job when the job is done"
    # But usually it's safer to keep files until next run. 
    # Let's ask or just leave it for the next GENERATE to clean.
    print(Fore.YELLOW + "Job complete. Files will be cleared on next GENERATE.")

def main():
    print(Fore.MAGENTA + "Welcome to the TikTok Carousel Generator!")
    print(Fore.WHITE + "Commands:")
    print("  GENERATE - Create new carousel concept (Clears previous files!)")
    print("  #1-#5    - Generate specific slide")
    print("  ALL      - Generate images for ALL slides (1-5)")
    print("  POST     - Launch Browser to Auto-Post")
    print("  Desc     - Show post description")
    print("  exit     - Quit")

    while True:
        # Custom input that forces caps visual
        user_input = get_uppercase_input(Fore.YELLOW + "\n> ")
        command = user_input.strip() # Already uppercase from the function
        
        if command == "EXIT":
            break
        elif command == "GENERATE":
            generate_carousel()
        elif command == "ALL":
            generate_all_images()
        elif command == "POST":
            upload_post()
        elif command.startswith("#") and command[1:].isdigit():
            slide_num = int(command[1:])
            if 1 <= slide_num <= 5:
                generate_image(slide_num)
            else:
                print(Fore.RED + "Invalid slide number. Use #1 through #5.")
        elif command == "DESC":
            show_description()
        else:
            print(Fore.RED + "Unknown command.")

if __name__ == "__main__":
    main()
