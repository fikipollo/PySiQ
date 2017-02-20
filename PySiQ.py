"""
PySiQ, a Python Simple Queue system

PySiQ is a task queue or task queue implemented for Python applications.
The main objectives of task queues are to avoid running resource-intensive tasks immediately and wait for them to complete.
Instead, tasks are scheduled by adding them to a queue, where they will wait until eventually a Worker, i.e. a special
process running in separate thread, takes them out of the queue and execute the task. This concept is especially
necessary for web applications where it is not possible to handle a heavy task during a short HTTP request window.
"""

#TODO: TIMEOUT
#TODO: AUTO REMOVE JOBS
#TODO: ADD DOCUMENTATION TO SCRIPT

import logging
from threading import RLock as threading_lock, Thread
from collections import deque
from enum import Enum
from time import sleep

class TaskStatus(Enum):
	QUEUED  ='queued'
	FINISHED='finished'
	FAILED  ='failed'
	STARTED ='started'
	DEFERRED='deferred'
	NOT_QUEUED='not queued'

class WorkerStatus(Enum):
	WORKING ='working'
	IDLE	='idle'
	STOPPED ='stopped'

class Queue:
	def __init__(self):
		logging.info("CREATING NEW INSTANCE FOR Queue...")
		self.lock = threading_lock()
		self.queue= deque([])
		self.tasks = {}
		self.workers = []

	def start_worker(self, n_workers=1):
		ids = []
		worker_id=""
		for i in range(0, n_workers):
			worker_id = "w" + self.get_random_id()
			self.workers.append(Worker(worker_id, self))
			ids.append(worker_id)
		return ids

	def stop_worker(self, worker_id=None):
		try:
			self.lock.acquire() #LOCK CACHE
			if worker_id == None:
				for worker in self.workers:
					if worker.must_die != True:
						worker_id = worker.id
						break
				if worker_id == None:
					logging.info("All workers will die...")

			for worker in self.workers:
				if worker.id == worker_id:
					worker.must_die = True
					break
		finally:
			self.lock.release() #UNLOCK CACHE
			self.notify_workers()

	def remove_worker(self, worker_id):
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

	def enqueue(self, fn, args, task_id="", timeout=600, depend=None):
		try:
			self.lock.acquire() #LOCK CACHE
			task = Task(fn, args, depend)

			if task_id=="":
				task_id = self.get_random_id()
				while self.tasks.has_key(task_id):
					task_id = self.get_random_id()
			elif self.tasks.has_key(task_id):
				raise RuntimeError("Task already at the queue (Task id : " + task_id + ")")

			task.set_id(task_id)
			task.set_timeout(timeout)

			self.tasks[task_id] = task
			self.queue.appendleft(task)

			logging.info("New task "  + task_id + " added to queue.")
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
				runnable = nextTask.canRun(self.tasks)

				while not runnable:
					switch_pos = switch_pos + 1
					if switch_pos > len(self.queue):
						#Reset queue state
						task_aux = self.queue.pop()
						self.queue.appendleft(task_aux)
						switch_pos = 0
						print "Cannot find runnable tasks, waiting 5 seconds..."
						sleep(5)
					elif len(self.queue) > 1:
						print "Switching tasks..."
						task_aux = self.queue[len(self.queue) - switch_pos]
						self.queue[len(self.queue) - switch_pos] = self.queue[len(self.queue) - 1]
						self.queue[len(self.queue) - 1] = task_aux
					nextTask = self.queue[len(self.queue) - 1]
					runnable = nextTask.canRun(self.tasks)
				return self.queue.pop()
			return None
		finally:
			self.lock.release() #UNLOCK CACHE

	def notify_workers(self):
		for worker in self.workers:
			worker.notify()

	def check_status(self, task_id):
		task = self.tasks.get(task_id, None)
		if task:
			return task.status
		return TaskStatus.NOT_QUEUED

	def fetch_task(self, task_id):
		return self.tasks.get(task_id, None)

	def get_result(self, task_id, remove=True):
		task = self.tasks.get(task_id, None)
		if task:
			if remove and (task.status == TaskStatus.FINISHED or task.status == TaskStatus.FAILED):
				logging.info("Removing task " + task_id)
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
			logging.info("Worker " + self.id + " starts working...")
			self.status = WorkerStatus.WORKING
			#Execute the function
			fn = self.task.fn
			args = self.task.args
			self.task.status=TaskStatus.STARTED
			self.task.result= fn(*args)
			self.task.status=TaskStatus.FINISHED
		except Exception as ex:
			self.task.status = TaskStatus.FAILED
			self.task.error_message=ex.message
		finally:
			logging.info("Worker " + self.id + " stops working...")
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
	def __init__(self, fn, args, depend=None):
		self.fn = fn
		self.args = args
		self.id = None
		self.timeout = 600
		self.status = TaskStatus.QUEUED
		self.result = None
		self.error_message=None
		self.depend = depend

	def set_id(self, _id):
		self.id = _id
	def set_timeout(self, _timeout):
		self.timeout = _timeout

	def is_finished(self):
		return  self.status == TaskStatus.FINISHED
	def is_failed(self):
		return self.status == TaskStatus.FAILED
	def get_status(self):
		return self.status
	def set_depend(self, _depend):
		self.depend = _depend

	def canRun(self, tasks):
		if self.depend == None:
			return True

		for dependency in self.depend:
			task = tasks.get(dependency, None)
			if task == None:
				print "Cannot run task " + self.id + ". Unable to find task " + dependency + " in queue."
				return False
		 	if not task.is_finished():
				print "Cannot run task " + self.id + ". Task " + dependency + " is not finished"
				return False
		return True
