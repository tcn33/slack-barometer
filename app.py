import os
import sqlite3
import datetime
import urllib.request
from collections import defaultdict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
DB_FILE = "emoji_tracker.db"
EMOJI_FOLDER = os.path.join("static", "custom_emojis")
DAYS_TO_FETCH = 90

os.makedirs(EMOJI_FOLDER, exist_ok=True)
client = WebClient(token=SLACK_BOT_TOKEN)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Added 'top_channel' column
    c.execute('''
        CREATE TABLE IF NOT EXISTS weekly_emojis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT,
            emoji_name TEXT,
            count INTEGER,
            top_channel TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS custom_emojis (
            emoji_name TEXT PRIMARY KEY,
            local_path TEXT
        )
    ''')
    conn.commit()
    return conn

def sync_custom_emojis(conn):
    print("Syncing custom workspace emojis...")
    c = conn.cursor()
    try:
        response = client.emoji_list()
        custom_emojis = response.get("emoji", {})
        for name, url in custom_emojis.items():
            if url.startswith("alias:"): continue
            c.execute("SELECT local_path FROM custom_emojis WHERE emoji_name = ?", (name,))
            if c.fetchone() is not None: continue
                
            ext = url.split(".")[-1].split("?")[0]
            local_path = os.path.join(EMOJI_FOLDER, f"{name}.{ext}")
            try:
                urllib.request.urlretrieve(url, local_path)
                c.execute("INSERT OR REPLACE INTO custom_emojis (emoji_name, local_path) VALUES (?, ?)", (name, local_path))
                conn.commit()
            except Exception as e:
                print(f"Failed to download :{name}: {e}")
    except SlackApiError as e:
        print(f"Error fetching custom emojis: {e}")

def get_channels_info():
    """Returns a dictionary mapping channel_id to channel_name"""
    try:
        response = client.conversations_list(types="public_channel")
        channels = response["channels"]
        channel_info = {}

        for channel in channels:
            channel_id = channel["id"]
            channel_name = channel["name"]
            channel_info[channel_id] = channel_name
            
            if not channel["is_member"]:
                try:
                    client.conversations_join(channel=channel_id)
                except SlackApiError:
                    pass
        return channel_info
    except SlackApiError as e:
        print(f"Error fetching channels: {e}")
        return {}

def get_reactions_by_channel(channel_info, oldest_timestamp):
    # Dictionary structure: { "emoji_name": { "channel_name": count } }
    emoji_stats = defaultdict(lambda: defaultdict(int))
    
    for channel_id, channel_name in channel_info.items():
        try:
            result = client.conversations_history(channel=channel_id, oldest=oldest_timestamp, limit=200)
            for message in result["messages"]:
                if "reactions" in message:
                    for reaction in message["reactions"]:
                        emoji_stats[reaction["name"]][channel_name] += reaction["count"]
        except SlackApiError as e:
            print(f"Error in #{channel_name}: {e}")
            
    return emoji_stats

def main():
    if not SLACK_BOT_TOKEN:
        print("Error: SLACK_BOT_TOKEN missing.")
        return

    conn = init_db()
    sync_custom_emojis(conn)
    
    c = conn.cursor()
    # Define "Work Week" using ISO Year and Week Number (e.g., "2023-W42")
    current_week_str = datetime.date.today().strftime("%Y-W%W")
    
    oldest_dt = datetime.datetime.now() - datetime.timedelta(days=DAYS_TO_FETCH)
    oldest_ts = oldest_dt.timestamp()

    print("Fetching channel list...")
    channel_info = get_channels_info()
    
    print(f"Fetching reactions since {oldest_dt.date()}...")
    emoji_stats = get_reactions_by_channel(channel_info, oldest_ts)

    # Delete existing data for this week if running the script multiple times a week
    c.execute("DELETE FROM weekly_emojis WHERE run_date = ?", (current_week_str,))

    # Save to database
    for emoji, channel_counts in emoji_stats.items():
        total_count = sum(channel_counts.values())
        top_channel = max(channel_counts, key=channel_counts.get) # Finds channel with highest count
        
        c.execute("INSERT INTO weekly_emojis (run_date, emoji_name, count, top_channel) VALUES (?, ?, ?, ?)",
                  (current_week_str, emoji, total_count, top_channel))
    conn.commit()
    print("Run complete!")

if __name__ == "__main__":
    main()

