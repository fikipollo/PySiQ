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
    print "Task " +  message + " started..."
    from time import sleep
    sleep(n_seconds)
    print "Task " + message + " finished"


queue_instance.enqueue(
    fn=foo,
    args=(10, "1"),
    task_id= "1"
)

queue_instance.enqueue(
    fn=foo,
    args=(4, "2"),
    task_id= "2"
)

queue_instance.enqueue(
    fn=foo,
    args=(5, "3"),
    task_id= "3",
	depend = ["1"]
)

queue_instance.enqueue(
    fn=foo,
    args=(20, "4"),
    timeout=5,
    task_id= "4",
	depend = ["3"]
)

queue_instance.enqueue(
    fn=foo,
    args=(10, "5"),
    timeout=5,
    task_id= "5",
	depend = ["1", "3"]
)
