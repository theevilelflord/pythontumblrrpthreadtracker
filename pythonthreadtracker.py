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

    # Initialize Tumblr client
    client = pytumblr.TumblrRestClient(settings['api key'])
    blog = settings['blog name']
    trackedtag = settings['rp tag'].strip()
    tagexists = trackedtag != ''

    print(f"\nProcessing blog: {blog}")
    print(f"Tracked tag: {trackedtag if tagexists else 'None'}")

    # Get current post count and change since last run
    try:
        r = client.posts(blog)
    except Exception as e:
        print(f"Error fetching posts for {blog}: {e}")
        continue

    total = r['total_posts']
    since_last = total - settings['previous total']
    print(f"Total posts: {total}")
    print("-" * 40)

    if since_last == 0:
        print(f"No new posts since last check for blog {blog}.")
        continue

    # Load or initialize post log
    if settings['previous total'] == 0:
        posts_df = pd.DataFrame(columns=['postURL', 'id', 'rootID', 'rootURL','rpthread'])
    else:
        try:
            posts_df = pd.read_csv(f"{blog}_all_posts.csv")
        except FileNotFoundError:
            posts_df = pd.DataFrame(columns=['postURL', 'id', 'rootID', 'rootURL','rpthread'])

    # Fetch new posts
    n = 0
    l = 50
    new_rows = []

    while n < since_last:
        try:
            r2 = client.posts(blog, limit=l, offset=n, reblog_info=True)
            posts = r2.get('posts', [])
        except Exception as e:
            print(f"Failed to fetch posts at offset {n}: {e}")
            break

        for i, b in enumerate(posts):
            if (n + i) >= total:
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

            print(f"{n+i}: {post_url} | RP Thread: {rpthread}")
            print(f"Post ID: {post_id} | RootID: {root_id}")

            new_rows.append([post_url, post_id, root_id, root_url, rpthread])

        n += l

    # Add new rows and save all posts
    new_posts_df = pd.DataFrame(new_rows, columns=['postURL', 'id', 'rootID', 'rootURL','rpthread'])
    posts_df = pd.concat([posts_df, new_posts_df], ignore_index=True)
    posts_df.to_csv(f"{blog}_all_posts.csv", index=False)

    threads = posts_df.drop_duplicates(subset='rootID')
    
    print("-" * 40)
    print(threads.head())

    threads.to_csv(f"{blog}_all_threads.csv", index=False)

    # Update settings with new post total
    settings['previous total'] = total
    with open(os.path.join('settings', f"{blog}_settings.json"), 'w') as g:
        json.dump(settings, g, indent=4)
    
        
    # Filter rows where 'rpthread' is True
    rp_threads = threads[threads['rpthread'] == True].copy()

    # Add new columns
    rp_threads['archive'] = ''
    rp_threads['last poster'] = ''
    rp_threads['time'] = ''
    rp_threads['reply URL'] = ''
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
        print(f"\n✅ Updated CSV saved to: {output_csv}")

    # Usage
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
    print(f"\n✅ Archive flags updated in: {blog}_rp_threads.csv")


