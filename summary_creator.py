import json
from datetime import datetime, timedelta
import re

def load_team_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def calculate_days_of_rest(game_log_content):
    lines = game_log_content.split('\n')
    game_lines = [line for line in lines if re.match(r'\|\s*\d{2}/\d{2}\s*\|', line)]

    current_date = datetime.now() - timedelta(days=1)
    last_game_date = None

    for game_line in game_lines:
        parts = game_line.split('|')
        game_date_str = parts[1].strip()

        try:
            game_date = datetime.strptime(game_date_str, '%m/%d')
            game_date = game_date.replace(year=current_date.year)
            if game_date < current_date:
                if last_game_date is None or game_date > last_game_date:
                    last_game_date = game_date
        except ValueError:
            continue

    if last_game_date:
        return (current_date - last_game_date).days
    else:
        return None

def get_last_game_result(team_data):
    game_log_content = team_data['game_log']
    lines = game_log_content.split('\n')
    game_lines = [line for line in lines if re.match(r'\|\s*\d{2}/\d{2}\s*\|', line)]

    current_date = datetime.now()
    last_game_date = None
    last_game_result = None

    for game_line in game_lines:
        parts = game_line.split('|')
        game_date_str = parts[1].strip()
        game_result = parts[5].strip()

        try:
            game_date = datetime.strptime(game_date_str, '%m/%d')
            game_date = game_date.replace(year=current_date.year)
            if game_date < current_date:
                if last_game_date is None or game_date > last_game_date:
                    last_game_date = game_date
                    last_game_result = game_result
        except ValueError:
            continue

    if last_game_date:
        return last_game_result, last_game_date.strftime('%m/%d')
    else:
        return None, None

def check_conference(team_data):
    overview_content = team_data['overview']
    lines = overview_content.split('\n')
    for line in lines:
        if 'Place' in line:
            conference_info = line.split(',')[1].strip()
            conference = conference_info.split('(')[0].strip()
            return conference
    return "Unknown"

def extract_predictive_rank(overview_content):
    match = re.search(r'Predictive rank\s+#(\d+)', overview_content)
    if match:
        return int(match.group(1))
    return None

def write_summary(file_path, summary):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(summary, file, indent=4)

def main():
    away_team_data = load_team_data('Away_Team_data.json')
    home_team_data = load_team_data('Home_Team_data.json')

    away_last_result, _ = get_last_game_result(away_team_data)
    home_last_result, _ = get_last_game_result(home_team_data)

    away_days_of_rest = calculate_days_of_rest(away_team_data['game_log'])
    home_days_of_rest = calculate_days_of_rest(home_team_data['game_log'])

    away_conference = check_conference(away_team_data)
    home_conference = check_conference(home_team_data)

    away_predictive_rank = extract_predictive_rank(away_team_data['overview'])
    home_predictive_rank = extract_predictive_rank(home_team_data['overview'])

    away_summary = {
        "Last Game": away_last_result,
        "Days of Rest": away_days_of_rest,
        "Conference": away_conference,
        "Predictive Rank": away_predictive_rank
    }
    home_summary = {
        "Last Game": home_last_result,
        "Days of Rest": home_days_of_rest,
        "Conference": home_conference,
        "Predictive Rank": home_predictive_rank
    }

    write_summary('Away_Team_Summary.json', away_summary)
    write_summary('Home_Team_Summary.json', home_summary)

if __name__ == "__main__":
    main()
