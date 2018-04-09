from time import sleep

def foo(task_id, file_path, delay):
    print "Task " +  str(task_id) + " started..."
    file = open(file_path,"a")
    file.write("This is task " + str(task_id) + ". I'm safely writing in this file.\n")
    sleep(delay)
    file.close()
    print "Task " + str(task_id) + " finished"