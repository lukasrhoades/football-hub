def get_batch_images(players):
    """Fetches tons of images of given players in their club kits"""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException
    import sys
    import requests
    import os
    import time

    # Configure for performance
    options = Options()
    options.add_argument("--headless=new")
    browser = webdriver.Chrome(options=options)

    # For each player search an image
    sources = []  # Save sources in list
    for player, club in players:
        browser.get("https://www.google.com/imghp?hl=en")
        
        # Wait for search bar to load
        search_player = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "APjFqb"))
        ) 
        # Search player images (without Wikipedia entries)
        search_player.send_keys(player + " " + club + " -wiki match")
        search_player.send_keys(Keys.ENTER)
        
        try:  # Filter only large images
            # Locate large images (higher quality)
            WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.ID, "hdtb-tls"))
            ).click()  # Click tools
            WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "KTBKoe"))
            ).click()  # Click size
            large = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.YpcDnf a"))
            )
            url = large.get_attribute("href")
            browser.get(url)
        except TimeoutException:
            pass

        try:  # In case no images found
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "eA0Zlc"))
            )
        except TimeoutException:
             continue
        
        # Locate all images on page
        pics = WebDriverWait(browser, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "eA0Zlc"))
        )

        # Process each image, keep if meets certain standards
        for i, pic in enumerate(pics): 
            try:
                # Find higher quality version
                pic.click()
                image = WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".p7sI2 img"))
                )
            except TimeoutException:
                # Download image
                image = WebDriverWait(pic, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "img"))
                )

            src = image.get_attribute("src")

            try:  # Request image and save to images folder
                response = requests.get(src, timeout=10)
                response.raise_for_status  # If failed request

                if "Access Denied" in response.text:
                    continue  # If content invalid 

                if "ipykernel" in sys.modules:  # If in Jupyter
                    fp = f"batch_images/{player}-{i}.png"
                    with open(fp, "wb") as file:
                        file.write(response.content)
                    
                    # Throw out image if too small (saves Gemini tokens too)
                    if (os.path.getsize(fp) / 1024) < 50:  # If < 50kb
                        os.remove(fp)
                        time.sleep(5)
                        continue

                    # Determine the strength of tone and image quality
                    response = mini_tone_detector(fp)
                    tone = response.split(",")[0].strip()
                    strength = int(response.split(",")[1].strip())
                    quality = int(response.split(",")[2].strip())

                    # Get rid of image if doesn't meet certain LLM standard
                    if tone != "Neutral" and strength < 90:
                        os.remove(fp)
                        time.sleep(5)
                        continue

                    if quality < 90:
                        os.remove(fp)
                        time.sleep(5)
                        continue

                    # Rename image to reflect tone
                    os.rename(fp,
                              f"batch_images/{player}-{tone}-{i}.png")
                    
                else:  # If in python script file
                    with open(f"media/batch_images/{player}-{i}.png", "wb") as file:
                        file.write(response.content)

            except requests.exceptions.RequestException:
                continue
            
            # Save source
            source = pic.get_attribute("data-lpage")
            sources.append((player, source))

            time.sleep(5)
    
    return sources


def mini_tone_detector(image_path):
    """Uses LLM to determine media tone of image"""
    import google.generativeai as genai
    import api_key
    from PIL import Image

    # Configure for image analysis
    genai.configure(api_key=api_key.api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Upload samples
    sample_positive = "samples/iwobi-positive.png"
    sample_negative = "samples/iwobi-negative.png"
    sample_neutral = "samples/iwobi-neutral.png"

    image = Image.open(image_path)

    prompt = """
    Respond with exactly 3 values separated by a comma:
    tone, tone strength(0-100), image quality(0-100)).

    The first three images are sample images. For the purposes of classification:
    The first reflects a positive image,
    The second reflects a negative image,
    The third reflects a neutral image.

    The final image is the image you are tasked with classifying on three criteria:
    Tone, tone strength, image quality.

    Tone:
    Does the player in the final image reflect a positive, neutral, or negative media tone?
    If the player is smiling or celebrating, the image is positive.
    The image is negative if the player looks disappointed or frustrated.
    Otherwise, the image is neutral (player has neutral expression).

    Tone Strength:
    Rank the previous classification on a scale of 0 to 100.
    Scores closer to 0 means you are unsure and classified randomly.
    Scores closer to 100 means the image closely resembles the given criteria for the tone.

    Image Quality:
    Scores closer to 0 means the image is grain, tiny, or very difficult to decipher.
    Scores closer to 100 means the image is very large (many pixels) and of high quality.
    Images of the player on the pitch are of higher quality. Images with a plain background are lower.
    If the image has watermarks such as "Getty Images", the score is automatically 0.
    Of the samples, note how the first two are of higher quality than the last.

    Do not include new lines in any part of the response. It should be formatted as follows:
    string, integer, integer
    with the string being "Positive", "Neutral", or "Negative"
    and the integer being from 0 to 100.
    """

    response = model.generate_content([prompt, sample_positive, sample_negative, sample_neutral, image])

    return response.text.replace("\n", "")

