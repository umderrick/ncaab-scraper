import re

import pandas as pd
import requests

# Define API URL
URL = 'https://r.jina.ai/https://barttorvik.com/?year=2025&sort=&hteam=&t2value=&conlimit=All&state=All&begin=20241104&end=20250501&top=0&revquad=0&quad=5&venue=All&type=All&mingames=0#'

# Define Headers for Jina API
headers = {
    'Authorization': 'Bearer jina_8b0736d9f3d348308c4bd704285dae56xV2RikInQdzzWZuR1QRrjTGfduDM',
    'X-Locale': 'en-US',
    'X-With-Generated-Alt': 'true',
    'X-With-Iframe': 'true',
    'X-Retain-Images': 'none',
    'X-With-Links-Summary': 'true',
    'X-With-Shadow-Dom': 'true',
    'X-Target-Selector': 'table',
    'X-Remove-Selector': 'header, footer',
    'X-No-Cache': 'true'
}

# Function to fetch the data from Jina API


def fetch_data(url):
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200 and response.content:
            return response.text
        print(f"Failed to fetch data from {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


# Fetch data
data = None
attempts = 3
for attempt in range(attempts):
    data = fetch_data(URL)
    if data:
        break
    print(f"Attempt {attempt + 1} failed, retrying...")

if not data:
    raise RuntimeError(
        "Failed to retrieve webpage data after multiple attempts.")

# Save the raw HTML data to a text file
RAW_FILE = "torvik_data.txt"
with open(f"data/{RAW_FILE}", "w", encoding="utf-8") as file:
    file.write(data)

# Load file content
with open(f"data/{RAW_FILE}", "r", encoding="utf-8") as file:
    lines = file.readlines()

# Headers for the table
headers = [
    "Rk", "Team", "Conf", "G", "Rec", "ConfRec", "AdjOE", "AdjDE", "Barthag",
    "EFG%", "EFGD%", "TOR", "TORD", "ORB", "DRB", "FTR", "FTRD",
    "2P%", "2P%D", "3P%", "3P%D", "3PR", "3PRD", "Adj T.", "WAB"
]

# Regular expression to detect team entries
team_pattern = re.compile(
    r"\|\s*(\d+)\s*\|\s*\[(.*?)\]\(.*?\)\s*\|\s*\[(.*?)\]\(.*?\)\s*\|\s*(\d+)\s*\|\s*\[(.*?)\]\(.*?\)\s*")

processed_data = []
current_row = []
stat_values = []

for line in lines:
    line = line.strip()

    # Detect start of a new team row
    match = team_pattern.match(line)
    if match:
        if current_row and len(stat_values) == len(headers) - len(current_row):
            # Append extracted stat values to the current row
            current_row.extend(stat_values)
            processed_data.append(current_row)

        # Start a new row with Rank, Team, Conference, Games, and Record
        current_row = list(match.groups())
        stat_values = []

    else:
        # Extract stats, ignoring ranking index before each value
        values = [x.strip() for x in line.split("|") if x.strip()]

        # **Fix: Ensure conference record is properly captured**
        if len(stat_values) == 0 and len(values) >= 2:
            stat_values.append(values[0])  # Conference record

        # **Fix: Ensure each stat value is properly captured**
        # Take every second value to remove ranking indices
        filtered_values = values[1::2]
        stat_values.extend(filtered_values)

# Append last row if complete
if current_row and len(stat_values) == len(headers) - len(current_row):
    current_row.extend(stat_values)
    processed_data.append(current_row)
column_explanations = {
    "Rk": "Rank",
    "Team": "Team Name",
    "Conf": "Conference",
    "G": "Games Played",
    "Rec": "Record (Wins-Losses)",
    "ConfRec": "Conference Record",
    "AdjOE": "Adjusted Offensive Efficiency (Points per 100 possessions, adjusted for opponent strength)",
    "AdjDE": "Adjusted Defensive Efficiency (Points allowed per 100 possessions, adjusted for opponent strength)",
    "Barthag": "Bart Torvik's Power Rating (Probability of beating an average Division I team)",
    "EFG%": "Effective Field Goal Percentage",
    "EFGD%": "Effective Field Goal Percentage Defense",
    "TOR": "Turnover Rate (Percentage of possessions ending in a turnover)",
    "TORD": "Turnover Rate Defense (Opponent's turnover rate)",
    "ORB": "Offensive Rebound Percentage",
    "DRB": "Defensive Rebound Percentage",
    "FTR": "Free Throw Rate (FTA/FGA - How often a team gets to the free-throw line)",
    "FTRD": "Free Throw Rate Defense (Opponent’s free throw rate)",
    "2P%": "Two-Point Field Goal Percentage",
    "2P%D": "Two-Point Field Goal Percentage Defense",
    "3P%": "Three-Point Field Goal Percentage",
    "3P%D": "Three-Point Field Goal Percentage Defense",
    "3PR": "Three-Point Attempt Rate (Percentage of field goal attempts that are three-pointers)",
    "3PRD": "Three-Point Attempt Rate Defense (Opponent's three-point attempt rate)",
    "Adj T.": "Adjusted Tempo (Possessions per 40 minutes, adjusted for opponent pace)",
    "WAB": "Wins Above Bubble (Measures how many wins a team has above the expected wins of a 'bubble' team)"
}

# Convert to DataFrame
df = pd.DataFrame(processed_data, columns=headers)
df["Team"] = df["Team"].str.replace(
    r"\s*\(H\).*|\s*\(A\).*|\s*\(N\).*", "", regex=True)
# Remove trailing spaces in the row variable values
df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
# **Fix: Drop rows with incorrect column counts**
df = df.dropna()

# Add column explanations to the header row
df.columns = [f"{col} ({column_explanations[col]})" for col in df.columns]

# Clean team names in the Markdown file
MARKDOWN_FILE = "torvik_data.txt"
with open(f"data/{MARKDOWN_FILE}", "w", encoding="utf-8") as file:
    markdown_text = df.to_markdown(index=False)
    markdown_text = re.sub(
        r"(\b[A-Za-z ]+?)(?:\s*\(H\)|\s*\(A\)|\s*\(N\)).*?\|", r"\1 |", markdown_text)
    file.write(markdown_text)

print(f"Rankings table successfully parsed and saved as '{MARKDOWN_FILE}'.")
