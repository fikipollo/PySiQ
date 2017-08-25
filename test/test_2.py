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

def foo(task_id, file_path, delay):
    print "Task " +  str(task_id) + " started..."
    file = open(file_path,"a")
    file.write("This is task " + str(task_id) + ". I'm safely writing in this file.\n")
    sleep(delay)
    file.close()
    print "Task " + str(task_id) + " finished"

queue_instance.enqueue(
    fn=foo,
    args=(1, "/tmp/test_pysiq.log", 10),
    task_id= 1
)

queue_instance.enqueue(
    fn=foo,
    args=(2, "/tmp/test_pysiq.log", 5),
    task_id= 2,
    incompatible = ["foo"]
)

queue_instance.enqueue(
    fn=foo,
    args=(3, "/tmp/test_pysiq.log", 5),
    task_id= 3,
    depend= [2]
)
