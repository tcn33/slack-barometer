import sqlite3
import emoji
import datetime
from flask import Flask, render_template

app = Flask(__name__)
DB_FILE = "emoji_tracker.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def convert_to_unicode(emoji_name):
    return emoji.emojize(f":{emoji_name}:", language='alias')

@app.route("/")
def index():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("SELECT DISTINCT run_date FROM weekly_emojis ORDER BY run_date DESC LIMIT 2")
    dates = [row['run_date'] for row in c.fetchall()]
    
    if not dates: return "No data found! Run app.py first."

    latest_week = dates[0]
    prev_week = dates[1] if len(dates) > 1 else None

    try:
        # "%w-0" parses the Sunday (0) of that specific year (%Y) and week (%W)
        sunday_date = datetime.datetime.strptime(latest_week + "-0", "%Y-W%W-%w")
        week_ending = sunday_date.strftime("%B %d, %Y")  # e.g., "June 14, 2026"
    except Exception:
        week_ending = latest_week  # Fallback to "2026-W23" if parsing fails

    # Get ALL emojis for current week to calculate global rank
    c.execute("SELECT emoji_name, count, top_channel FROM weekly_emojis WHERE run_date = ? ORDER BY count DESC", (latest_week,))
    latest_rows = c.fetchall()
    
    current_ranks = {row['emoji_name']: rank for rank, row in enumerate(latest_rows, 1)}

    # Get ALL emojis for previous week to calculate past rank
    prev_ranks = {}
    prev_counts = {}
    if prev_week:
        c.execute("SELECT emoji_name, count FROM weekly_emojis WHERE run_date = ? ORDER BY count DESC", (prev_week,))
        for rank, row in enumerate(c.fetchall(), 1):
            prev_ranks[row['emoji_name']] = rank
            prev_counts[row['emoji_name']] = row['count']

    # Get custom emojis paths
    c.execute("SELECT emoji_name, local_path FROM custom_emojis")
    custom_paths = {row['emoji_name']: row['local_path'].replace("static/", "").replace("static\\", "") for row in c.fetchall()}

    # Assemble Top 20 for dashboard
    dashboard_data = []
    for row in latest_rows[:20]: # Only display top 20
        name = row['emoji_name']
        rank = current_ranks[name]
        count = row['count']
        top_channel = row['top_channel']
        
        # Calculate Rank Change (Prev Rank - Current Rank)
        # e.g., was #5, now #2 -> 5 - 2 = +3 spots
        prev_rank = prev_ranks.get(name)
        rank_change = (prev_rank - rank) if prev_rank else None
        
        count_diff = count - prev_counts.get(name, 0)
        
        custom_path = custom_paths.get(name)
        display_emoji = None if custom_path else convert_to_unicode(name)

        dashboard_data.append({
            "rank": rank,
            "name": name,
            "count": count,
            "count_diff": count_diff,
            "rank_change": rank_change,
            "is_new": prev_rank is None,
            "top_channel": top_channel,
            "custom_path": custom_path,
            "display_emoji": display_emoji
        })

    conn.close()
    return render_template("index.html", emojis=dashboard_data, week_ending=week_ending)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

