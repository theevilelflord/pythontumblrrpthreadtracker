import os, pytumblr, pandas as pd, json, requests, time
from datetime import datetime

directory = 'settings'

for filename in os.listdir(directory):
    f = os.path.join(directory, filename)

    with open(f) as json_file:
        try:
            settings = json.load(json_file)
        except json.JSONDecodeError:
            print(f"Invalid JSON in {filename}, skipping.")
            continue
    # Load the CSV file
    df = pd.read_csv(f"{blog}_all_threads.csv")

    # Filter rows where 'rpthread' is True
    rp_threads = df[df['rpthread'] == True].copy()

    try:
        rp_threads = pd.read_csv(f"{blog}_rp_threads.csv")
    except FileNotFoundError:
        rp_threads = threads
        # Add new columns
        rp_threads['archive'] = 'false'
        rp_threads['last_poster'] = ''
        rp_threads['timestamp'] = ''
        rp_threads['latest_reply_URL']
        # Save to new CSV file (or overwrite the original)
        rp_threads.to_csv(f"{blog}_rp_threads.csv", index=False)
     def get_post_notes(blog_name, post_id, api_key):
            url = f"https://api.tumblr.com/v2/blog/{blog_name}/notes"
            params = {
                "api_key": api_key,
                "id": post_id,
                "mode": "raw",
                "notes_info": True
            }

            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                notes = data.get("response", {}).get("notes", [])
                for note in notes:
                    if note.get("type") == "reblog":
                        blog_name = note.get("blog_name")
                        timestamp = note.get("timestamp")
                        reply_id = note.get("post_id")
                        return blog_name, timestamp, reply_id
                return None, None, None  # Fix: return 3 values consistently
            else:
                print(f"Error fetching notes for post {post_id}: {response.status_code}")
                return None, None, None

        def process_csv(input_csv, output_csv, blog_name_base, api_key):
            df = pd.read_csv(input_csv)

            if "id" not in df.columns:
                raise ValueError("CSV must contain a 'id' column")

            for i, row in df.iterrows():
                post_id = row["id"]
                print(f"Processing post ID: {post_id}")
                last_poster, timestamp, reply_id = get_post_notes(blog_name_base, post_id, api_key)

                if last_poster and timestamp:
                    df.at[i, "last poster"] = last_poster
                    df.at[i, "reply URL"] = f"https://{last_poster}.tumblr.com/post/{reply_id}"
                    df.at[i, "time"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

                time.sleep(1)  # Respect Tumblr API rate limits

            df.to_csv(output_csv, index=False)
            print(f"Updated CSV saved to: {output_csv}")

        API_KEY = settings['api key']
        INPUT_CSV = f"{blog}_rp_threads.csv"
        OUTPUT_CSV = f"{blog}_rp_threads.csv"
        BLOG_NAME_BASE = settings['blog name']

        process_csv(INPUT_CSV, OUTPUT_CSV, BLOG_NAME_BASE, API_KEY)


        auto_days = int(settings.get('auto archive', 9999))
        ask_days = int(settings.get('ask archive', 9999))
        today = datetime.today()

        def apply_archive(row):
            ts_raw = row.get('time', '')

            # Explicit string conversion and NaN check
            if pd.isna(ts_raw):
                return ''

            ts = str(ts_raw).strip()

            if not ts or ts.lower() == 'nan':
                return ''

            try:
                last_date = datetime.strptime(ts, '%Y-%m-%d')
            except Exception as e:
                print(f"Failed to parse timestamp '{ts}': {e}")
                return ''

            days_old = (today - last_date).days

            if days_old >= auto_days:
                return 'true'
            elif days_old >= ask_days:
                print(f"\nThread: {row.get('rootURL', 'Unknown URL')}")
                print(f"Last reply was {days_old} days ago.")
                ans = input("Do you want to archive this thread? (y/n): ").strip().lower()
                return 'true' if ans == 'y' else ''
            else:
                return ''
            
        rp_threads['archive'] = rp_threads.apply(apply_archive, axis=1)

        rp_threads.to_csv(f"{blog}_rp_threads.csv", index=False)
        print(f"Archive flags updated in: {blog}_rp_threads.csv")

