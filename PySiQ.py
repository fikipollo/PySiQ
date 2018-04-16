"""
PySiQ, a Python Simple Queue system

PySiQ is a task queue or task queue implemented for Python applications.
The main objectives of task queues are to avoid running resource-intensive tasks immediately and wait for them to complete.
Instead, tasks are scheduled by adding them to a queue, where they will wait until eventually a Worker, i.e. a special
process running in separate thread, takes them out of the queue and execute the task. This concept is especially
necessary for web applications where it is not possible to handle a heavy task during a short HTTP request window.

VERSION 0.3 APRIL 2018
"""

#TODO: TIMEOUT
#TODO: AUTO REMOVE JOBS
#TODO: ADD DOCUMENTATION TO SCRIPT

import logging
from threading import RLock as threading_lock, Thread, Timer
from collections import deque
from enum import Enum

class TaskStatus(Enum):
    """
    Defines all the possible status for a task in the queue
    """
    QUEUED  ='queued'
    FINISHED='finished'
    FAILED  ='failed'
    STARTED ='started'
    DEFERRED='deferred'
    NOT_QUEUED='not queued'

class WorkerStatus(Enum):
    """
    Defines all the possible status for a worker in the queue
    """
    WORKING ='working'
    IDLE    ='idle'
    STOPPED ='stopped'

