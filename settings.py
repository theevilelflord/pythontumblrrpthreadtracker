outdir = 'settings/'

# Check if folder exists, and create it if it doesn't
if not os.path.exists(outdir):
    os.makedirs(outdir)

while True:
    # Get user input for blog name and rp tag
    blog_name = input("Enter the blog name: ").strip()
    rp_tag = input("Enter the RP tag (leave blank if not applicable): ").strip()
    auto_archive = input("Enter the number of days of inactivity before automativally arhiving a thread (leave blank if not applicable): ").strip()
    ask_archive = input("Enter the number of days of inactivity before asking to arhive a thread (leave blank if not applicable): ").strip()

    settings = {
        'api key': 'XXXXXX_API_KEY_HERE_XXXXXX',  # Replace with your API key
        'blog name': blog_name, # blog you want to track
        'previous total': 0,  # Or the actual previous total if available
        'rp tag': rp_tag, # a tag you use for in character posts that you can use to automatically add a thread to track
        'auto archive': auto_archive, # automatically archive a thread after x days
        'ask to archive': ask_archive # have script ask if you want to archive after y days
    }

    # Save to file
    filename = os.path.join(outdir, blog_name + '_settings.json')
    with open(filename, "w") as outfile:
        json.dump(settings, outfile, indent=4)

    print(f"Settings saved to {filename}")

    # Ask user if they want to generate another
    again = input("Do you want to generate another settings file? (y/n): ").strip().lower()
    if again != 'y':
        print("Exiting.")
        break


