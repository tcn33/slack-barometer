# Ferocia Vibe Barometer 🌤️

A Python and Flask-based web application that tracks your Slack workspace's emoji usage, calculates week-over-week trends, and displays the most popular reactions in a beautiful, Slack-native dashboard.

Officevibe is how people tell you they feel. Slack reactions tell the **real** story of the office vibe this week.

![An example screenshot](screenshot.png)

## Prerequisites
* Python 3.9+
* A Slack Workspace where you have permission to install Apps

---

## 1. Slack Bot Setup & Required Scopes

Before running any code, you need to create a Slack App and get an OAuth token.

1. Go to the [Slack API Apps page](https://api.slack.com/apps) and click **Create New App** > **From scratch**.
2. Name it (e.g., "Emoji Barometer") and select your workspace.
3. In the left sidebar, navigate to **OAuth & Permissions**.
4. Scroll down to **Scopes > Bot Token Scopes** and add the following exactly:
   * `channels:history` *(Allows the bot to count reactions on messages)*
   * `channels:read` *(Allows the bot to see a list of all public channels)*
   * `channels:join` *(Allows the bot to automatically join public channels to read them)*
   * `emoji:read` *(Allows the bot to download your workspace's custom emojis)*
5. Scroll up and click **Install to Workspace** (or **Reinstall to Workspace** if you are updating scopes).
6. Copy the **Bot User OAuth Token** (it starts with `xoxb-`).

---

## 2. Local Installation

1. **Clone or create your project folder** and ensure all Python scripts and your `templates` folder are present.
2. **Install dependencies:**
   ```bash
   pip install slack_sdk python-dotenv flask emoji
   ```
3. **Configure your Environment:**
   Create a `.env` file in the root of your project directory and add your Slack token:
   ```env
   SLACK_BOT_TOKEN="xoxb-your-token-goes-here"
   ```

---

## Option A: Running with Synthetic Data (For Testing/Development)

If your test Slack workspace doesn't have weeks of message history, you can generate 6 weeks of realistic, fluctuating synthetic data. *Note: This process pulls your actual custom emojis from Slack, but fakes the usage numbers.*

1. **Delete any existing database** to start fresh:
   ```bash
   rm emoji_tracker.db
   ```
2. **Pull your workspace emojis:**
   Run the main app script once. This connects to Slack, downloads your real custom emojis (`.gif`, `.png`) to the `static/custom_emojis` folder, and registers them in the database.
   ```bash
   python3 app.py
   ```
3. **Generate 6 weeks of synthetic trends:**
   This script reads your downloaded emojis and generates realistic week-over-week data (Up/Down trends, top channels, etc.).
   ```bash
   python3 generate_synthetic_data.py
   ```
4. **Start the Web Dashboard:**
   ```bash
   python3 web.py
   ```
   Open your browser to [http://127.0.0.1:5000](http://127.0.0.1:5000) to view the synthetic dashboard.

---

## Option B: Running with Real Data (Production)

To run the app using actual, live reaction counts from your Slack workspace:

1. **Clear out any synthetic data** by deleting the database:
   ```bash
   rm emoji_tracker.db
   ```
2. **Run the data gatherer:**
   The `app.py` script will crawl all public channels, join them if necessary, count the reactions over the last 90 days, download any new custom emojis, and save the data for the current work week.
   ```bash
   python3 app.py
   ```
   *(Note: The bot will post a "joined channel" message the first time it enters a public channel. Slack Admins can disable this workspace-wide if desired).*
3. **Start the Web Dashboard:**
   ```bash
   python3 web.py
   ```
   Open your browser to [http://127.0.0.1:5000](http://127.0.0.1:5000) to view your live data.

### Production Scheduling
In a production environment, `web.py` should be run continuously as a background service (using Gunicorn, Heroku, AWS, etc.), while `app.py` should be configured as a **Cron Job** to run automatically once a week (e.g., every Friday at 5:00 PM) to snapshot that week's data.

```bash
# Example cron job running every Friday at 17:00
0 17 * * 5 cd /path/to/app && /usr/bin/python3 app.py
```

## Project Risks

This project reads reaction history from **public Slack channels only** and turns that activity into visible trend data. It does not have access to private channels or private messages, unless the bot is invited to that channel/DM. Only emoji reactions are stored.

Key risks to consider before using real workspace data:

* **Privacy and consent:** Employees may not expect emoji reactions to be aggregated or used as a proxy for sentiment. Before installing, you should communicate clearly what is collected, who can view it, and why.
* **Misinterpretation:** Emoji usage is noisy and context-dependent. They are indicators only, not hard data.
* **Access scope:** The Slack bot requires broad public-channel read access and is intended to automatically join channels to ensure the data collected is representative of most/all users.
* **Data exposure:** The SQLite database, downloaded custom emojis, and web dashboard can reveal internal activity patterns. Protect the app, token, database, and hosting environment accordingly.
* **Operational impact:** Crawling long history windows may hit Slack rate limits (though by default it is set to crawl only the past week), create visible "joined channel" messages, or surprise channel members.

---

## Project Structure
* `app.py` - Connects to Slack, downloads custom emojis, and counts reactions.
* `web.py` - Flask web server that reads the database and calculates trends.
* `generate_synthetic_data.py` - Populates the DB with mock history for testing.
* `emoji_tracker.db` - SQLite database (auto-generated).
* `templates/index.html` - The frontend UI.
* `static/custom_emojis/` - Local storage for downloaded Slack emojis.
