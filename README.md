# Introduction
PySiQ (_Python Simple Queue_) is a job queue or task queue implemented for Python applications. The main objective of task queues is to avoid running resource-intensive tasks immediately and wait for them to complete. Instead, tasks are scheduled by adding them to a queue, where they will wait until eventually a _worker_, i.e. a special process running in separate thread, takes them out of the queue and execute the job. This concept is especially necessary for web applications where it is not possible to handle a heavy task during a short HTTP request window.

# Features
PySiQ is entirely implemented in Python and provides the following features:
- Multi-process execution on tasks, configurable number of workers.
- The status of the queued tasks can be easily checked at any time.
- Dependencies between tasks can be specified executing them in the appropriate order.
- Incompatible tasks can be specified, avoiding execute conflicting tasks simultaneously.
- The results for tasks are stored until the client asks for them.
- Lightweight module. The code takes less than 300 lines of code.
- Easy to use and to install in your application.
- It does not depend on other libraries or tools.

The main component of PySiQ is the *Queue*, a Python object that works as a task dispatcher and worker-pool manager. The Queue is a _singleton_ instance that is listening to the other components in the application (Figure 1-1). When the queue is instantiated, a certain number of *Workers* are created depending on the user's settings. Workers are special threads that extract tasks from the queue and execute them. By default, workers are idle, waiting for new tasks are sent to the queue (Figure 1-2). When a client needs to execute certain time-consuming job, it is encapsulated in a *Task* instance, defining the function or code to be executed and the parameters for its execution (Figure 1-3). Some additional parameters can be specified such as a timeout that will abort the execution of the task if it does not start after a determined amount of time, and a list of dependencies, i.e. the identifiers for the tasks that must be completed before launching the execution of the new task. The task instance is sent to the queue and workers are notified that a new task is waiting for being executed. As soon as a worker is idle, it takes the next task at the queue and starts the execution, provided that all its dependencies already finished (Figure 1-4).

The queue contains an internal table that keeps the status for all the tasks in the queue. Possible statuses are: "waiting", "running", "finished", and "error" (Figure 1-5). When a task is finished, it is kept in this table in addition to the results of the execution, until someone asks for the results. Similarly, failed tasks are kept in the table with the information of the error (Figure 1-6).

<div style="width:80%; max-width: 800px; margin:auto;">
<img src="https://cloud.githubusercontent.com/assets/11427394/24916922/df0d9fd6-1edb-11e7-9da1-1bfb3c5e6434.png">
<p style="text-align:justify;"><b>Figure 1. Overview of the design of the queue system.</b></p>
</div>

# Example of use 1 (file test/test_1.py)
The following code fragment exemplifies the usage of the developed module. For this use case an instance of queue is initialized with two workers. A total of five tasks are sent to the queue. All tasks will execute the same function called _foo_ which displays a message indicating that execution has started, then waits _N_ seconds, and displays a message announcing the end of execution. Both the displayed message and the duration of the delay (the _N_ value) are provided as parameters for the _foo_ function.

Tasks 1 and 3 will take 10 seconds for execution, while tasks 2 and 4 will take less than 5 seconds. Task 5 takes 4 seconds but it won't start until tasks 3 and 4 are completed.

Figure 2 shows the temporal line for the execution of the tasks, as well as the status for the queue and the workers at different time-points.

```python
# ************************************************************************
# Initialize queue
# ************************************************************************
N_WORKERS = 2

queue_instance = Queue()
queue_instance.start_worker(N_WORKERS)


# ************************************************************************
# Queue tasks
# ************************************************************************

def foo(N, message):
    print message + " started..."
    from time import sleep
    sleep(N)
    print message + " finished"

queue_instance.enqueue(
    fn=foo,
    args=(10, "Task 1"),
    task_id= "Task 1"
)

queue_instance.enqueue(
    fn=foo,
    args=(4, "Task 2"),
    task_id= "Task 2"
)

queue_instance.enqueue(
    fn=foo,
    args=(10, "Task 3"),
    task_id= "Task 3"
)

queue_instance.enqueue(
    fn=foo,
    args=(5, "Task 4"),
    task_id= "Task 4"
)

queue_instance.enqueue(
    fn=foo,
    args=(4, "Task 5"),
    task_id= "Task 5",
    depend= ["Task 3", "Task 4"]
)
```

