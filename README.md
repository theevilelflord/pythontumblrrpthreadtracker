# pythonrpthreadtracker
 Generate a list of all threads, choose which are rp threads, and track locally.
 
 ## Getting Started:
 This script is meant to be run through command line terminal, though in theory you could also run it through Jupyter Notebook or another 
 Pythone environment.
 1. If you don't have it already, you will need python3. 
 2. Generate your API key. Go to https://www.tumblr.com/oauth/apps and register a new application.
 3. Open 'settings.py', and paste your API key (consumer key from the application you just registered) on line 15 where it says 'XXXXXX_API_KEY_HERE_XXXXXX', between the single quotation marks. Make sure to keep the single quotations, as they denote that the variable api_key is of type string.
 4. Run 'settings.py'. Open teminal (for mac or linux) or powershell (for windows), and navigate to the folder pythonthreadtracker is in. Type in 'python3 settings.py', and hit ENTER. If this is the first time you are running the script, it will generate a folder named 'settings'. It will generate a .json file with settings and metadata for each blog you are tracking.The script will ask you to enter five values:
    a. the blog name: if the blog is under the Tumblr domain, omit .tumblr.com. For example, if your blog is the9muses.tumblr.com, then you would enter 'the9muses'.
    b. tracked tag: if you use a tag to denote in character threads, add it here. If not, press enter to skip.
    c. auto-archive: this is mostly to make the initial run go a little smoother and filter out threads you don't want to track. This value should be an integer representing the number of days of inactivity you want to allow before automatically archiving a thread. Press ENTER without entering a value if you do not wish to use this functionality.
    d. ask-archive: this is meant mostly for general maintenance after the initial run, and should be an integer smaller than the one entered for auto-archive, but otherwise funtions the same. Press ENTER without entering a value if you do not wish to use this function.
    e. generate another: if you would like to track another blog, enter y, and it will loop through the prompts again. If you are done with the settings, enter n to quit the script.
 5. run pythonthreadtracker script. type 'python3 pythonthreadtracker.py', and press ENTER to run the script. This will take a while to complete the first time it is run, especially if you have an older blog or thousands of posts. The script will generate three files, all threads, and all RP threads, and rp threads that are not archived. 
 6. If you do not have a tag to denote rp threads, you can edit the csv either in a plaintext editor or spreadsheet program of your choosing, and enter 'true' for the threads you want to track under the column 'rp thread' You will then need to run the script that loads all_threads and then sorts out the rp thread entries.
    a. What may be an easier alternative is to add a tag to track using the bulk tag funtion on tumblr's archive. Feedback on this funtionality would be much appreciated.
 7. That should be it! now open the csv labeled RP threads, and they should show all rp threads
 
 ##FLAGS:
 --skip-ask-archive: for automation, purposes, does not archive any threads that have not had activity for the amount of time between the ask-archive date and auto-archive date.
 --auto-archive for automation purposes, automatically archives threads that fall in the ask-archive catigory.
