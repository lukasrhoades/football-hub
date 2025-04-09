import media
import glob
import os

# Clear current images directory
files = glob.glob("media/images/*")
for file in files:
    os.remove(file)

# Fetch new images
initial_players = media.get_players(2000)
sample = media.random_selection(initial_players)
media.get_images(sample)

# Count number successful images
files = glob.glob("media/images/*")
print(len(files))