<div style="width:80%; max-width: 800px; margin:auto;">
<img src="https://cloud.githubusercontent.com/assets/11427394/24916923/df174b44-1edb-11e7-863b-693fc4117b90.png">
<p style="text-align:justify;"><b>Figure 2. Output for the example program, overview for the tasks' execution, and status of the queue and workers.</b>  (A) - When the program execution starts, the queue is empty and both workers are idle. The five tasks are then sequentially added to the queue and workers are notified to start working. (B) - The first two tasks are extracted from the queue and executed by the workers. Each task shows a message in the terminal. (C) - After four seconds, task 2 finishes, and worker 2 becomes idle.  Worker 2 then asks for a new task (task 3) and executes it. (D) - After four seconds, task 1 finishes and task 4 starts. (E) - When task 3 is done, worker 2 become idle and waits for a new task; however, task 5 cannot start because it depends on task 4, which still running on worker 1. (F) - Once task 4 finished, task 5 is valid for being executed by any worker. (G) - Finally, after 4 seconds, task 5 is finished.</p>
</div>


# Example of use 2 (file test/test_2.py)
The following code exemplifies the usage of all the available options. For this use case an instance of queue is initialized with two workers. Three tasks are sent to the queue. Tasks execute the same function _foo_ which opens and manipulates the content of a given file and then wait _n_ seconds. The parameters for the function are the identifier for the task, the path to the file, and the duration of the delay.

Task 1 takes 10 seconds for execution, while tasks 2 and 3 will take 5 seconds.
Task 3 won't start until task 2 is completed (i.e. depends on task 2), and task 2  won't start until task 1 is done as it is _incompatible_ with task 1.

Figure 3 shows the temporal line for the execution of the tasks, as well as the status for the queue and the workers at different time-points.

```python
# ************************************************************************
# Initialize queue
# ************************************************************************
N_WORKERS = 2

queue_instance = Queue()
queue_instance.start_worker(N_WORKERS)


# ************************************************************************
# Queue tasks
# ************************************************************************

def foo(task_id, file_path, delay):
    file = open(file_path,"a")
    file.write("This is task " + str(task_id) + ". I'm safely writing in this file.")
    from time import sleep
    sleep(delay)
    file.close()

queue_instance.enqueue(
    fn=foo,
    args=(1, "~/test_pysiq.log", 10),
    task_id= 1
)

queue_instance.enqueue(
    fn=foo,
    args=(2, "~/test_pysiq.log", 5),
    task_id= 2,
    incompatible = ["foo"]
)

queue_instance.enqueue(
    fn=foo,
    args=(3, "~/test_pysiq.log", 5),
    task_id= 3,
    depend= [2]
)

```

# Advanced use
Figure 4 shows a more complex example of using. For this use of case two different users interact with the queue by sending requests to a server-side program. More specifically, each user sends first a request to the server in order to launch certain time-consuming task. For each client, a task instance is created and sent to the queue and the identifier for the new job is returned to the client application. While waiting for the end if the task, the clients send periodically a request in order to query the execution status. Finally, when the task if finished, the user can retrieve the result for the execution of the task.

<div style="width:80%; max-width: 800px; margin:auto;">
<img src="https://cloud.githubusercontent.com/assets/11427394/24916921/df0a7aa4-1edb-11e7-9b0b-c90bcfd3811c.png">
<p style="text-align:justify;"><b>Figure 4. Using the queue system in a Client-Server environment.</b>From client side, two different users send a request to execute some time-consuming task at server side (1). When a request is received, the server program wraps the job to be executed, and its parameters into an instance of task, and sends the new object to the queue system (2).  When a task is queued, an identifier is returned that uniquely identifies the task in the queue system. Task identifiers are then returned to the corresponding client that can use it later to check the execution status or retrieve the results. Every time that a new task is received, the queue system notifies the workers (3), and those that are idle extract and execute the next tasks in the queue (4). While the task is being executed, clients can check periodically the status of the job by sending a request to the server (5). Possible statuses are "queued", "running", "finished" and "failed". When a worker finishes the execution of a task, the result is kept in the queue system until it is requested, and the worker proceeds to execute the next task in queue (6). If no new tasks are available the worker becomes idle. Finally, when the client detects that the task is done - i.e. it receives a 'finished' status (7), a new request is sent in order to retrieve the results of the execution (8).</p>
</div>
