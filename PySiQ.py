"""
PySiQ, a Python Simple Queue system

PySiQ is a task queue or task queue implemented for Python applications.
The main objectives of task queues are to avoid running resource-intensive tasks immediately and wait for them to complete.
Instead, tasks are scheduled by adding them to a queue, where they will wait until eventually a Worker, i.e. a special
process running in separate thread, takes them out of the queue and execute the task. This concept is especially
necessary for web applications where it is not possible to handle a heavy task during a short HTTP request window.

VERSION 0.3r1 January 2021
"""

#TODO: TIMEOUT
#TODO: AUTO REMOVE JOBS
#TODO: ADD DOCUMENTATION TO SCRIPT

import logging
import string
import random
from threading import RLock as threading_lock, Thread, Timer
from collections import deque
from enum import Enum

# Get an instance of a logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """
    Defines all the possible status for a task in the queue
    """
    QUEUED = 'queued'
    FINISHED = 'finished'
    FAILED = 'failed'
    STARTED = 'started'
    DEFERRED = 'deferred'
    NOT_QUEUED = 'not queued'


class WorkerStatus(Enum):
    """
    Defines all the possible status for a worker in the queue
    """
    WORKING = 'working'
    IDLE = 'idle'
    STOPPED = 'stopped'


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
        logger.info("Creating the new instance of queue...")
        self.id = self.get_random_id("queue_")
        logger.debug("ID for new queue instance is " + self.id)
        # First we acquire the lock to avoid concurrent access to the queue
        self.lock = threading_lock()
        # Initialize the queue, task list and the workers
        self.queue = deque([])
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
            # Get the worker ID
            # TODO: check if unique
            worker_id = self.get_random_id(prefix="w")
            # Add the worker to the list of available workers
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
            self.lock.acquire()  # LOCK CACHE
            if worker_id is None:
                # If no worker id was provided, kill all workers
                for worker in self.workers:
                    logger.info("All workers will die...")
                    worker.must_die = True
            else:
                # Otherwise kill the specified worker
                for worker in self.workers:
                    if worker.id == worker_id:
                        worker.must_die = True
                        break
        finally:
            self.lock.release()  # UNLOCK CACHE
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
            self.lock.acquire()  # LOCK CACHE
            i = 0
            for worker in self.workers:
                if worker.id == worker_id and worker.must_die == True:
                    self.workers.pop(i)
                    break
                i += 1
        finally:
            self.lock.release()  # UNLOCK CACHE
            self.notify_workers()

    def enqueue(self, fn, args, task_id=None, timeout=600, depend=None, incompatible=None):
        """
        This function enqueues a new task
        :param fn: the function to run by the task
        :param args: the list of arguments for the provided function
        :param task_id: the identifier for the task [autocreated if not provided)
        :param timeout:
        :param depend:
        :param incompatible:
        :return:
        """
        try:
            self.lock.acquire()  # LOCK CACHE
            # Create the new task
            task = Task(fn, args, depend, incompatible)
            # Get the unique identifier for the task (if not provided)
            if task_id == "" or task_id is None:
                task_id = self.get_random_id()
                while task_id in self.tasks.keys():
                    task_id = self.get_random_id()
            # Validate the task id
            if task_id in self.tasks.keys():
                raise RuntimeError("Task already at the queue (Task id : " + str(task_id) + ")")
            # Set the id and the timeout and add the task to the queue
            task.set_id(task_id)
            task.set_timeout(timeout)
            self.tasks[task_id] = task
            self.queue.appendleft(task)
            logger.debug("New task " + str(task_id) + " added to queue.")
            logger.debug("Queue length " + str(len(self.queue)))
        finally:
            self.lock.release()  # UNLOCK CACHE
            self.notify_workers()
            return task_id

    def dequeue(self):
        """
        This function will return the next executable task in the queue (if any)
        according to the specified dependencies and incompatibilities.
        :return: the next executable task (if any)
        """
        try:
            self.lock.acquire()  # LOCK CACHE
            # If there are tasks in the queue
            if len(self.queue) > 0:
                switch_pos = 1
                # Get the next queue according to FIFO
                next_task = self.queue[len(self.queue) - 1]
                # Check if the queue is runnable
                runnable = next_task.is_runnable(self.tasks)
                # While the task is not runnable, reorder the queue moving tasks
                while not runnable:
                    switch_pos = switch_pos + 1
                    if switch_pos > len(self.queue):
                        # Reset queue state
                        self.queue.rotate(1)
                        switch_pos = 0
                        logger.debug("Cannot find runnable tasks, waiting for next try...")
                        if self.timer is None:
                            self.timer = Timer(10.0, self.notify_workers);
                            self.timer.start()
                        return None
                    elif len(self.queue) > 1:
                        logger.debug("Reordering tasks...")
                        #             ________________________
                        #            |    .---------------.   |
                        # T1 | T2 | T3 | T4 -> T1 | T2 | T4 | T3 -> T1 | T3 | T4 | T2 -> T2 | T3 | T4 | T1
                        task_aux = self.queue[len(self.queue) - switch_pos]
                        self.queue[len(self.queue) - switch_pos] = self.queue[len(self.queue) - 1]
                        self.queue[len(self.queue) - 1] = task_aux
                    # Try with the next task
                    next_task = self.queue[len(self.queue) - 1]
                    runnable = next_task.is_runnable(self.tasks)
                logger.debug("Task " + str(next_task.id) + " was dequeued.")
                logger.debug("Queue length is " + str(len(self.queue)))
                return self.queue.pop()
            else:
                # Queue is empty
                return None
        finally:
            self.lock.release()  # UNLOCK CACHE

    def notify_workers(self):
        """
        This function will notify workers to check if new tasks are available
        :return: None
        """
        logger.debug("Notifying workers")
        if self.timer is not None:
            logger.debug("Cleaning timer")
            self.timer.cancel()
            self.timer = None
        for worker in self.workers:
            worker.notify()

    def check_status(self, task_id):
        """
        This function will return the status for a given task
        :param task_id: the id for the task
        :return: the status for the task
        """
        task = self.tasks.get(task_id, None)
        if task:
            return task.status
        return TaskStatus.NOT_QUEUED

    def fetch_task(self, task_id):
        """
        This function returns a task by a given task id
        :param task_id: the id for the task to be returned
        :return: the object representing the task
        """
        return self.tasks.get(task_id, None)

    def remove_task(self, task_id):
        """
        This function removes a task from the queue w/o executing.
        :param task_id: the id for the task to be removed
        :return: the removed task
        """
        try:
            self.lock.acquire()  # LOCK CACHE
            if task_id in self.tasks.keys():
                logger.debug("Removing task " + str(task_id))
                task = self.tasks.get(task_id)
                self.queue.remove(task)
                del self.tasks[task_id]
                return task
            else:
                logger.debug("Failed removing task " + str(task_id) + ". Not found in the queue.")
                return None
        finally:
            self.lock.release()  # UNLOCK CACHE

    def get_result(self, task_id, remove=True):
        """
        This function returns the stored result (if any) for the finished or
        failed task and removes the task from the queue if specified
        :param task_id: the id for the task
        :param remove: if True (default), return the value and remove the task from queue
        :return: the result (if any)
        """
        task = self.tasks.get(task_id, None)
        if task:
            if remove and (task.status == TaskStatus.FINISHED or task.status == TaskStatus.FAILED):
                logger.debug("Removing task " + str(task_id))
                self.tasks.pop(task_id)
            return task.result
        else:
            logger.debug("Failed getting the result for task " + str(task_id) + ". Not found in the queue.")
            return None

    def get_error_message(self, task_id):
        """
        This function returns the stored error message (if any) for a task
        in the queue
        :param task_id: the id for the task
        :return: the error message (if any)
        """
        task = self.tasks.get(task_id, None)
        if task:
            return task.error_message
        else:
            logger.debug("Failed getting the result for task " + str(task_id) + ". Not found in the queue.")
            return None

    @staticmethod
    def get_random_id(prefix="", suffix="", length=10):
        """
        This function returns a new random identifier
        :param prefix: an optional prefix for the identifier
        :param suffix: an optional suffix for the identifier
        :param length: the length for the random identifier (w/o prefix and suffix)
        :return: the random identifier
        """
        random_id = ''.join(random.sample(string.ascii_letters + string.octdigits * 5, length))
        return prefix + random_id + suffix

    @staticmethod
    def enable_stdout_log():
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode is enabled")


class Worker:
    def __init__(self, _id, _queue):
        """
        Create a new worker instance
        :param _id: the worker id
        :param _queue: the associated queue for the worker
        """
        self.id = _id
        self.queue = _queue
        self.status = WorkerStatus.IDLE
        self.must_die = False
        self.task = None

    def notify(self):
        """
        When a worker is notified, it will check for the next executable task
        in the queue, unless the worker received the signal "must die" which
        will cause the worker to stop and die.
        :return: None
        """
        if self.status != WorkerStatus.WORKING:
            if self.must_die:
                self.queue.remove_worker(self.id)
            else:
                task = self.queue.dequeue()
                if task is not None:
                    self.task = task
                    WorkerThread(self).start()

    def run(self):
        """
        This function will launch the execution of a given task by this worker
        :return: None
        """
        try:
            logger.debug("Worker " + str(self.id) + " starts working...")
            self.status = WorkerStatus.WORKING
            # Execute the function
            fn = self.task.fn
            args = self.task.args
            self.task.status = TaskStatus.STARTED
            self.task.result = fn(*args)
            self.task.status = TaskStatus.FINISHED
        except Exception as ex:
            if self.task is not None:
                self.task.status = TaskStatus.FAILED
                self.task.error_message = ex.message
            else:
                logger.debug("WORKER " + str(self.id) + " WITHOUT TASK.")
        finally:
            logger.debug("Worker " + str(self.id) + " stops working...")
            self.status = WorkerStatus.IDLE
            self.task = None
            self.notify()


class WorkerThread(Thread):
    def __init__(self, worker):
        Thread.__init__(self)
        self.worker = worker

    def run(self):
        self.worker.run()


class Task:
    def __init__(self, fn, args, depend=None, incompatible=None):
        """
        Creates a new task object
        :param fn: the function to be executed
        :param args: the arguments for the function
        :param depend: a list of identifiers for dependencies, i.e. tasks that must be finished before this task is executed
        :param incompatible: a list of function names that cannot be executed at the same time than the provided function
        """
        self.fn = fn
        self.args = args
        self.id = None
        self.timeout = 600
        self.status = TaskStatus.QUEUED
        self.result = None
        self.error_message=None
        self.depend = depend
        self.incompatible = incompatible

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

    def is_runnable(self, tasks):
        """
        Determines whether this task can be executed taking in account the
        dependencies and the incompatibilities
        :param tasks: a list of tasks that may be in a queue
        :return: whether this task can be executed or not
        """
        # First check dependencies
        if self.depend is not None:
            for dependency in self.depend:
                task = tasks.get(dependency, None)
                if task is None:
                    logger.debug("Cannot run task " + str(self.id) + ". Unable to find task " + str(dependency) + " in queue.")
                    return False
                if not task.is_finished():
                    logger.debug("Cannot run task " + str(self.id) + ". Task " + str(dependency) + " is not finished")
                    return False
        # Now check incompatibilities
        if self.incompatible is not None:
            for task in tasks.values():
                if task.is_started() and str(task.fn.__name__) in self.incompatible:
                    logger.debug("Cannot run task " + str(self.id) + ". Conflicting task " + str(task.fn.__name__) + " is running.")
                    return False
        # If we are here, the task is runnable
        return True
