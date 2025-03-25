"""Functions to visualize shotmap data for a football player in a chosen season and competition"""

def season_shotmap(player_name, competition_name):
    """
    Returns a shotmap for a given football player in a given season

    Arguments:
    player_name = 'Firstname Lastname'
        Titlecased string
        Must include special characters if necessary, 'Kylian Mbappé'
    competition_name = 'Competition Name StartYr/EndYr'
        Titlecased string, default (YY/YY)
        See exceptions below
    
    Example Usage:
    season_shotmap('Mohamed Salah', 'Premier League 24/25')
    season_shotmap('Lionel Messi', 'UEFA Champions League 22/23')

    Known Competitions:
    Europe: 'UEFA Champions League', 'UEFA Europa League'
    International (YYYY): 'World Cup 2022', 'Copa America 2024', 'EURO 2024'
    England: 'Premier League'
    Spain: 'LaLiga'
    Italy: 'Serie A'
    France: 'Ligue 1'
    USA: 'MLS' (YYYY)
    
    Exceptions: 
    For certain competitions, input year (YYYY) 
    Examples: 'MLS', 'EURO', 'Copa America', 'World Cup'
    
    Restrictions:
    Domestic cup competitions do not have xG data and are not included
    Only works for 22/23, 23/24, 24/25 seasons due to xG data collection
    MLS only works for 2024, 2025
    """
    # Handle inputs
    player_name = player_name.strip().title()
    competition_name = competition_name.strip().title()
    if "Uefa" in competition_name:
        competition_name = competition_name.replace("Uefa", "UEFA")
    if "Euro " in competition_name:
        competition_name = competition_name.replace("Euro ", "EURO ")
    if "Laliga" in competition_name:
        competition_name = competition_name.replace("Laliga", "LaLiga")
    if "Mls" in competition_name:
        competition_name = competition_name.replace("Mls", "MLS")

    # Generate shotmap
    player_id = get_player_id(player_name)
    compiled_data = shotmap_compiler(player_id, player_name, competition_name)
    return visualize_shotmap(player_name, compiled_data, competition_name)


def get_player_id(player_name):
    """Returns SofaScore player ID for given player"""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.wait import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time
    import re

    # Search SofaScore for player url
    browser = webdriver.Chrome()
    browser.minimize_window()  # Hide operations
    browser.get("https://www.sofascore.com")

    # Wait for search input to load
    search_player = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "search-input"))
    )

    # Query player name, wait for options to load, then select first option
    search_player.send_keys(player_name)
    time.sleep(1.5)
    search_player.send_keys(Keys.ARROW_DOWN, Keys.ENTER)

    # When player url loads, grab the url and close browser
    WebDriverWait(browser, 10).until(EC.url_contains("player"))
    url = browser.current_url
    browser.quit()

    # Take player ID from end of url
    player_id = re.findall(r"-\w+/(.*)", url)
    return player_id[0]


def season_match_ids(player_id, competition_name):
    """Returns SofaScore match IDs in chosen competition for chosen player"""
    import requests
    import codes
    
    match_ids = []

    # Check to see how many pages you will need to loop through
    if competition_name.split(" ")[-1] == "24/25":
        n = 2
    elif competition_name.split(" ")[-1] == "23/24":
        n = 6
    else:
        n = 10
    
    for i in range(n):  # Loops through page numbers for more complete season data
        pg_num = i
        url = f"https://www.sofascore.com/api/v1/player/{player_id}/events/last/{pg_num}"
        response = requests.get(url, headers=codes.headers)
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get("events", [])
            
            for match in matches:
                match_filter = match.get("season")
                if match_filter["name"] == competition_name:
                    match_id = match.get("id")
                    match_ids.append(match_id)
        else:
            print(response.status_code)

    return match_ids


def get_shots(match_id, player_name):
    """Returns list of shots in a given game taken by a given player"""
    import requests
    import codes
    import pandas as pd
    
    url = f"https://www.sofascore.com/api/v1/event/{match_id}/shotmap"
    response = requests.get(url, headers=codes.headers)
    
    if response.status_code == 200:
        shots = pd.DataFrame(response.json())["shotmap"]
        data = pd.DataFrame()
        for shot in shots:
            if shot["player"]["name"] == f"{player_name}":
                x, y, _ = shot["playerCoordinates"].values()

                columns = {"shot_type": shot["shotType"],
                           "situation": shot["situation"],
                           "body_part": shot["bodyPart"],
                           "x": x,
                           "y": y,
                           "xg": shot["xg"],
                           # "xgot": shot["xgot"]
                          }
                
                if data.empty:
                    data = pd.DataFrame([columns])
                else:
                    new_data = pd.DataFrame([columns])
                    data = pd.concat([data, new_data]).reset_index(drop=True)
        return data
    else:
        print(response.code)


def shotmap_compiler(player_id, player_name, competition_name):
    """Returns compiled shot data from entire season for a given player"""
    import pandas as pd
    
    compiled_data = pd.DataFrame()
    shot_list = season_match_ids(player_id, competition_name)
    for shot in shot_list:
        match_data = get_shots(shot, player_name)
        if compiled_data.empty:
            compiled_data = match_data
        else:
            compiled_data = pd.concat([compiled_data, match_data]).reset_index(drop=True)
            
    assert not compiled_data.empty, "Player took no shots during this competition"
    
    return compiled_data