class Singleton(type):
    """
    The Singleton definition of the queue.
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Queue:
    """
    Definition for the queue
    """
    __metaclass__ = Singleton

    def __init__(self):
        logging.info("Creating the new instance for queue...")
        self.id = self.get_random_id()
        # First we acquire the lock to avoid concurrent access to the queue
        self.lock = threading_lock()
        # Initialize the queue, task list and the workers
        self.queue= deque([])
        self.tasks = {}
        self.workers = []
        self.timer = None

    def start_worker(self, n_workers=1):
        """
        This function starts a given number of workers providing them a
        random identifier.
        :param n_workers: the total new workers to be created
        :return: the list of new workers
        """
        ids = []
        for i in range(0, n_workers):
            worker_id = "w" + self.get_random_id()
            self.workers.append(Worker(worker_id, self))
            ids.append(worker_id)
        return ids

    def stop_worker(self, worker_id=None):
        """
        This function stops and kills a worker.
        If no id is provided, all workers are killed.
        :param worker_id: the identifier for the worker to kill
        :return: None
        """
        try:
            # First we acquire the lock to avoid concurrent access to the queue
            self.lock.acquire() #LOCK CACHE
            if worker_id == None:
                for worker in self.workers:
                    logging.info("All workers will die...")
                    worker.must_die = True
            else:
                for worker in self.workers:
                    if worker.id == worker_id:
                        worker.must_die = True
                        break
        finally:
            self.lock.release() #UNLOCK CACHE
            # Here the workers will die
            self.notify_workers()

    def remove_worker(self, worker_id):
        """
        This function removes a worker from the list of workers
        (only if the worker was notified "to die" previously)
        :param worker_id: the ID for the worker to remove
        :return:
        """
        try:
            self.lock.acquire() #LOCK CACHE
            i=0
            for worker in self.workers:
                if worker.id == worker_id and worker.must_die == True:
                    self.workers.pop(i)
                    break
                i+=1
        finally:
            self.lock.release() #UNLOCK CACHE
            self.notify_workers()

    def enqueue(self, fn, args, task_id="", timeout=600, depend=None, incompatible=None):
        try:
            self.lock.acquire() #LOCK CACHE
            task = Task(fn, args, depend, incompatible)

            if task_id=="" or task_id==None:
                task_id = self.get_random_id()
                while self.tasks.has_key(task_id):
                    task_id = self.get_random_id()
            elif self.tasks.has_key(task_id):
                raise RuntimeError("Task already at the queue (Task id : " + str(task_id) + ")")

            task.set_id(task_id)
            task.set_timeout(timeout)

            self.tasks[task_id] = task
            self.queue.appendleft(task)
            logging.debug("New task "  + str(task_id) + " added to queue.")
            logging.debug("Queue length " + str(len(self.queue)))

        finally:
            self.lock.release() #UNLOCK CACHE
            self.notify_workers()
            return task_id

    def dequeue(self):
        try:
            self.lock.acquire() #LOCK CACHE

            if len(self.queue) > 0:
                switch_pos = 1
                nextTask = self.queue[len(self.queue) - 1]
                runnable = nextTask.can_run(self.tasks)

                while not runnable:
                    switch_pos = switch_pos + 1
                    if switch_pos > len(self.queue):
                        #Reset queue state
                        self.queue.rotate(1)
                        switch_pos = 0
                        logging.debug("Cannot find runnable tasks, waiting for next try...")
                        if self.timer == None:
                            self.timer = Timer(10.0, self.notify_workers);
                            self.timer.start()
                        return None
                    elif len(self.queue) > 1:
                        logging.debug("Reordering tasks...")
                        task_aux = self.queue[len(self.queue) - switch_pos]
                        self.queue[len(self.queue) - switch_pos] = self.queue[len(self.queue) - 1]
                        self.queue[len(self.queue) - 1] = task_aux
                    nextTask = self.queue[len(self.queue) - 1]
                    runnable = nextTask.can_run(self.tasks)
                logging.debug("Task dequeued.")
                logging.debug("Queue length " + str(len(self.queue)))
                return self.queue.pop()
            return None
        finally:
            self.lock.release() #UNLOCK CACHE

    def notify_workers(self):
        logging.debug("Notifying workers")
        if self.timer != None:
            logging.debug("Cleaning timer")
            self.timer.cancel()
            self.timer = None
        for worker in self.workers:
            worker.notify()

    def check_status(self, task_id):
        task = self.tasks.get(task_id, None)
        if task:
            return task.status
        return TaskStatus.NOT_QUEUED

    def fetch_task(self, task_id):
        return self.tasks.get(task_id, None)

    def remove_task(self, task_id):
        try:
            self.lock.acquire()  # LOCK CACHE
            if self.tasks.has_key(task_id):
                self.queue.remove(self.tasks.get(task_id))
                del self.tasks[task_id]
        finally:
            self.lock.release() #UNLOCK CACHE

    def get_result(self, task_id, remove=True):
        task = self.tasks.get(task_id, None)
        if task:
            if remove and (task.status == TaskStatus.FINISHED or task.status == TaskStatus.FAILED):
                logging.debug("Removing task " + str(task_id))
                self.tasks.pop(task_id)
            return task.result
        return TaskStatus.NOT_QUEUED

    def get_error_message(self, task_id):
        task = self.tasks.get(task_id, None)
        if task:
            return task.error_message
        return None

    def get_random_id(self):
        """
        This function returns a new random task id
        @returns taskID
        """
        #RANDOM GENERATION OF THE JOB ID
        #TODO: CHECK IF NOT EXISTING ID
        import string, random
        taskID = ''.join(random.sample(string.ascii_letters+string.octdigits*5,10))
        return taskID

    def enable_stdout_log(self):
        # import sys
        # logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    @DeprecationWarning
    def enableStdoutLogging(self):
        self.enable_stdout_log()

class Worker():
    def __init__(self, _id, _queue):
        self.id = _id
        self.queue = _queue
        self.status = WorkerStatus.IDLE
        self.must_die = False
        self.task = None

    def notify(self):
        if self.status != WorkerStatus.WORKING:
            if self.must_die:
                self.queue.remove_worker(self.id)
            else:
                task = self.queue.dequeue()
                if task != None:
                    self.task = task
                    WorkerThread(self).start()

    def run(self):
        try:
            logging.debug("Worker " + str(self.id) + " starts working...")
            self.status = WorkerStatus.WORKING
            #Execute the function
            fn = self.task.fn
            args = self.task.args
            self.task.status=TaskStatus.STARTED
            self.task.result= fn(*args)
            self.task.status=TaskStatus.FINISHED
        except Exception as ex:
            if self.task != None:
                self.task.status = TaskStatus.FAILED
                self.task.error_message=ex.message
            else:
                logging.debug("WORKER " + str(self.id) + " WITHOUT TASK.")
        finally:
            logging.debug("Worker " + str(self.id) + " stops working...")
            self.status=WorkerStatus.IDLE
            self.task=None
            self.notify()

class WorkerThread (Thread):
    def __init__(self, worker):
        Thread.__init__(self)
        self.worker = worker
    def run(self):
        self.worker.run()

class Task:
    def __init__(self, fn, args, depend=None, incompatible=None):
        self.fn = fn
        self.args = args
        self.id = None
        self.timeout = 600
        self.status = TaskStatus.QUEUED
        self.result = None
        self.error_message=None
        self.depend = depend
        self.incompatible= incompatible

    def set_id(self, _id):
        self.id = _id
    def set_timeout(self, _timeout):
        self.timeout = _timeout

    def is_finished(self):
        return  self.status == TaskStatus.FINISHED
    def is_started(self):
        return  self.status == TaskStatus.STARTED
    def is_failed(self):
        return self.status == TaskStatus.FAILED
    def get_status(self):
        return self.status
    def set_depend(self, _depend):
        self.depend = _depend
    def set_incompatible(self, _incompatible):
        self.incompatible = _incompatible

    def can_run(self, tasks):
        if self.depend != None:
            for dependency in self.depend:
                task = tasks.get(dependency, None)
                if task == None:
                    logging.debug("Cannot run task " + str(self.id) + ". Unable to find task " + str(dependency) + " in queue.")
                    return False
                if not task.is_finished():
                    logging.debug("Cannot run task " + str(self.id) + ". Task " + str(dependency) + " is not finished")
                    return False

        if self.incompatible != None:
            for task in tasks.values():
                if task.is_started() and str(task.fn.__name__) in self.incompatible:
                        logging.debug("Cannot run task " + str(self.id) + ". Conflicting task " + str(task.fn.__name__) + " is running.")
                        return False
        return True
