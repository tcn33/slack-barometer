import sqlite3
import random

DB_FILE = "emoji_tracker.db"

# We only hardcode standard emojis now. Custom ones will be fetched dynamically from your DB!
STANDARD_EMOJIS = [
    "thumbsup", "eyes", "heart", "fire", "tada", "rocket", "clap", 
    "sweat_smile", "joy", "cry", "thinking_face", "pleading_face", 
    "pray", "hundred", "skull"
]

MOCK_CHANNELS = ["general", "random", "engineering", "marketing", "watercooler"]
MOCK_WEEKS = ["2026-W18", "2026-W19", "2026-W20", "2026-W21", "2026-W22", "2026-W23"]

def main():
    print("Generating synthetic database entries aligned with your live workspace...")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Check if we have live custom emojis downloaded by app.py
    # If the custom_emojis table doesn't exist yet, we create it.
    c.execute('''CREATE TABLE IF NOT EXISTS custom_emojis 
                 (emoji_name TEXT PRIMARY KEY, local_path TEXT)''')
    
    c.execute("SELECT emoji_name FROM custom_emojis")
    live_custom_emojis = [row[0] for row in c.fetchall()]
    
    if not live_custom_emojis:
        print("\n⚠️ WARNING: No live custom emojis found in your database.")
        print("Please run 'python3 app.py' first to pull your workspace custom emojis!")
        conn.close()
        return

    print(f" -> Found {len(live_custom_emojis)} live custom emojis in your database: {', '.join(live_custom_emojis)}")

    # 2. Recreate ONLY the weekly counts table (leaving your custom_emojis table intact!)
    c.execute("DROP TABLE IF EXISTS weekly_emojis")
    c.execute('''CREATE TABLE IF NOT EXISTS weekly_emojis 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, run_date TEXT, emoji_name TEXT, count INTEGER, top_channel TEXT)''')
    conn.commit()

    # Combine standard emojis and your live custom emojis for the history generator
    all_emojis = {}
    for name in STANDARD_EMOJIS:
        all_emojis[name] = 100 # Standard baseline count
        
    for name in live_custom_emojis:
        all_emojis[name] = 150 # Custom emojis get a slightly higher baseline to keep them in the top 20!

    # 3. Populate weekly counts
    for week in MOCK_WEEKS:
        print(f" -> Generating trends for week {week}...")
        for name, base_count in all_emojis.items():
            
            # Add some fun volatility
            volatility = random.uniform(0.75, 1.25)
            final_count = int(base_count * volatility)
            top_channel = random.choice(MOCK_CHANNELS)
            
            c.execute("INSERT INTO weekly_emojis (run_date, emoji_name, count, top_channel) VALUES (?, ?, ?, ?)",
                      (week, name, final_count, top_channel))
            
    conn.commit()
    conn.close()
    print("\nSuccess! Synthetic trends generated using your live custom emoji files!")

if __name__ == "__main__":
    main()

