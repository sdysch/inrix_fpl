import os
import requests
import pandas as pd
import argparse
from datetime import datetime

LEAGUE_ID = 993114

def get_league_data():
    league_url = f'https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/'
    return requests.get(league_url).json()


def get_manager_data(league_data):
    managers = []
    for entry in league_data['standings']['results']:
        managers.append({
            'id': entry['entry'],
            'player_name': entry['player_name'],
            'team_name': entry['entry_name']
        })
    return managers


def get_history(managers, latest_only=False):
    """Fetch all past gameweeks for each manager (used for full rebuild)."""
    all_histories = []
    now = datetime.utcnow().isoformat(timespec='seconds')
    for m in managers:
        history_url = f'https://fantasy.premierleague.com/api/entry/{m["id"]}/history/'
        history_data = requests.get(history_url).json()
        gameweeks = history_data['current'][-1:] if latest_only else history_data['current']
        for gw in gameweeks:
            all_histories.append({
                'manager': m['player_name'],
                'team': m['team_name'],
                'gameweek': gw['event'],
                'points': gw['points'],
                'total_points': gw['total_points'],
                'overall_rank': gw['overall_rank'],
                'last_updated': now
            })
    return all_histories


def main(args):
    # fetch managers
    league_data = get_league_data()
    managers = get_manager_data(league_data)

    # if full rebuild is requested
    if args.full:
        full_history = get_history(managers, latest_only=False)
        df_all = pd.DataFrame(full_history)
        df_all.to_csv(args.csv, index=False)
        max_gw = df_all['gameweek'].max()
        print(f'Forced full rebuild: saved history up to GW{max_gw} '
              f'for {len(df_all["manager"].unique())} managers')
        return

    # If csv already exists, append latest gameweek
    if os.path.exists(args.csv):
        existing = pd.read_csv(args.csv)
        latest_data = get_history(managers, latest_only=True)
        df_new = pd.DataFrame(latest_data)
        combined = pd.concat([existing, df_new], ignore_index=True)
        combined = combined.sort_values('last_updated')
        combined = combined.drop_duplicates(subset=['manager', 'gameweek'], keep='last')
        added_rows = len(combined) - len(existing)
        if added_rows > 0:
            combined.to_csv(args.csv, index=False)
            gw_num = df_new['gameweek'].iloc[0]
            print(f'Added/updated GW{gw_num} results for {added_rows} managers '
                  f'at {df_new["last_updated"].iloc[0]}')
    # otherwise, create new full history if file doesn't exist
    else:
        full_history = get_history(managers)
        df_all = pd.DataFrame(full_history)
        df_all.to_csv(args.csv, index=False)
        max_gw = df_all['gameweek'].max()
        print(f'Created new file with full history up to GW{max_gw} '
              f'for {len(df_all["manager"].unique())} managers')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', type=str, required=True, help='Output csv filename')
    parser.add_argument('--full', action='store_true', help='Force a full rebuild of history')
    args = parser.parse_args()
    main(args)

