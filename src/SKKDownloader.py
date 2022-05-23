from datetime import timedelta
import logging
from multiprocessing import Lock, Semaphore
import os
import queue
from random import randint
from re import L
import sys
import threading
import time
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
from HashTable import HashTable
from HashTable import KVPair
"""
Redesign of ImageOpener without the use of Selenium and HandyImage
"""

# Threading Variables #####################################################
tname = threading.local()   # TLV for thread name
# Download task queue, Contains tuples in the structure: (func(),(args1,args2,...))
download_queue = queue.Queue(-1)
downloadables = Semaphore(0)     # Avalible downloadable resource device
kill = False    # Kill switch for downThreads
POST_PREFIX = 'https://chan.sankakucomplex.com/'
DATA_PREFIX = 'https:'
LOG_PATH = r'c:/Users/chenj/Downloads/SKK-Downloader-v2/src/logs/'
BLACK_PATH =  r'c:/Users/chenj/Downloads/SKK-Downloader-v2/src/logs/'
fcount = 0  # Used to count and rename content
fcount_mutex = Lock()   # Mutex for fcount
failed = 0
failed_mutex = Lock()
headers = {
    'User-agent': 'Mozilla/5.0 (Windows NT 5.1; rv:43.0) Gecko/20100101 Firefox/43.0'}


class Error(Exception):
    """Base class for other exceptions"""
    pass


class UnknownURLTypeException(Error):
    """Raised when url type cannot be determined"""
    pass


class downThread(threading.Thread):
    """
    Fully generic threadpool where tasks of any kind is stored and retrieved in task_queue,
    threads are daemon threads and can be killed using kill variable. 
    """
    __id: int

    def __init__(self, id: int) -> None:
        """
        Initializes thread with a thread name
        Param: 
        id: thread identifier
        """
        self.__id = id
        super(downThread, self).__init__(daemon=True)

    def run(self) -> None:
        """
        Worker thread job. Blocks until a task is avalable via downloadables
        and retreives the task from download_queue
        """
        tname.name = "Thread #" + str(self.__id)
        while True:
            # Wait until download is available
            downloadables.acquire()

            # Check kill signal
            if kill:
                return

            # Pop queue and download it
            todo = download_queue.get()
            logging.debug(tname.name + " Processing: " + str(todo))
            todo[0](*todo[1])
            download_queue.task_done()


