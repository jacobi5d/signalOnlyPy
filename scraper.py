import os
import json
import csv
from playwright.sync_api import sync_playwright

# Define target endpoints
LOGIN_URL = "https://www.actionnetwork.com/login"
SIGNALS_URL = "https://www.actionnetwork.com/pro-systems/discover"
INJURY_URL = "https://www.actionnetwork.com/nfl/injuries"

def extract_next_data(page, url):
    """Navigates to the target URL and extracts the __NEXT_DATA__ JSON payload."""
    page.goto(url, wait_until="networkidle")
    
    # Locate the hydration script tag utilized by Next.js
    script_element = page.locator("script#__NEXT_DATA__")
    if script_element.count() > 0:
        raw_json = script_element.inner_text()
        return json.loads(raw_json)
    return None

def process_signals_data(json_data):
    """Traverses the hierarchical JSON to extract relevant PRO signal metrics."""
    signals_list =  # Fix: Added missing brackets to initialize the list
    try:
        # Note: The exact dictionary traversal path requires adjustment based on the live schema
        games = json_data['props']['pageProps']['games']
        for game_id, game_data in games.items():
            signals_list.append({
                'game_id': game_id,
                'home_team': game_data.get('home_team_name', 'N/A'),
                'away_team': game_data.get('away_team_name', 'N/A'),
                'public_betting_pct': game_data.get('public_betting_pct', 0),
                'sharp_action_flag': game_data.get('sharp_action', False),
                'money_pct': game_data.get('money_pct', 0)
            })
    except KeyError:
        pass
    return signals_list

def process_injury_data(json_data):
    """Traverses the hierarchical JSON to extract roster physiological statuses."""
    injury_list =  # Fix: Added missing brackets to initialize the list
    try:
        players = json_data['props']['pageProps']['injuries']
        for player in players:
            injury_list.append({
                'player_name': player.get('full_name', 'N/A'),
                'team': player.get('team_name', 'N/A'),
                'status': player.get('status', 'N/A'),
                'description': player.get('description', 'N/A')
            })
    except KeyError:
        pass
    return injury_list

    # Save to JSON for archival preservation
    with open(f"{filename_prefix}.json", "w") as json_file:
        json.dump(data_list, json_file, indent=4)

    # Save to CSV for downstream algorithmic ingestion
    keys = data_list.keys()
    with open(f"{filename_prefix}.csv", "w", newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data_list)

def main():
    email = os.environ.get("ACTION_EMAIL")
    password = os.environ.get("ACTION_PASSWORD")

    if not email or not password:
        raise ValueError("Critical Security Error: Credentials not found in environment.")

    with sync_playwright() as p:
        # Launch Chromium. In production, proxy arguments would be appended here.
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Step 1: Execute Authentication Sequence
        page.goto(LOGIN_URL, wait_until="networkidle")
        page.locator('input[name="email"]').fill(email)
        page.locator('input[name="password"]').fill(password)
        page.locator('button[type="submit"]').click()
        page.wait_for_load_state("networkidle")

        # Step 2: Extract PRO Signals Data
        signals_json = extract_next_data(page, SIGNALS_URL)
        if signals_json:
            processed_signals = process_signals_data(signals_json)
            save_to_json_and_csv(processed_signals, "signals_data")

        # Step 3: Extract Injury Report Data
        injury_json = extract_next_data(page, INJURY_URL)
        if injury_json:
            processed_injuries = process_injury_data(injury_json)
            save_to_json_and_csv(processed_injuries, "injury_data")

        browser.close()

if __name__ == "__main__":
    main()
