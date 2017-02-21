import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from PySiQ import Queue

N_WORKERS = 2

queue_instance = Queue()
queue_instance.start_worker(N_WORKERS)
#Uncomment this line to get a verbose queuing
#queue_instance.enableStdoutLogging()

# ************************************************************************
# Step 4. Queue task
# ************************************************************************

def foo(n_seconds, message):
    print message + " started..."
    from time import sleep
    sleep(n_seconds)
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
    args=(5, "Task 3"),
    task_id= "Task 3"
)

queue_instance.enqueue(
    fn=foo,
    args=(20, "Task 4"),
    timeout=5,
    task_id= "Task 4"
)
