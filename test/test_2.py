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
def foo(task_id, file_path, delay):
    print("Task " +  str(task_id) + " started...")
    file = open(file_path,"a")
    file.write("This is task " + str(task_id) + ". I'm safely writing in this file.\n")
    sleep(delay)
    file.close()
    print("Task " + str(task_id) + " finished")


print("Enqueueing Task 1...")
print("Enqueueing Task 2 (incompatible with Task 1)...")
print("Enqueueing Task 3 (depend on Task 2)...")

queue_instance.enqueue(
    fn=foo,
    args=(1, "/tmp/test_pysiq.log", 10),
    task_id=1
)

queue_instance.enqueue(
    fn=foo,
    args=(2, "/tmp/test_pysiq.log", 5),
    task_id=2,
    incompatible = ["foo"]
)

queue_instance.enqueue(
    fn=foo,
    args=(3, "/tmp/test_pysiq.log", 5),
    task_id=3,
    depend=[2]
)

while 1:
    done_tasks = 0
    for i in range(1,4):
        status = queue_instance.check_status(i)
        print("Task " + str(i) + " is " + str(status))
        if "FINISHED" in str(status):
            done_tasks+=1
    if done_tasks == 3:
        break
    sleep(3)
