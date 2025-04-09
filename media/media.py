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
    import urllib

    # Configure for performance
    options = Options()
    options.add_argument("--headless=new")
    browser = webdriver.Chrome(options=options)

    # For each player search an image
    for player, club in players:
        browser.get("https://www.google.com/imghp?hl=en")
        
        # Wait for search bar to load
        search_player = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "APjFqb"))
        ) 
        # Search player images (without Wikipedia entries)
        search_player.send_keys(player + " " + club + " -wiki")
        search_player.send_keys(Keys.ENTER)

        # Find first image
        try:  # In case no images found
            first = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "eA0Zlc"))
            )
        except TimeoutException:
            continue

        # Download source
        image = WebDriverWait(first, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "img"))
        )
        src = image.get_attribute("src")
        if "ipykernel" in sys.modules:  # If in Jupyter
            urllib.request.urlretrieve(src, filename=f"images/{player}.png")
        else:  # If in python script file
            urllib.request.urlretrieve(src, filename=f"media/images/{player}.png")


"""
def get_players(season):
    import requests
    import time
    
    base_url = "https://fbrapi.com"

    # Get API key for FBRef
    response = requests.post(base_url + "/generate_api_key")
    api_key = response.json()["api_key"]

    time.sleep(7)  # Avoid rate limit

    # Grab team roster for each Premier League team
    url = base_url + "/league-standings"
    params = {
        "league_id": "9",
        "season_id": season
    }
    headers = {"X-API-KEY": api_key}
    
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        print(response.json())
    else:
        print(response.status_code)
"""



