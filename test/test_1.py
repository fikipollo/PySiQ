import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from time import sleep
from PySiQ import Queue

# ************************************************************************
# Initialize queue
# ************************************************************************

N_WORKERS = 2
print("Starting new queue with " + str(N_WORKERS) + " workers")
queue_instance = Queue()
queue_instance.start_worker(N_WORKERS)

# NOTE: Uncomment this line to enable verbose queuing
# queue_instance.enable_stdout_log()


# ************************************************************************
# Queue tasks
# ************************************************************************


def foo(n, message):
    print(message + " started...")
    sleep(n)
    print(message + " finished")


print("Enqueueing Task 1...")
print("Enqueueing Task 2...")
print("Enqueueing Task 3...")
print("Enqueueing Task 4...")
print("Enqueueing Task 5 (depend on tasks 3 and 4)...")

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

while 1:
    done_tasks = 0
    for i in range(1,6):
        status = queue_instance.check_status("Task " + str(i))
        print("Task " + str(i) + " is " + str(status))
        if "FINISHED" in str(status):
            done_tasks+=1
    if done_tasks == 5:
        break
    sleep(3)
