"""Functions to grab images of Premier League players"""

def get_players(threshold):
    """Fetches players that meet certain minutes threshold in the premier league"""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import NoSuchElementException
    import time

    # Configure for performance
    options = Options()
    options.add_argument("--headless=new")
    browser = webdriver.Chrome(options=options)

    browser.get("https://understat.com/league/EPL")

    # Filter out players that don't meet minute threhsold 
    WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#league-players > div.table-control-panel > button > i"))
    ).click()

    minutes = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.row-title:has(> span[title='Minutes played']) ~ div.row-filter > input[data-name='min']"))
       )
    minutes.send_keys(threshold)

    WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#league-players > div.table-popup > div.table-popup-footer > a.button-apply"))
    ).click()

    time.sleep(2)

    # Grab all players
    player_list = []
    pg_no = 1
    while True:
        players = browser.find_elements(By.CSS_SELECTOR, "#league-players > table > tbody:nth-child(2) > tr")
        for player in players:
            try:  # Catch empty player row
                name = player.find_element(By.CSS_SELECTOR, "td:nth-child(2) > a").text
            except NoSuchElementException:
                break
            team = player.find_element(By.CSS_SELECTOR, "td:nth-child(3) > a").text
            player_list.append((name, team))
        pg_no += 1
        try:
            browser.find_element(By.CSS_SELECTOR, f"ul.pagination > li[data-page='{pg_no}'] > a").click()
        except NoSuchElementException:
            break
    
    return player_list


def random_selection(players):
    """Randomly selects 85 players"""
    import random

    # Sample 100 players from input list
    return random.sample(players, 85)


def get_images(players):
    """Fetches images of given players in their club kits"""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException
    import sys
    import requests

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

        # Find first image
        try:  # In case no images found
            first = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "eA0Zlc"))
            )
        except TimeoutException:
            continue
        
        try:
            # Find higher quality version
            first.click()
            hq = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "p7sI2"))
            )
            # Download image
            image = WebDriverWait(hq, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "img"))
            )
        except TimeoutException:
            # Download image
            image = WebDriverWait(first, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "img"))
            )

        src = image.get_attribute("src")

        try:  # Request image and save to images folder
            response = requests.get(src, timeout=10)
            response.raise_for_status  # If failed request

            if "Access Denied" in response.text:
                continue  # If content invalid 

            if "ipykernel" in sys.modules:  # If in Jupyter
                with open(f"images/{player}.png", "wb") as file:
                    file.write(response.content)
            else:  # If in python script file
                with open(f"media/images/{player}.png", "wb") as file:
                    file.write(response.content)
        except requests.exceptions.RequestException:
            continue
        
        # Save source
        source = first.get_attribute("data-lpage")
        sources.append((player, source))
    
    return sources


def tone_detector(images):
    """Uses LLM to determine media tone of image"""
    import google.generativeai as genai
    import api_key
    from PIL import Image
    import time

    # Configure for image analysis
    genai.configure(api_key=api_key.api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    tone = []
    batch_size = 5  # Process in batches to avoid resource exhaustion
    for i in range(0, len(images), batch_size):
        batch = images[i:i+batch_size]

        # Upload samples
        sample_positive = "samples/iwobi-positive.png"
        sample_negative = "samples/iwobi-negative.png"
        sample_neutral = "samples/iwobi-neutral.png"

        for image_path in batch:
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
            Scores closer to 100 means the image is large and of high quality.
            Images of the player on the pitch are of higher quality. Images with a plain background are lower.
            If the image has watermarks such as "Getty Images", the score is automatically 0.
            Of the samples, note how the first two are of higher quality than the last.

            Do not include new lines in any part of the response. It should be formatted as follows:
            string, integer, integer
            with the string being "Positive", "Neutral", or "Negative"
            and the integer being from 0 to 100.
            """

            response = model.generate_content([prompt, sample_positive, sample_negative, sample_neutral, image])

            tone.append(response.text.replace("\n", ""))

            time.sleep(2)  # Pause in beetween images

        time.sleep(5)  # Pause in between batches
    
    return tone


def compiler(sources, tones):
    """Compiles data into a pandas DataFrame"""
    import pandas as pd
    import glob
    import re

    # Set up DataFrame with sources
    players, sources = zip(*sources)
    source_df = pd.DataFrame(
        {"Players": players,
         "Source": sources}
    )

    # Set up DataFrame with tone data
    images = glob.glob("images/*")
    names = [re.findall(r"images/(.+)\.png", image)[0] for image in images]
    processed_tones = []
    for response in tones:
        processed_tones.append(
            (response.split(",")[0].strip('"'), 
             response.split(",")[1].strip(), 
             response.split(",")[2].strip())
             )
    tone, strength, quality = zip(*processed_tones)
    tone_df = pd.DataFrame(
        {"Players": names,
         "Tone": tone,
         "Tone Strength": strength,
         "Image Quality": quality}
    )

    # Merge dataframe
    merged = pd.merge(tone_df, source_df, on="Players")
    merged.sort_values(by="Players", inplace=True)
    merged.reset_index(drop=True, inplace=True)
    return merged