import json
import re

import requests

URL = 'https://r.jina.ai/https://apnews.com/hub/ap-top-25-college-basketball-poll'

headers = {
    'Authorization': 'Bearer jina_8b0736d9f3d348308c4bd704285dae56xV2RikInQdzzWZuR1QRrjTGfduDM',
    'X-Locale': 'en-US',
    'X-Wait-For-Selector': 'body, .class, #id',
    'X-With-Generated-Alt': 'true',
    'X-With-Iframe': 'true',
    'X-Retain-Images': 'none',
    'X-With-Links-Summary': 'true',
    'X-With-Shadow-Dom': 'true',
    'X-Target-Selector': 'body > div.Page-content > main > div:nth-child(1) > div',
    'X-Remove-Selector': 'header, footer',
    'X-No-Cache': 'true'
}


def fetch_data(url):
    """
    Fetches data from the provided URL.

    Args:
        url (str): The URL to fetch data from.

    Returns:
        str: The fetched data as text if the request was successful, otherwise None.
    """
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200 and response.content:
            print(response.text)
            return response.text
        else:
            print(f"Failed to fetch data from {url}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def parse_rankings(text):
    """
    Parses rankings from the response text using regex.

    Args:
        text (str): The text containing rankings.

    Returns:
        list: A list of dictionaries with team rankings.
    """
    # Adjust the pattern to match the structure of the rankings in the text
    pattern = r"Links/Buttons:\s*(.*?)\s*AP Top 25"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        links_section = match.group(1)
        team_pattern = r"\[(.*?)\]\(https://apnews.com/hub/.*?-mens-basketball/?\)"
        teams = re.findall(team_pattern, links_section)
    else:
        teams = []

    rankings = [{"AP Ranking": i + 1, "team": team}
                for i, team in enumerate(teams)]
    return rankings


def main():
    rankings = parse_rankings(fetch_data(URL))

    # Save to JSON file
    with open("AP_Top_25_College_Basketball_Poll.json", "w", encoding="utf-8") as file:
        json.dump(rankings, file, ensure_ascii=False, indent=4)

    print("Data has been successfully parsed and saved.")
    print(rankings)  # Print to verify


if __name__ == "__main__":
    main()
