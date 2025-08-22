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
    # posts_df.to_csv(f"{blog}_all_posts.csv", index=False)

    threads = posts_df.drop_duplicates(subset='rootID')
    
    print("-" * 40)
    print(threads.head())

    threads.to_csv(f"{blog}_all_threads.csv", index=False)

    # Update settings with new post total
    settings['previous total'] = total
    with open(os.path.join('settings', f"{blog}_settings.json"), 'w') as g:
        json.dump(settings, g, indent=4)
