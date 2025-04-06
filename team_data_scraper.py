"""
Module: team_data_scraper.py
This module provides functionality to scrape and fetch data for 
NCAA basketball teams from the TeamRankings website.
It allows users to input team names, find the closest matches, 
and retrieve various statistics and trends for the teams.
Functions:
    fetch_data(url_dict):
        Fetches data from the provided URLs and returns a dictionary with the fetched data.
Usage:
    1. Run the script.
    2. If data has not been scraped today, it will scrape data for all teams.
    3. Input the names of two NCAA basketball teams when prompted.
    4. The script will find the closest matches for the input teams.
    5. It will then return the data for the matched teams from the master scraped JSON.
"""
import json
import os
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
from fuzzywuzzy import fuzz, process
from tqdm import tqdm

JINA_API_KEY = 'Bearer jina_8b0736d9f3d348308c4bd704285dae56xV2RikInQdzzWZuR1QRrjTGfduDM'
JINA_API_URL = 'https://api.jina.ai/v1/rerank'
MASTER_FILE_PATH = "data/master_team_data.json"
DATE_FILE_PATH = "data/last_scrape_date.txt"
MATCHUPS_FILE_PATH = "data/matchups.json"
NCAA_TEAMS_FILE_PATH = "data/ncaa_teams.json"

headers = {
    'Authorization': JINA_API_KEY,
    'X-Locale': 'en-US',
    'X-Wait-For-Selector': 'body, .class, #id',
    'X-With-Generated-Alt': 'true',
    'X-With-Iframe': 'true',
    'X-Retain-Images': 'none',
    'X-With-Links-Summary': 'true',
    'X-With-Shadow-Dom': 'true',
    'X-Target-Selector': 'table',
    'X-Remove-Selector': 'header, footer',
    'X-No-Cache': 'true'
}

with open(NCAA_TEAMS_FILE_PATH, encoding='utf-8') as f:
    teams = json.load(f)

URL = 'https://r.jina.ai/https://www.teamrankings.com/ncaa-basketball/team/'

def rerank_with_jina(query, candidates):
    """Rerank search results using Jina Reranker API to improve accuracy."""
    payload = {
        "model": "jina-reranker-v2-base-multilingual",
        "query": query,
        "documents": candidates,
        "top_n": 1,  # Get only the best match
        "return_documents": True
    }

    rerank_headers = headers.copy()
    rerank_headers['Content-Type'] = 'application/json'

    try:
        response = requests.post(
            JINA_API_URL, headers=rerank_headers, json=payload, timeout=15)
        response_data = response.json()

        if "results" in response_data and response_data["results"]:
            best_match = response_data["results"][0]
            return best_match["document"]["text"], best_match["relevance_score"]
        else:
            print("Jina Reranker returned no results.")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"Error calling Jina API: {e}")
        return None, None

def find_best_match(input_team, available_team_names):
    """Find the best match for an input team name using fuzzy matching and Jina Reranker API."""

    # Step 1: Get initial candidates using fuzzy matching
    fuzzy_matches = process.extract(
        input_team, available_team_names, scorer=fuzz.token_sort_ratio, limit=3)
    candidate_names = [match[0] for match in fuzzy_matches]

    # Step 2: Use Jina Reranker API for final ranking
    best_match, score = rerank_with_jina(input_team, candidate_names)

    if best_match:
        print(f"Best match for '{input_team}' is '{best_match}' with a Jina relevance score of {score}")
        return best_match
    else:
        print(f"No close match found for '{input_team}'")
        return None

def fetch_url(key, url, retries=3):
    '''Fetches the content of a URL and returns the key and content.'''
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200 and response.content:
                return key, response.text
            else:
                return key, None
        except requests.exceptions.ReadTimeout:
            print(f"ReadTimeout occurred for {url}. Retrying {attempt + 1}/{retries}...")
    return key, None

