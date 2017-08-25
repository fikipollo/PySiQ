import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from time import sleep
from PySiQ import Queue

# ************************************************************************
# Initialize queue
# ************************************************************************

N_WORKERS = 2

queue_instance = Queue()
queue_instance.start_worker(N_WORKERS)

#NOTE: Uncomment this line to enable verbose queuing
#queue_instance.enableStdoutLogging()

# ************************************************************************
# Queue tasks
# ************************************************************************

def foo(N, message):
    print message + " started..."
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

# Uncomment this code to show the queue status
# while 1:
# 	print("Task 1 is " + str(queue_instance.check_status("Task 1")))
# 	print("Task 2 is " + str(queue_instance.check_status("Task 2")))
# 	print("Task 3 is " + str(queue_instance.check_status("Task 3")))
# 	print("Task 4 is " + str(queue_instance.check_status("Task 4")))
# 	print("Task 5 is " + str(queue_instance.check_status("Task 5")))
# 	sleep(3)