class SKK():
    __url: str           # URL to Download
    __lastAddedID: str   # Last added postID
    __cookie: dict        # Sankaku Cookie
    __download_path: str  # Where to save images to
    __chunksz: int       # Download chunk size
    __tcount: int        # Number of threads
    __wait_time: int     # Time to wait
    __logn: str          # Name of log file
    __blacklist: HashTable | None    # Postids of blacklist posts
    __blackn: str        # Name of text file to put saved post id items in
    # Minimum number of bytes a file must download, if a lower download count is detected, it is added to the back of the queue
    __max_retries:int # Maximum number of times a download must take to complete
    __logn_mutex = Lock()
    __blackn_mutex = Lock()

    def __init__(self, tcount: int | None, chunksz: int | None, wait_time: int | None, blacklist: str | None,  max_retries: int|None, cookie: dict, download_path: str) -> None:
        """
        Sets up sankaku account info needed and download path

        Param:
            tcount: (optional) Number of threads (default is 1 which avoids timeouts, if a timeout error persists, lower the number of threads)
            chunksz: (optional) Download chunk sz (deafult is 64M)
            wait_time: (optional) Number of time to wait between downloads (default is 7 seconds, increase if timeout error persists)
            blacklist: (optional) File containing a blacklist of postids organized as post ids and new lines
            max_retries: (optional) Maximum cycles a download can take until becoming invalid (default is 100)
            cookie: Sankaku account cookie
            download_path: Where to save files at
        """
        # Cookie and download path
        assert(cookie != None)
        assert(download_path != None)
        self.__cookie = cookie
        self.__download_path = download_path

        # Threshold
        if max_retries and max_retries >= 1:
            self.__max_retries = max_retries
        else:
           self.__max_retries = 100

        # Blacklist
        if(blacklist):
            with open(blacklist, 'r') as fd:
                self.__blacklist = HashTable(10)
                lines = fd.readlines()

                for line in lines:
                    s = line.strip()
                    if len(s) > 0:
                        self.__blacklist.hashtable_add(KVPair[str, str](s, s))
        else:
            self.__blacklist = None

        # Misc
        self.__logn = LOG_PATH + "link - " + \
            str(int(time.monotonic())) + ".txt"
        tname.name = "main"
        self.__blackn = BLACK_PATH + "Blacklist - " + \
            str(int(time.monotonic())) + ".txt"

        # Tcount
        if tcount and tcount > 0:
            self.__tcount = tcount
        else:
            self.__tcount = 1

        # Chunksz
        if chunksz and chunksz > 0 and chunksz <= 12:
            self.__chunksz = chunksz
        else:
            self.__chunksz = 1024 * 1024 * 64

        # Wait time
        if wait_time and wait_time > 0:
            self.__wait_time = wait_time
        else:
            self.__wait_time = 7

    def set_url(self, url: str | None) -> None:
        """
        Sets download url, if url is None or incorrect, ask user for the url.

        Param:
            url: sankaku url to download from  
        """
        while not url or "chan.sankakucomplex.com" not in url:
            url = input("URL to download from> ")

        self.__url = url

    def run(self, segmented: bool, initial_skips: int):
        """
        KMP runner

        Param:
            initial_skips: number of images to skip in first page processing
            segmented: True to download in parts, false to download immediately.
        """
        if segmented:
            threads = self.__create_threads(self.__tcount)
            self.__process_container_in_segments(initial_skips)
        else:
            threads = self.__process_container(initial_skips)
            threads = self.__create_threads(self.__tcount)

        # Close threads
        download_queue.join()
        self.__kill_threads(threads)
        logging.info("Files downloaded: " + str(fcount))
        logging.info("Files failed: " + str(failed) +
                     " stored in " + self.__logn)

    def run_post_links(self, lname: str):
        """
        Downloads all post from a file containing links

        Param: 
            lname: file containing sankaku post links
        """
        threads = self.__create_threads(self.__tcount)
        with open(lname, 'r') as fd:
            line = fd.readline().strip()

            if(len(line) > 0):
                download_queue.put((self.__process_content, (line,)))
                downloadables.release()

        # Close threads
        download_queue.join()
        self.__kill_threads(threads)
        logging.info("Files downloaded: " + str(fcount))
        logging.info("Files failed: " + str(failed) +
                     " stored in " + self.__logn)

    def __create_threads(self, count: int) -> list:
        """
        Creates count number of downThreads and starts it

        Param:
            count: how many threads to create
        Return: Threads
        """
        threads = []
        # Spawn threads
        for i in range(0, count):
            threads.append(downThread(i))
            threads[i].start()
        return threads

    def __kill_threads(self, threads: list) -> None:
        """
        Kills all threads in threads. Threads are restarted and killed using a
        switch, deadlocked or infinitely running threads cannot be killed using
        this function.

        Param:
        threads: threads to kill
        """
        global kill
        kill = True

        for i in range(0, len(threads)):
            downloadables.release()

        for i in threads:
            i.join()

        kill = False
        logging.info(str(len(threads)) + " threads have been terminated")

    def __get_content_links(self, url: str, skips: int) -> int:
        """
        Grabs all content links from url and puts them into download_queue
        Updates __lastAddedID

        Param:
            skip: how many beginning links to skip, >= 0
            url: url to process
        Returns Number of items processed
        """
        # Get all image links from the page ###################
        reqs = requests.get(url, cookies=self.__cookie, headers=headers)
        acquired = 0
        # Keep trying until server responds
        while reqs.status_code >= 400:
            logging.error("HTTP Code " + str(reqs.status_code) + " at " +
                          url + ", retrying...")
            time.sleep(self.__wait_time * 2)
            reqs = requests.get(url,  cookies=self.__cookie, headers=headers)

        # Parse html for links
        soup = BeautifulSoup(reqs.text, 'html.parser')
        imgLinks = soup.find_all("span", class_="thumb")
        prev = None  # Last added item
        if(len(imgLinks) > skips):
            for link in imgLinks:
                # Get href in enclosed img class
                src = link.find("a").get('href')

                if skips > 0:
                    skips -= 1
                elif '/post/show/' in src:
                    prev = src
                    download_queue.put(
                        (self.__process_content, (POST_PREFIX + src,)))
                    acquired += 1
                    downloadables.release()

        if prev:
            self.__lastAddedID = self.__sankaku_postid_strip(prev)
        return acquired

    def __process_container(self, initial_skips) -> None:
        """
        Processes all content links within a tag, obtain all pages then download

        Pre: set_url has been called
        Post: All content links within a tag has been processed.
        """

        paritionedURL = self.__convert_link(self.__url)    # Paritioned link
        oldSz = 0
        # First link only one with 4 skips
        newSz = self.__get_content_links(
            paritionedURL[0] + paritionedURL[2], initial_skips)

        # Loop until queue is no longer growing
        while(oldSz != newSz):
            time.sleep(self.__wait_time + randint(0, self.__wait_time))
            # Get next page and process it
            oldSz = newSz
            newSz = self.__get_content_links(
                paritionedURL[0] + paritionedURL[1] + self.__lastAddedID + paritionedURL[2], 1)
            logging.info("Current Download QSize: " + str(newSz))

    def __process_container_in_segments(self, initial_skips: int) -> None:
        """
        Processes all content links within a tag, process and download 1 page at a time
        Pre: set_url has been called
        Post: All content links within a tag has been processed.
        """

        paritionedURL = self.__convert_link(self.__url)    # Paritioned link
        # First link only one with 4 skips
        items = self.__get_content_links(self.__url + '&page=1', initial_skips)
        logging.info("Parsed " + str(items) + " : " + self.__url + 'page=1')
        # Loop until queue is no longer growing
        while(items > 0):
            time.sleep(self.__wait_time + randint(0, self.__wait_time))
            # Get next page and process it
            items = self.__get_content_links(
                paritionedURL[0] + paritionedURL[1] + self.__lastAddedID + paritionedURL[2], 1)
            logging.info("Parsed " + str(items) + " : " +
                         paritionedURL[0] + paritionedURL[1] + self.__lastAddedID + paritionedURL[2])
            download_queue.join()

    def __sankaku_postid_strip(self, url: str) -> str:
        """
        Strips a sankaku url and returns the post id referred to by the url

        Param:
            url: sankaku post url to get postid from
        """
        tokens = url.rpartition('/')
        return tokens[2]

    def __convert_link(self, url: str) -> tuple[str]:
        """
        Converts Sankaku link into a page link and returns its partition
        For example:
            https://chan.sankakucomplex.com/?tags=persona

            Partition
            [0] -> https://chan.sankakucomplex.com/
            [1] -> ?next=
            [2] -> &tags=persona&page=1

        Param: 
            url: Sankaku URL to partition, cannot contain &page=, or ?next already
        Return:
            3 part tuple described above
        """
        partition = url.rpartition('?')
        return (partition[0], '?next=', '&' + partition[2] + '&page=1')

    def __get_content_src(self, url: str):
        """
        Grabs src of content, builds src into a valid https url

        Param: sankaku post link
        Raise: UnknownURLTypeException if content not found
        """

        # Get HTML
        reqs = requests.get(url, cookies=self.__cookie, headers=headers)

        # Keep trying until server responds
        while reqs.status_code >= 400:
            logging.error("HTTP Code " + str(reqs.status_code) + " at " +
                          url + ", retrying...")
            time.sleep(self.__wait_time * 2)
            reqs = requests.get(url, headers=headers)

        # Check if is video
        soup = BeautifulSoup(reqs.text, 'html.parser')
        imgLinks = soup.find("video", {"id": "image"})

        if imgLinks:
            return DATA_PREFIX + imgLinks.get('src')

        # Check if is flash
        imgLinks = soup.find("embed")

        if imgLinks:
            return DATA_PREFIX + imgLinks.get('src')

        # Check if is image
        imgLinks = soup.find("a", class_="sample")

        if imgLinks:
            return DATA_PREFIX + imgLinks.get('href')

        # Check if is gif
        imgLinks = soup.find("a", {"id": "image-link"})
        if(imgLinks):
            return DATA_PREFIX + imgLinks.find("img").get('src')

        raise UnknownURLTypeException

    def __guess_ext_type(self, fname: str) -> str:
        """
        Given a file name, determine file type

        Params:
            fname: file name
        Return: file extension (".png", ".webm",...), None if cannot be determined
        """
        if(".gif" in fname):
            return ".gif"
        elif(".jpg" in fname):
            return ".jpg"
        elif(".png" in fname):
            return ".png"
        elif("jpeg" in fname):
            return ".jpeg"
        elif(".mp4" in fname):
            return ".mp4"
        elif(".swf" in fname):
            return ".swf"
        elif(".webp" in fname):
            return ".webp"
        elif(".webm" in fname):
            return".webm"
        elif(".mov" in fname):
            return ".mov"
        return None

    def __process_content(self, url: str):
        """
        Downloads either video, flash, or image content at url

        Param:
            url: Sankaku post url to download content from
        """
        global failed
        global fcount
        # Check if the file is on the blacklist ###########################
        postid = self.__sankaku_postid_strip(url)
        if self.__blacklist and self.__blacklist.hashtable_exist_by_key(postid) != -1:
            logging.debug("File on blacklist already " + postid)
            self.__write_to_file(
                fname=self.__blackn, line=postid + '\n', mutex=self.__blackn_mutex, quiet=True)
            return

        # Get src on page ##################################################
        try:
            src = self.__get_content_src(url)
        except UnknownURLTypeException:
            logging.fatal("Unknown URL given, url:" + url)
            self.__write_to_file(fname=self.__logn, line="BAD URL:" +
                                 url + "\n", quiet=False, mutex=self.__logn_mutex)
            return
        # Download it
        # Get file size ######################################################
        r = None
        while not r:
            try:
                # Get download size
                logging.debug("Getting head of " + src)
                r = requests.get(src, cookies=self.__cookie,
                                 headers=headers, stream=True)
                if r.status_code >= 400:
                    logging.error(
                        "Encountered server error, writing to log " + url)
                    self.__write_to_file(
                        fname=self.__logn, line=url + "\n", quiet=False, mutex=self.__logn_mutex)
                    failed_mutex.acquire()
                    failed += 1
                    failed_mutex.release()
                    return
            except(requests.exceptions.ConnectTimeout):
                logging.debug("Connection request unanswered, retrying")
        fullsize = r.headers.get('Content-Length')

        # Get Filename ######################################################
        fname = self.__download_path + postid + self.__guess_ext_type(src)

        # Download the file in chunks #######################################
        downloaded = 0
        mode = 'wb'
        if not os.path.exists(fname) or os.stat(fname).st_size != int(fullsize):
            done = False
            cycles = 0
            while(not done):
                try:
                    # Download the file
                    with open(fname, mode) as fd, tqdm(
                            desc=fname,
                            total=int(fullsize),
                            unit='iB',
                            unit_scale=True,
                            leave=False,
                            bar_format=" (" + str(download_queue.qsize()) + ")->" +
                        fname + '[{bar}{r_bar}]',
                            unit_divisor=int(self.__chunksz)) as bar:
                        for chunk in r.iter_content(chunk_size=self.__chunksz):
                            sz = fd.write(chunk)
                            bar.update(sz)
                            downloaded += sz
                            
                            # Check max cycles, if detected, register failure and delete file
                            cycles += 1
                            if(cycles == self.__max_retries):
                                logging.info("Max download cycles reached, download rejected: " + url)
                                bar.close()
                                r.close()
                                self.__write_to_file(
                                fname=self.__logn, line=src + "\n", quiet=False, mutex=self.__logn_mutex)
                                failed_mutex.acquire()
                                failed += 1
                                failed_mutex.release()
                                return

                        time.sleep(1)
                        bar.clear()
                        r.close()

                    # Verify file size is large enough
                    if(os.stat(fname).st_size == int(fullsize)):
                        done = True

                        # Increment count
                        fcount_mutex.acquire()
                        fcount += 1
                        fcount_mutex.release()

                        # Write to blacklist
                        if(self.__blackn):
                            self.__write_to_file(
                                fname=self.__blackn, line=postid + '\n', mutex=self.__blackn_mutex, quiet=True)
                    else:
                        # Check max cycles, if detected, register failure and delete file
                        cycles += 1
                        if(cycles == self.__max_retries):
                            logging.info("Max download cycles reached, download rejected: " + url)
                            self.__write_to_file(
                            fname=self.__logn, line=url + "\n", quiet=False, mutex=self.__logn_mutex)
                            failed_mutex.acquire()
                            failed += 1
                            failed_mutex.release()
                            return
                        logging.debug("Incomplete download, will restart download (" +
                                      src + ") Dcount=" + str(cycles) + "-> " + str(os.stat(fname).st_size) + " / " + fullsize)
                        header = {'User-agent': 'Mozilla/5.0 (Windows NT 5.1; rv:43.0) Gecko/20100101 Firefox/43.0',
                                  'Range': 'bytes=' + str(downloaded) + '-' + fullsize}
                        mode = 'ab'
                        r = requests.get(
                            src, cookies=self.__cookie, headers=header, stream=True)
                        time.sleep(self.__wait_time)
                except requests.exceptions.ChunkedEncodingError:
                    logging.debug(
                        "Chunked encoding error has occured, server has likely disconnected, download has restarted")
                    time.sleep(self.__wait_time * 2)
                    r = requests.get(src, cookies=self.__cookie,
                                     headers=headers, stream=True)
        else:

            logging.debug("Skipping duplicate file: " + fname)
            # Write to blacklist
            if self.__blackn:
                self.__write_to_file(
                    fname=self.__blackn, line=postid + '\n', mutex=self.__blackn_mutex, quiet=True)

        # Sleep
        time.sleep(self.__wait_time + randint(0, self.__wait_time))

    def get_url(self):
        """
        Returns current url

        Return: Current url
        """
        return self.__url

    def __write_to_file(self, fname: str, line: str, mutex, quiet: bool) -> None:
        """
        Appends to a file

        Param:
            fname: file to write to, absolute path 
            line: line to append to file
            mutex: (Optional) mutex lock associated with the file
            quiet: Report finding or do not
        """
        if mutex:
            mutex.acquire()

        if not os.path.exists(fname):
            open(fname, 'a').close()
        with open(fname, "a") as myfile:
            myfile.write(line)

        if not quiet:
            logging.info("Wrote \"" + line + "\" in \"" + fname)

        if mutex:
            mutex.release()