def fetch_data(url_dict):
    """
    Fetches data from a dictionary of URLs concurrently.

    Args:
        url_dict (dict): A dictionary where keys are identifiers and 
        values are URLs to fetch data from.

    Returns:
        OrderedDict: An ordered dictionary where keys are the same as the input dictionary 
        and values are the fetched data as text if the request was successful, 
        otherwise None.
    """
    team_data = {}
    with ThreadPoolExecutor(max_workers=9) as executor:
        futures = {executor.submit(fetch_url, key, url): key for key, url in url_dict.items()}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching data"):
            key, result = future.result()
            team_data[key] = result

    # Reorganize the data into the original order
    ordered_team_data = OrderedDict()
    for key in url_dict.keys():
        ordered_team_data[key] = team_data.get(key)

    # Check for None values and retry fetching those URLs
    missing_data = {key: url for key, url in url_dict.items() if ordered_team_data[key] is None}
    if missing_data:
        print("Retrying for missing data...")
        retry_data = fetch_data(missing_data)
        if retry_data is not None:
            for key, value in retry_data.items():
                ordered_team_data[key] = value

    return ordered_team_data

def scrape_selected_teams():
    """Scrape data for teams listed in matchups.json."""
    with open(MATCHUPS_FILE_PATH, encoding='utf-8') as f:
        matchups = json.load(f)

    selected_teams = set()
    for matchup in matchups:
        away_team = find_best_match(matchup["teams"]["away"]["full_name"], teams.keys())
        home_team = find_best_match(matchup["teams"]["home"]["full_name"], teams.keys())
        if away_team:
            selected_teams.add(away_team)
        if home_team:
            selected_teams.add(home_team)
    selected_teams = list(selected_teams)

    all_team_data = {}
    for team_name in selected_teams:
        team_url = teams.get(team_name)
        if team_url:
            urls = OrderedDict([
                ("win_trends", f"{team_url}/win-trends"),
                ("ats_trends", f"{team_url}/ats-trends"),
                ("over_under_trends", f"{team_url}/over-under-trends"),
                ("overview", team_url),
                ("stats", f"{team_url}/stats"),
                ("power_ratings", f"{team_url}/rankings"),
                ("game_log", f"{team_url}/game-log"),
                ("ats_results", f"{team_url}/ats-results"),
                ("over_under_results", f"{team_url}/over-under-results")
            ])
            data = fetch_data(urls)
            all_team_data[team_name] = data

    with open(MASTER_FILE_PATH, "w", encoding='utf-8') as master_file:
        json.dump(all_team_data, master_file, ensure_ascii=False, indent=4)

    with open(DATE_FILE_PATH, "w", encoding='utf-8') as date_file:
        date_file.write(datetime.now().strftime("%Y-%m-%d"))

    print(f"Selected team data scraped and saved to {MASTER_FILE_PATH}")

def check_and_scrape_data():
    """Check if data has been scraped today and scrape if not."""
    if os.path.exists(DATE_FILE_PATH):
        with open(DATE_FILE_PATH, "r", encoding='utf-8') as date_file:
            last_scrape_date = date_file.read().strip()
    else:
        last_scrape_date = ""

    current_date = datetime.now().strftime("%Y-%m-%d")

    if last_scrape_date != current_date:
        print("Scraping data for selected teams...")
        scrape_selected_teams()
    else:
        print("Data has already been scraped today.")

def handle_user_input():
    """Handle user input for team names and fetch their data."""
    # Load the master team data
    with open(MASTER_FILE_PATH, "r", encoding='utf-8') as master_file:
        master_team_data = json.load(master_file)

    # Load the matchups data
    with open(MATCHUPS_FILE_PATH, encoding='utf-8') as f:
        matchups = json.load(f)

    # Create a dictionary to map shorthand names to full names
    shorthand_to_full = {}
    for matchup in matchups:
        shorthand_to_full[matchup["teams"]["away"]["shorthand"].lower()] = matchup["teams"]["away"]["full_name"]
        shorthand_to_full[matchup["teams"]["home"]["shorthand"].lower()] = matchup["teams"]["home"]["full_name"]

    # Prompt user for team names
    away_team_input = input("Enter the away team shorthand: ").lower()
    away_team_full_name = shorthand_to_full.get(away_team_input)

    home_team_input = input("Enter the home team shorthand: ").lower()
    home_team_full_name = shorthand_to_full.get(home_team_input)

    # Return the data for the matched teams
    if away_team_full_name and home_team_full_name:
        away_team_data = master_team_data.get(away_team_full_name, {})
        home_team_data = master_team_data.get(home_team_full_name, {})
        print(f"Away Team Data: {json.dumps(away_team_data, indent=4)}")
        print(f"Home Team Data: {json.dumps(home_team_data, indent=4)}")
    else:
        print("One or both team names could not be matched.")

def main():
    check_and_scrape_data()
    handle_user_input()

if __name__ == "__main__":
    main()
