import logging
import threading
import queue
"""
Simple task sharing threadpool. Handles fully generic tasks of any kind

Author: Jeff Chen
Last modified: 5/23/2022
"""
tname = threading.local()   # TLV for thread name

class Kill_Queue():
    """
    Queue with a built in kill switch with sem == # of available items,
    to be used in multithreading
    """
    __queue:queue.Queue 
    __kill:bool     # Kill switch for downThreads
    __tasks:any     # Avalible downloadable resource device

    def __init__(self) -> None:
        """
        Create queue and set kill to false
        """
        self.__queue = queue.Queue(-1)
        self.__kill = False
        self.__tasks = threading.Semaphore(0)
    
    def kill(self) -> None:
        """
        Turns kill switch on
        """
        self.__kill = True
    
    def revive(self) -> None:
        """
        Turn kill switch off
        """
        self.__kill = False
    
    def status(self) -> bool:
        """
        Reports if the queue is dead or alive

        Return: True if dead, False if alive
        """
        return self.__kill
    
    def enqueue(self, task:any) -> None:
        """
        Put an item in the queue
        """
        self.__queue.put(task)
        self.__tasks.release()
    
    def acquire_resource(self) -> None:
        """
        Decrement semaphore keeping track of queue items
        """
        self.__tasks.acquire()

    def release_resource(self) -> None:
        """
        Increment semaphore keeping track of queue items.
        Does not need to be called after enqueue as it 
        increments the semaphore automatically
        """
        self.__tasks.release()

    def dequeue(self) -> any:
        """
        Removes an item

        Pre: acquire_resource was called first
        Return item in front of the queue
        """
        return self.__queue.get()
    
    def task_done(self) -> None:
        """
        Indicates queue task was completed

        Pre: dequeue was called, thread task was completed
        """
        self.__queue.task_done()
    
    def join_queue(self) -> None:
        """
        Blocks until all task queue items have been processed
        """
        self.__queue.join()

    def get_qsize(self) -> int:
        """
        Get queue size (unreliable)

        Return: queue size
        """
        return self.__queue.qsize()
    


    



class ThreadPool():
    # Download task queue, Contains tuples in the structure: (func(),(args1,args2,...))
    __task_queue:Kill_Queue
    __threads:list  # List of threads in the threadpool

    def __init__(self, tcount:int) -> None:
        """
        Initializes a threadpool and starts the threads

        Param:
            tcount: Number of threads for the threadpool
        """
        self.__task_queue = Kill_Queue()
        self.__threads = self.__create_threads(tcount)
        tname.name = "main"
    
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
            threads.append(ThreadPool.TaskThread(i, self.__task_queue))
            threads[i].start()
        logging.debug(str(count) + " threads have been started")
        return threads
    
    def kill_threads(self) -> None:
        """
        Kills all threads in threadpool. Threads are restarted and killed using a
        switch, deadlocked or infinitely running threads cannot be killed using
        this function.
        """
        self.__task_queue.kill()

        for i in range(0, len(self.__threads)):
            self.__task_queue.release_resource()

        for i in self.__threads:
            i.join()

        self.__task_queue.revive()
        logging.debug(str(len(self.__threads)) + " threads have been terminated")

    def enqueue(self, task:tuple) -> None:
        """
        Put an item in task queue

        Param:
            task: tuple in the structure (func(),(args1,args2,...))
        """
        logging.debug("Enqueued into task queue: " + str(task))
        self.__task_queue.enqueue(task)
    
    def join_queue(self) -> None:
        """
        Blocks until all task queue items have been processed
        """
        logging.debug("Blocking until all tasks are complete")
        self.__task_queue.join_queue()

    def get_qsize(self) -> int:
        """
        Get queue size (unreliable)

        Return: task queue size
        """
        return self.__task_queue.get_qsize()


    class TaskThread(threading.Thread):
        """
        Fully generic threadpool where tasks of any kind is stored and retrieved in task_queue,
        threads are daemon threads and can be killed using kill variable. 
        """
        __id: int
        __task_queue:Kill_Queue

        def __init__(self, id: int, task_queue:Kill_Queue) -> None:
            """
            Initializes thread with a thread name
            Param: 
            id: thread identifier
            task_queue: Queue to get tasks from
            tasks: Semaphore assoaciated with task queue
            """
            self.__id = id
            self.__task_queue = task_queue
            super(ThreadPool.TaskThread, self).__init__(daemon=True)

        def run(self) -> None:
            """
            Worker thread job. Blocks until a task is avalable via downloadables
            and retreives the task from download_queue
            """
            tname.name = "Thread #" + str(self.__id)
            while True:
                # Wait until download is available
                self.__task_queue.acquire_resource()

                # Check kill signal
                if self.__task_queue.status():
                    logging.debug(tname.name + " has terminated")
                    return

                # Pop queue and download it
                todo = self.__task_queue.dequeue()
                logging.debug(tname.name + " Processing: " + str(todo))
                todo[0](*todo[1])
                self.__task_queue.task_done()