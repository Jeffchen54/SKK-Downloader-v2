# SKK-Downloader-v2
This is the improved version of SKK Downloader described here here: https://github.com/Jeffchen54/SKK-Downloader

Currently, SKK Downloader is very early in development. It is only partially functional and a working version
will be published in releases when it is completed. 

SKK Downloader v2 is a simple web scraping based downloader offering the following features:
- Downloading entire tags without any limit (>2000 limit imposed by v1)
- Automatic retry for "Please slow down" messages (v1 had a less efficient approach)
- Blacklists 
- Duplicate file skip based on name and file size
- Multithreaded***
- Logging of all failed downloads**
- Cookie user authentication

*** Sankaku servers bottleneck downloads harshly, even viewing several posts normally is enough to bottleneck performance. 

** 403 Errors, unable to load, timeouts...

## Invocation: 
-j <textfile.txt> : REQUIRED - Sankaku cookie

-f <.txt> : Downloads posts within text file

-d <path> : REQUIRED - Set download path for single instance, must use '/'
  
-c <#> : Adjust download chunk size in bytes (Default is 64M)
  
-b <path> : Set path to blacklist file
  
-h : Help
  
-u <url> : Set download url
  
-t <#> : Change download thread count (default is 1)
  
  
## Example invocations:
**SKKDownloader.py -d "C:/Users/chenj/Downloads/SKK-Downloader-v2/src/img/" -j "C:/Users/chenj/Downloads/SKK-Downloader-v2/src/Cookie2.txt"**
- Bare minimum invocation. Set download path to img directory and set Cookie to cookie within Cookie2.txt

  
**SKKDownloader.py -d "C:/Users/chenj/Downloads/SKK-Downloader-v2/src/img/" -j "C:/Users/chenj/Downloads/SKK-Downloader-v2/src/Cookie2.txt" -u https://chan.sankakucomplex.com/?tags=xxxxxx**
- Same as first example but skip prompt asking for a url to download from
  
  
**SKKDownloader.py -d "C:/Users/chenj/Downloads/SKK-Downloader-v2/src/img/" -j "C:/Users/chenj/Downloads/SKK-Downloader-v2/src/Cookie2.txt" -f "C:/Users/chenj/Downloads/SKK-Downloader-v2/src/logs/link - 159641.txt"**
- Bare minimum invocation for downloading from text file "link - 159641.txt" 
  
  
**SKKDownloader.py -d "C:/Users/chenj/Downloads/SKK-Downloader-v2/src/img/" -j "C:/Users/chenj/Downloads/SKK-Downloader-v2/src/Cookie2.txt" -b "C:/Users/chenj/Downloads/SKK-Downloader-v2/src/logs/Blacklist - 159641.txt" -c 8192 -t 2**
- Loaded invocation that adds a blacklist, chunk size to 8192 bytes, and thread count to 2.

## Instructions
  1) Download all required dependencies
  2) Choose a program invocation that is described above. Please review supported link types and other switches underneath this section
  3) If a prompt for URL comes up, use a tag URL, posts can only be downloaded through a post file.
  4) Once downloads are completed, the program will report so and logs will be written to the logs folder.

## Supported URL types:
  https://chan.sankakucomplex.com/?tags=...
      Tag only for downloading all posts sharing a tag.
  
  https://chan.sankakucomplex.com/post/show/xxxxxx
      URL for downloading a post

## Input file structure

  ### Blacklist file (-b):
  File contents:
  "abcdefgh  
  ijklsads
  casdsadc
  ..."
  
  Blacklist file contains a column of post ids separated with new lines.
  
  ### Post link file  (-f):
  File contents:
  
  "https://chan.sankakucomplex.com//post/show/abcedfg
  
  https://chan.sankakucomplex.com//post/show/dcasdfs"
  ...
  
  Post link file contains a column of post links separated with new lines.
  
  ### Cookie file (-j):
  File contents:
  "blacklisted_tags=; theme=1; _pk_id.2.42fa=..."
  
  Cookie contents only. Extracting this cookie will be described further in this document.

## Logs:
  - Upon completion of all downloads, 2 logs will created in the home directory's log folder.
  - A Blacklist and a link file will be created. The Blacklist contains all successfully post ids and the link file contains all failed download urls. 
  - These file can be inputted using -f and -b switches.
  - Using a blacklist file is highly recommend, there is a substantial performance difference between skipping a file versus duplicate file checking.

  
## Special notices
  - Progress bar may seem to hang. This is either Sankaku streaming continuous data slowly or a slow connection. 

## Bugs:
- Download progress bar does not show file size correctly

## How to get Sankaku cookie?
1. Log into sankaku account
2. Visit a post
3. Go to inspect element, then network, there should be nothing displayed there
4. Refresh the tab, lots of documents and files should show up. Search for the document matching the current post id. 
5. In the Request Headers, there should be the field 'Cookie' followed by the value 'blacklisted_tags=...'. Copy only the value and copy all of it.
6. Paste the cookie into a text file and save it. The cookie is now ready to be used with the -j switch. 
  
Please note that your cookie is essentially a verified ticket. Do not share this with anyone besides yourself! Cookies are needed because certain content and tags are locked behind an account.
  
## Changelog:
- Nothing for now
  
  
