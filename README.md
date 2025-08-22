# pythonrpthreadtracker
 Get list of all threads, choose which are rp threads, and track locally.
 ## Getting Started:
 
 ### Settings:
  1. you will need to get a Tumblr API key. The easiest way to do  this is with a git page, though you can use any website you like.
  2. Once you have your API key, open the settings script and paste the API key where it says API KEY HERE, keeping the single quotes. 
  3. In the 'blog name' field, type in the name of the blog you want to track. If it is under the Tumblr domain, you can omit '.tumblr.com'.
  3. Leave the previous total as zero, This is the total number of posts for the blog the last time the trakcer script was run.
  4. If you have a tag you use for RP threads, you can add it here and it will automatically add those threads to the RP threads CSV. Else, leave the field blank.
  5. Run the settings script. If there is not a settings folder, it will be created, with a settings file for your blog. Run for each additional blog you wish to track. The only field that you need to change for each additional blog settings file generated is the blog name, and the optional tracked thread. If wish to completely rewrite the tracked threads csv, either this script for the blog to reset previous total to zero, or open the .json in a text editor and reset to zero manually. 
 
 ### running the script:
 
  There are two ways to select which threads are rp threads (and more importantly, ones you wish to track. The first is to manually go through the list of threads, and change the value of rp thread to 'True'. The second method is to choose a tag that you add to your rp posts for the script to track. You can set this in the settings file under the 'rp tracked thread' entry.
