import requests
from bs4 import BeautifulSoup
import csv
import json
import os
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
# Target URL for Action Network Pro Signals
URL = "https://www.actionnetwork.com/pro/signals"

# You MUST provide your session cookie to access Pro data.
# Log into Action Network in your browser, open DevTools (F12) -> Network, 
# refresh the page, click the main document request, and copy the 'cookie' string from Request Headers.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Cookie": "YOUR_PRO_SESSION_COOKIE_HERE" # <-- PASTE COOKIE HERE
}

# Output files
CSV_FILENAME = "action_signals.csv"
JSON_FILENAME = "action_signals.json"

# ==========================================
# SCRAPING LOGIC
# ==========================================
def fetch_page(url, headers):
    """Fetches the HTML content of the page."""
    print(f"Fetching data from {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the page: {e}")
        return None

def parse_signals(html_content):
    """Parses the HTML and extracts the betting splits and signals."""
    soup = BeautifulSoup(html_content, 'html.parser')
    scraped_data = []

    # NOTE: These CSS selectors (.game-row, .team-name, etc.) are placeholders.
    # Action Network frequently updates their React class names. 
    # Inspect the page and update these classes to match the current DOM.
    game_rows = soup.select('.game-row-class-placeholder') 
    
    if not game_rows:
        print("Warning: No game rows found. Check your CSS selectors or your authentication cookie.")

    for row in game_rows:
        try:
            # Extract Matchup
            away_team = row.select_one('.away-team-class').text.strip()
            home_team = row.select_one('.home-team-class').text.strip()
            matchup = f"{away_team} @ {home_team}"

            # Extract ATS Splits
            ats_bet_pct = row.select_one('.ats-bet-pct-class').text.strip()
            ats_handle_pct = row.select_one('.ats-handle-pct-class').text.strip()
            
            # Extract TOTAL Splits
            total_bet_pct = row.select_one('.total-bet-pct-class').text.strip()
            total_handle_pct = row.select_one('.total-handle-pct-class').text.strip()

            # Extract Line Movement & RLM (Reverse Line Movement)
            line_movement = row.select_one('.line-movement-class').text.strip()
            rlm_indicator = row.select_one('.rlm-indicator-class')
            rlm = "Yes" if rlm_indicator else "No"

            # Extract Pro Signals (Sharp Action, Big Money, etc.)
            signals_elements = row.select('.pro-signal-icon-class')
            signals = [sig['title'] for sig in signals_elements if sig.has_attr('title')]

            # Build the data dictionary
            game_data = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Matchup": matchup,
                "ATS_%Bets": ats_bet_pct,
                "ATS_%Handle": ats_handle_pct,
                "TOTAL_%Bets": total_bet_pct,
                "TOTAL_%Handle": total_handle_pct,
                "Line_Movement": line_movement,
                "RLM": rlm,
                "Active_Signals": ", ".join(signals)
            }
            scraped_data.append(game_data)

        except AttributeError as e:
            # Skips rows that might be missing data or are ad blocks
            print(f"Skipping a row due to missing elements: {e}")
            continue

    return scraped_data

# ==========================================
# EXPORT LOGIC
# ==========================================
def save_to_csv(data, filename):
    """Saves the list of dictionaries to a CSV file."""
    if not data:
        return
    
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    print(f"Successfully saved {len(data)} records to {filename}")

def save_to_json(data, filename):
    """Saves the list of dictionaries to a JSON file."""
    if not data:
        return
        
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"Successfully saved {len(data)} records to {filename}")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    html = fetch_page(URL, HEADERS)
    
    if html:
        extracted_data = parse_signals(html)
        
        if extracted_data:
            save_to_csv(extracted_data, CSV_FILENAME)
            save_to_json(extracted_data, JSON_FILENAME)
        else:
            print("No data extracted. Process finished.")
