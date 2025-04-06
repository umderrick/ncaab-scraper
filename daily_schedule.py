import json
import re
import requests

# Headers for request
headers = {
    'Authorization': 'Bearer jina_8b0736d9f3d348308c4bd704285dae56xV2RikInQdzzWZuR1QRrjTGfduDM',
    'X-Locale': 'en-US',
    'X-Wait-For-Selector': 'body, .class, #id',
    'X-With-Generated-Alt': 'true',
    'X-With-Iframe': 'true',
    'X-With-Images-Summary': 'true',
    'X-With-Links-Summary': 'true',
    'X-With-Shadow-Dom': 'true',
    'X-No-Cache': 'true',
    'X-Target-Selector': '#tab-latest-odds',
}

URL = 'https://r.jina.ai/https://www.teamrankings.com/ncb/odds/'
FILE_PATH = "./data/raw_data.txt"

# Function to fetch data
def fetch_data(url, request_headers, retries=3):
    for _ in range(retries):
        try:
            response = requests.get(url, headers=request_headers, timeout=30)
            if response.status_code == 200:
                return response.text
            else:
                print(f"Error: Received status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
    return None  # Return None if all retries fail

# Fetch and save HTML data
data = fetch_data(URL, headers)

if data:
    with open(FILE_PATH, "w", encoding="utf-8") as file:
        file.write(data)
else:
    print("Failed to fetch data, exiting.")
    exit()

with open(FILE_PATH, "r", encoding="utf-8") as file:
    lines = file.readlines()

# Regex pattern to detect start of a matchup (Game Time)
start_pattern = re.compile(r"\|\s*(\d{1,2}:\d{2}\s*(?:AM|PM)\s*EST)\s*\|")

# Regex pattern to detect the end of a matchup
end_pattern = re.compile(r"\|\s*\[Full betting preview »\]")

# Function to clean and format team names
def format_team_name(raw_name):
    """Formats team names properly by replacing dashes and expanding abbreviations."""
    formatted_name = raw_name.replace('-', ' ').title()
    return formatted_name.replace(" St ", " State ")  # Expanding "St" to "State"

# Function to extract key details from a single matchup line
def extract_team_data(matchup_line):
    # Example input format:
    # | **[N Colorado](https://www.teamrankings.com/ncaa-basketball/team/northern-colorado-bears)** |  | \-4.0 | 153.5 | \-180 |

    pattern = re.search(
        r"\*\*\[(.*?)\]\(https://www\.teamrankings\.com/ncaa-basketball/team/([-a-z0-9]+)\)\*\*\s*\|\s*\|\s*((?:\\-|\+)?\d+\.\d+)?\s*\|\s*(\d+\.\d+)?\s*\|\s*((?:\\-|\+)?\d+)", 
        matchup_line
    )

    if not pattern:
        return None, None, None, None, None  # Return all values as None if no match
    
    shorthand_team = pattern.group(1)  # Displayed shorthand team name (e.g., "N Colorado")
    full_team_url = pattern.group(2)  # Extracted team name from URL (e.g., "northern-colorado-bears")
    full_team = format_team_name(full_team_url)  # Convert to formatted name (e.g., "Northern Colorado Bears")
    
    spread = float(pattern.group(3).lstrip("\\")) if pattern.group(3) else None  # Strip the backslash before -
    total = float(pattern.group(4)) if pattern.group(4) else None  # Over/Under
    moneyline = int(pattern.group(5).lstrip("\\")) if pattern.group(5) else None  # Strip the backslash before -

    return shorthand_team, full_team, spread, total, moneyline

# Function to parse a full matchup block
def parse_matchup(matchup_lines):
    if len(matchup_lines) < 4:  # Ensure enough data exists
        return None

    # Extract game time from the first line
    time_match = re.search(r"\|\s*([\d:APM\s]+EST)\s*\|", matchup_lines[0])
    if not time_match:
        return None
    game_time = time_match.group(1)

    # Extract for away team (line 2) and home team (line 3)
    away_shorthand, away_full, away_spread, total, away_moneyline = extract_team_data(matchup_lines[2])
    home_shorthand, home_full, home_spread, _, home_moneyline = extract_team_data(matchup_lines[3])  # Total already extracted

    if not away_shorthand or not home_shorthand:
        return None  # Skip if teams are missing

    return {
        "time": game_time,
        "teams": {
            "away": {
                "shorthand": away_shorthand,
                "full_name": away_full
            },
            "home": {
                "shorthand": home_shorthand,
                "full_name": home_full
            }
        },
        "spread": {
            "away": away_spread,
            "home": home_spread
        },
        "total": {
            "over/under": total
        },
        "moneyline": {
            "away": away_moneyline,
            "home": home_moneyline
        }
    }

# Extract matchups from file
matchups = []
current_matchup = []
collecting = False

for line in lines:
    if start_pattern.search(line):
        if current_matchup:
            parsed_matchup = parse_matchup(current_matchup)
            if parsed_matchup:
                matchups.append(parsed_matchup)
            current_matchup = []
        collecting = True

    elif end_pattern.search(line) and collecting:
        current_matchup.append(line)
        parsed_matchup = parse_matchup(current_matchup)
        if parsed_matchup:
            matchups.append(parsed_matchup)
        current_matchup = []
        collecting = False

    if collecting:
        current_matchup.append(line)

# Convert to JSON format
json_output = json.dumps(matchups, indent=4)
print(json_output)

# Save matchups to a JSON file
with open("./data/matchups.json", "w", encoding="utf-8") as f:
    json.dump(matchups, f, indent=4)
