"""
This module runs a series of scripts for team data scraping, summary creation, and JSON merging.
"""

import team_data_scraper
import summary_creator
import json_merger

def run_script():
    """
    Runs a series of predefined scripts using subprocess.
    """
    team_data_scraper.main()
    summary_creator.main()
    json_merger.main()

run_script()