def help() -> None:
    """
    Displays help information on invocating this program
    """
    logging.info(
        "Switches: Can be combined in any order!")
    logging.info(
        "Note that default settings correlate to settings that worked in internal testing")
    logging.info(
        "-j <textfile.txt> : REQUIRED - Sankaku cookie")
    logging.info(
        "-f <.txt> : Downloads posts within text file")
    logging.info(
        "-d <path> : REQUIRED - Set download path for single instance, must use '/'")
    logging.info(
        "-c <#> : Adjust download chunk size in bytes (Default is 64M)")
    logging.info(
        "-w <#> : Adjust download wait time in seconds (Default is 0 seconds)")
    logging.info(
        "-db : Turn on debug output")
    logging.info("-dbv : Turn on debug output and write output to file")
    logging.info("-h : Help")
    logging.info("-u <url> : Set download url")
    logging.info("-t <#> : Change download thread count (default is 1)")


def main() -> None:
    """
    Program runner
    """
    logging.basicConfig(level=logging.DEBUG)
    start_time = time.monotonic()
    folder = False
    tcount = -1
    chunksz = -1
    cookie = None
    url = None
    w = None
    posts = None
    debug = False
    debugV = False
    if len(sys.argv) > 1:
        pointer = 1
        while(len(sys.argv) > pointer):
            if sys.argv[pointer] == '-j':
                with open(sys.argv[pointer + 1], 'r') as fd:
                    cookie = {'cookie': fd.read()}
                pointer += 2
            elif sys.argv[pointer] == '-d' and len(sys.argv) >= pointer:
                folder = sys.argv[pointer + 1]
                pointer += 2
                logging.info("FOLDER -> " + folder)
            elif sys.argv[pointer] == '-db':
                debug = True
                pointer += 1
                logging.info("Debug mode turned on")
            elif sys.argv[pointer] == '-f' and len(sys.argv) >= pointer:
                posts = sys.argv[pointer + 1]
                pointer += 2
                logging.info("URLTXT -> " + posts)
            elif sys.argv[pointer] == '-u' and len(sys.argv) >= pointer:
                url = sys.argv[pointer + 1]
                pointer += 2
                logging.info("URL -> " + url)
            elif sys.argv[pointer] == '-t' and len(sys.argv) >= pointer:
                tcount = int(sys.argv[pointer + 1])
                pointer += 2
                logging.info("THREAD_COUNT -> " + str(tcount))
            elif sys.argv[pointer] == '-c' and len(sys.argv) >= pointer:
                chunksz = int(sys.argv[pointer + 1])
                pointer += 2
                logging.info("CHUNKSZ -> " + str(chunksz))
            elif sys.argv[pointer] == '-w' and len(sys.argv) >= pointer:
                w = int(sys.argv[pointer + 1])
                pointer += 2
                logging.info("WAIT TIME -> " + str(w))

            else:
                pointer = len(sys.argv)

    if folder:
        downloader = SKK(tcount=tcount, chunksz=chunksz, wait_time=w, cookie=cookie, download_path=folder,
                         blacklist='C:/Users/chenj/Downloads/SKK-Downloader-v2/src/logs/Blacklist - 396644.txt', max_retries=None)

        if posts:
            downloader.run_post_links(posts)
        else:
            downloader.set_url(url)
            downloader.run(True, 0)
    else:
        help()
    end_time = time.monotonic()
    logging.info(timedelta(seconds=end_time - start_time))


if __name__ == "__main__":
    main()
