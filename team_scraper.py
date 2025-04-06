"""
This script scrapes NCAA basketball team names and their URLs from the TeamRankings website
and saves them into a JSON file.
"""

import json
import re
import requests

# Headers for the HTTP request
HEADERS = {
    'Authorization': 'Bearer jina_8b0736d9f3d348308c4bd704285dae56xV2RikInQdzzWZuR1QRrjTGfduDM',
    'X-Locale': 'en-US',
    'X-Wait-For-Selector': 'body, .class, #id',
    'X-With-Generated-Alt': 'true',
    'X-With-Iframe': 'true',
    'X-With-Images-Summary': 'true',
    'X-With-Links-Summary': 'true',
    'X-With-Shadow-Dom': 'true',
    'X-No-Cache': 'true'
}

URL = 'https://r.jina.ai/https://www.teamrankings.com/ncb/'
FILE_PATH = "data/ncaa_teams.json"

def fetch_url(url, retries=3):
    """Fetches the webpage content with retries in case of failures."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 200 and response.text:
                return response.text
            elif response.status_code == 403:
                print(f"Access forbidden for {url}. Status code: 403")
                return None
            else:
                print(f"Failed to fetch {url}. Status code: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}. Retrying {attempt + 1}/{retries}...")
    return None

# Fetch webpage content
response_text = fetch_url(URL)

if not response_text:
    raise RuntimeError("Failed to fetch the URL after multiple retries.")

# Regular expression to extract team names from URLs
PATTERN = r"https://www\.teamrankings\.com/ncaa-basketball/team/([\w-]+)"
teams = re.findall(PATTERN, response_text)

# Function to clean and format team names
def format_team_name(raw_name):
    """Formats team names properly by replacing dashes and expanding abbreviations."""
    formatted_name = raw_name.replace('-', ' ').title()
    #if len(team_name_parts) > 1:
    # team_name = ' '.join(team_name_parts[:-1])
    return formatted_name.replace(" St ", " State ")  # Expanding "St" to "State"

# Construct dictionary with formatted team names as keys and URLs as values
team_dict = {format_team_name(team): f"https://www.teamrankings.com/ncaa-basketball/team/{team}" \
             for team in teams}

# Save dictionary to a JSON file
with open(FILE_PATH, "w", encoding="utf-8") as f:
    json.dump(team_dict, f, indent=4)

print(f"Dictionary saved to {FILE_PATH}")
