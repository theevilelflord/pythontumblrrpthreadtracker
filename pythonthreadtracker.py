import os, pytumblr, pandas as pd, json, requests, time
from datetime import datetime
import argparse

parser = argparse.ArgumentParser(description="Track RP threads with optional non-interactive archival modes")
group = parser.add_mutually_exclusive_group()
group.add_argument("--skip-ask-archive", action="store_true", help="Skip prompts and do not archive 'ask' threads")
group.add_argument("--archive-all", action="store_true", help="Skip prompts and auto-archive 'ask' threads")
args = parser.parse_args()


directory = 'settings'

for filename in os.listdir(directory):
    f = os.path.join(directory, filename)

    with open(f) as json_file:
        try:
            settings = json.load(json_file)
        except json.JSONDecodeError:
            print(f"Invalid JSON in {filename}, skipping.")
            continue

    # Initialize Tumblr client
    client = pytumblr.TumblrRestClient(settings['api key'])
    blog = settings['blog name']
    trackedtag = settings['rp tag'].strip()
    tagexists = trackedtag != ''

    print(f"\nProcessing blog: {blog}")
    print(f"Tracked tag: {trackedtag if tagexists else 'None'}")

    # Load last run timestamp (default to 0)
    last_run_timestamp = settings.get('last run', 0)
    print(f"Fetching posts since timestamp: {last_run_timestamp} ({time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_run_timestamp))})")

    # Load or initialize post log
    try:
        posts_df = pd.read_csv(f"{blog}_all_posts.csv")
    except FileNotFoundError:
        posts_df = pd.DataFrame(columns=['postURL', 'id', 'rootID', 'rootURL', 'rpthread'])

    # Fetch new posts since last run
    offset = 0
    limit = 50
    keep_fetching = True
    new_rows = []

    while keep_fetching:
        try:
            r2 = client.posts(blog, limit=limit, offset=offset, reblog_info=True)
            posts = r2.get('posts', [])
        except Exception as e:
            print(f"Failed to fetch posts at offset {offset}: {e}")
            break

        if not posts:
            break

        for b in posts:
            post_timestamp = b.get('timestamp', 0)
            if post_timestamp <= last_run_timestamp:
                keep_fetching = False
                break

            post_url = b.get('post_url')
            post_id = b.get('id_string')
            tags = b.get('tags', [])

            if 'reblogged_root_id' in b and b['reblogged_root_id']:
                root_id = b['reblogged_root_id']
                root_url = b['reblogged_root_url']
            else:
                root_id = b['id']
                root_url = b['post_url']

            rpthread = trackedtag in tags if tagexists else ''

            print(f"{offset}: {post_url} | RP Thread: {rpthread}")
            print(f"Post ID: {post_id} | RootID: {root_id} | Time: {post_timestamp}")

            new_rows.append([post_url, post_id, root_id, root_url, rpthread])

        offset += limit
        time.sleep(1)  # Respect API rate limits

    if not new_rows:
        print(f"No new posts since last check for blog {blog}.")
        continue

    # Add new rows and save all posts
    new_posts_df = pd.DataFrame(new_rows, columns=['postURL', 'id', 'rootID', 'rootURL', 'rpthread'])
    posts_df = pd.concat([posts_df, new_posts_df], ignore_index=True)
    # posts_df.to_csv(f"{blog}_all_posts.csv", index=False)

    # Drop duplicates from current batch
    threads = posts_df.drop_duplicates(subset='rootID').copy()

    # Load existing all_threads.csv if it exists
    all_threads_file = f"{blog}_all_threads.csv"
    if os.path.exists(all_threads_file):
        existing_threads = pd.read_csv(all_threads_file)
        threads = pd.concat([existing_threads, threads], ignore_index=True)
        threads = threads.drop_duplicates(subset='rootID', keep='last').copy()


    #threads.loc[:, 'id'] = threads['id'].astype(str)
    #threads.loc[:, 'rootID'] = threads['rootID'].astype(str)


    threads.to_csv(f"{blog}_all_threads.csv", index=False)

    print("-" * 40)
    print(threads.head())

    # Update settings with current timestamp
    settings['last run'] = int(time.time())
    with open(os.path.join('settings', f"{blog}_settings.json"), 'w') as g:
        json.dump(settings, g, indent=4)

    # Filter rows where 'rpthread' is True
    rp_threads = threads[threads['rpthread'] == True].copy()
    
    rp_threads = rp_threads.drop(columns=['rpthread'])

    rp_threads.loc[:, 'archive'] = 'false'
    rp_threads.loc[:, 'last poster'] = ''
    rp_threads.loc[:, 'time'] = ''
    rp_threads.loc[:, 'reply URL'] = ''
    rp_threads.loc[:, 'id'] = rp_threads['id']
    rp_threads.loc[:, 'rootID'] = rp_threads['rootID']
    if 'reply ID' not in rp_threads.columns:
        rp_threads.loc[:, 'reply ID'] = ''
    rp_threads.loc[:, 'reply ID'] = rp_threads['reply ID']

    rp_threads.to_csv(f"{blog}_rp_threads.csv", index=False)

    def get_post_notes(blog_name, post_id, api_key):
        notes_url = f"https://api.tumblr.com/v2/blog/{blog_name}/notes"
        notes_params = {
            "api_key": api_key,
            "id": post_id,
            "mode": "raw",
            "notes_info": True
        }

        response = requests.get(notes_url, params=notes_params)

        if response.status_code == 200:
            data = response.json()
            notes = data.get("response", {}).get("notes", [])
            for note in notes:
                if note.get("type") == "reblog":
                    last_poster = note.get("blog_name")
                    timestamp = note.get("timestamp")
                    reply_id = note.get("post_id")
                    return last_poster, timestamp, reply_id

            # Fallback
            print(f"No reblogs for post {post_id}, using original timestamp.")
            post_url = f"https://api.tumblr.com/v2/blog/{blog_name}/posts"
            post_params = {
                "api_key": api_key,
                "id": post_id,
                "notes_info": True
            }
            post_response = requests.get(post_url, params=post_params)

            if post_response.status_code == 200:
                post_data = post_response.json()
                posts = post_data.get("response", {}).get("posts", [])
                if posts:
                    post = posts[0]
                    timestamp = post.get("timestamp")
                    return blog_name, timestamp, post_id
                else:
                    print(f"No post found for ID {post_id}")
            else:
                print(f"Failed to fetch post data for fallback. Status: {post_response.status_code}")
        else:
            print(f"Error fetching notes for post {post_id}: {response.status_code}")

        return None, None, None

    def process_csv(input_csv, output_csv, blog_name_base, api_key):
        df = pd.read_csv(input_csv, dtype=str)

        if "id" not in df.columns:
            raise ValueError("CSV must contain an 'id' column")

        for i, row in df.iterrows():
            post_id = str(row["id"])
            print(f"Processing post ID: {post_id}")
            last_poster, timestamp, reply_id = get_post_notes(blog_name_base, post_id, api_key)

            if last_poster and timestamp:
                df.at[i, "last poster"] = str(last_poster)
                df.at[i, "reply ID"] = str(reply_id)
                df.at[i, "reply URL"] = f"https://{last_poster}.tumblr.com/post/{reply_id}"
                df.at[i, "time"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

            time.sleep(1)

        df.to_csv(output_csv, index=False)
        print(f"Updated CSV saved to: {output_csv}")

    API_KEY = settings['api key']
    INPUT_CSV = f"{blog}_rp_threads.csv"
    OUTPUT_CSV = f"{blog}_rp_threads.csv"
    BLOG_NAME_BASE = settings['blog name']

    process_csv(INPUT_CSV, OUTPUT_CSV, BLOG_NAME_BASE, API_KEY)
    
    rp_threads = rp_threads.sort_values(by='time', ascending=False)

    rp_threads = pd.read_csv(f"{blog}_rp_threads.csv")
    
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
             last_date = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"Failed to parse timestamp '{ts}': {e}")
            return ''

        days_old = (today - last_date).days

        if days_old >= auto_days:
            return 'true'
        elif days_old >= ask_days:
            if args.skip_ask_archive:
                return 'false'
            elif args.archive_all:
                return 'true'
            else:
                print(f"\nThread: {row.get('reply URL', 'Unknown URL')}")
                print(f"Last reply was {days_old} days ago.")
                ans = input("Do you want to archive this thread? (y/n): ").strip().lower()
                return 'true' if ans == 'y' else ''
        
    rp_threads['archive'] = rp_threads.apply(apply_archive, axis=1)

    rp_threads.to_csv(f"{blog}_rp_threads.csv", index=False)
    print(f"Archive flags updated in: {blog}_rp_threads.csv")
    
    tracked_threads = rp_threads[rp_threads['archive'] == 'false'].copy()
    
    tracked_threads = tracked_threads.drop(columns=['postURL', 'id', 'rootID', 'rootURL', 'archive', 'reply ID'])
    tracked_threads.to_csv(f"{blog}_tracked_threads.csv", index=False)


