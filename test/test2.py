import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from PySiQ import Queue
from time import sleep, time
from random import random

N_WORKERS = 2

queue_instance = Queue()
queue_instance.start_worker(N_WORKERS)
#Uncomment this line to get a verbose queuing
#queue_instance.enableStdoutLogging()

# ************************************************************************
# Step 4. Queue task
# ************************************************************************
start_time = time()

def log(message):
    print("--- %.2f seconds ---" % (time() - start_time)) + message


def foo(n_seconds, message):
    log(message + " started.")
    sleep(n_seconds)
    log(message + " finished.")
    return random()

#CLIENT 1 SEND TASK Task 1
task_1_id = queue_instance.enqueue(
    fn=foo,
    args=(6, "Task 1"),
)

#CLIENT 2 SEND TASK Task 2
task_2_id = queue_instance.enqueue(
    fn=foo,
    args=(10, "Task 2"),
)

# WAIT 5 SECONDS
sleep(5)

task_1_status = queue_instance.check_status(task_1_id)
task_2_status = queue_instance.check_status(task_2_id)

log("Task 1 is " + str(task_1_status))
log("Task 2 is " + str(task_2_status))

# WAIT 5 SECONDS
sleep(5)

task_1_status = queue_instance.check_status(task_1_id)
task_2_status = queue_instance.check_status(task_2_id)

log("Task 1 is " + str(task_1_status))
print "Task 1 returned " + str(queue_instance.get_result(task_1_id))

log("Task 2 is " + str(task_2_status))

# WAIT 5 SECONDS
sleep(5)

task_2_status = queue_instance.check_status(task_2_id)

log("Task 2 is " + str(task_2_status))
print "Task 2 returned " + str(queue_instance.get_result(task_2_id))