def visualize_shotmap(player_name, compiled_data, competition_name):
    """Generates shotmap visualization of given player using user shotmap data"""
    import pandas as pd
    import matplotlib.pyplot as plt
    from mplsoccer import VerticalPitch
    
    background_color = "#0C0D0E"  # Hides plotlines

    # Set up figure
    fig = plt.figure(figsize=(8, 12))
    fig.patch.set_facecolor(background_color)

    # First part of visualization, title & legend
    ax1 = fig.add_axes([0, 0.7, 1, 0.2])
    ax1.set_facecolor(background_color)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)

    # Heading, includes name of player that was inputted 
    ax1.text(
        x=0.5,
        y=0.85,
        s=player_name,
        fontsize=20,
        fontweight="bold",
        color="white",
        ha="center"  # Horizontal alignment
    )
    ax1.text(
        x=0.5,
        y=0.75,
        s=f"All non-penalty shots in the {competition_name}",
        fontsize=14,
        fontweight="bold",
        color="white",
        ha="center"
    )

    # Chance quality
    ax1.text(
        x=0.23,
        y=0.5,
        s="Low quality chance",
        fontsize=12,
        fontweight="bold",
        color="white",
        ha="center"
    )

    # Chance legend, plots rise in size to represent higher xG
    ax1.scatter(
        x=0.37,
        y=0.52,
        s=100,
        color=background_color,
        edgecolor="white",
        linewidth=0.8
    )
    
    ax1.scatter(
        x=0.42,
        y=0.52,
        s=200,
        color=background_color,
        edgecolor="white",
        linewidth=0.8
    )
    
    ax1.scatter(
        x=0.48,
        y=0.52,
        s=300,
        color=background_color,
        edgecolor="white",
        linewidth=0.8
    )
    
    ax1.scatter(
        x=0.54,
        y=0.52,
        s=400,
        color=background_color,
        edgecolor="white",
        linewidth=0.8
    )
    
    ax1.scatter(
        x=0.6,
        y=0.52,
        s=500,
        color=background_color,
        edgecolor="white",
        linewidth=0.8
    )
    
    ax1.text(
        x=0.76,
        y=0.5,
        s="High quality chance",
        fontsize=12,
        fontweight="bold",
        color="white",
        ha="center"
    )

    # Goal legend, first text & plot represent goal, second represent no goal
    ax1.text(
        x=0.44,
        y=0.27,
        s="Goal",
        fontsize=10,
        fontweight="bold",
        color="white",
        ha="right"
    )
    ax1.scatter(
        x=0.47,
        y=0.29,
        s=150,
        color="red",
        edgecolor="white",
        linewidth=0.8,
        alpha=0.7
    )
    
    ax1.text(
        x=0.54,
        y=0.27,
        s="No Goal",
        fontsize=10,
        fontweight="bold",
        color="white",
        ha="left"
    )
    ax1.scatter(
        x=0.51,
        y=0.29,
        s=150,
        color=background_color,
        edgecolor="white",
        linewidth=0.8
    )

    # Second part of visualization, shotmap on pitch
    ax2 = fig.add_axes([0.04, 0.25, 0.9, 0.5])
    ax2.set_facecolor(background_color)

    # Initialize a vertical pitch
    pitch = VerticalPitch(
        pitch_type="opta",
        half=True,
        pitch_color=background_color,
        pad_bottom=0.5,
        line_color="white",
        linewidth=0.75,
        axis=True,
        label=True
    )

    # Loop through inputted shotmap data and plot on pitch accordingly
    for shot in compiled_data.to_dict(orient="records"):
        x_coord = 100 - shot["x"]  # Align to pitch visualization 
        y_coord = 100 - shot["y"]
        if shot["situation"] != "penalty":  # Only non-penalty goals
            pitch.scatter(
                x_coord,
                y_coord,
                s=300 * shot["xg"],
                color="red" if shot["shot_type"] == "goal" else background_color,
                ax=ax2,
                alpha=0.7,
                linewidth=0.8,
                edgecolor="white"
            )
    
    pitch.draw(ax=ax2)

    # Part three of visualization, shot statistics
    ax3 = fig.add_axes([0, 0.2, 1, 0.05])
    ax3.set_facecolor(background_color)

    # Total shots
    ax3.text(
        x=0.225,
        y=0.5,
        s="Shots",
        fontsize=20,
        fontweight="bold",
        color="white",
        ha="left"
    )
    ax3.text(
        x=0.225,
        y=0,
        s=f"{len(compiled_data)}",
        fontsize=16,
        color="white",
        ha="left"
    )

    # Total goals
    ax3.text(
        x=0.365,
        y=0.5,
        s="Goals",
        fontsize=20,
        fontweight="bold",
        color="white",
        ha="left"
    )
    ax3.text(
        x=0.365,
        y=0,
        s=f"{len(compiled_data[compiled_data["shot_type"] == "goal"])}",
        fontsize=16,
        color="white",
        ha="left"
    )

    # Total xG
    ax3.text(
        x=0.505,
        y=0.5,
        s="xG",
        fontsize=20,
        fontweight="bold",
        color="white",
        ha="left"
    )
    ax3.text(
        x=0.505,
        y=0,
        s=f"{compiled_data["xg"].sum():.2f}",
        fontsize=16,
        color="white",
        ha="left"
    )

    # Average xG per shot
    ax3.text(
        x=0.645,
        y=0.5,
        s="xG/Shot",
        fontsize=20,
        fontweight="bold",
        color="white",
        ha="left"
    )
    ax3.text(
        x=0.645,
        y=0,
        s=f"{compiled_data["xg"].sum() / len(compiled_data):.2f}",
        fontsize=16,
        color="white",
        ha="left"
    )

    return fig
