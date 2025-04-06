import json

def main():
    # File paths
    away_team_data_path = 'Away_Team_data.json'
    away_team_summary_path = 'Away_Team_Summary.json'
    home_team_data_path = 'Home_Team_data.json'
    home_team_summary_path = 'Home_Team_Summary.json'

    # Load JSON data
    with open(away_team_data_path, 'r', encoding='utf-8') as file:
        away_team_data = json.load(file)

    with open(away_team_summary_path, 'r', encoding='utf-8') as file:
        away_team_summary = json.load(file)

    with open(home_team_data_path, 'r', encoding='utf-8') as file:
        home_team_data = json.load(file)

    with open(home_team_summary_path, 'r', encoding='utf-8') as file:
        home_team_summary = json.load(file)

    # Combine JSON data with more structure
    combined_data = {
        "game": {
            "away_team": {
                "data": away_team_data,
                "summary": away_team_summary
            },
            "home_team": {
                "data": home_team_data,
                "summary": home_team_summary
            }
        }
    }

    # Remove specified fields
    for team in ["away_team", "home_team"]:
        for field in ["stats", "game_log", "ats_results", "over_under_results"]:
            if field in combined_data["game"][team]["data"]:
                del combined_data["game"][team]["data"][field]

    # Save combined JSON data to a new file
    output_path = 'combined_data.json'
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(combined_data, file, indent=4)

    print(f"Combined JSON data saved to {output_path}")

if __name__ == "__main__":
    main()