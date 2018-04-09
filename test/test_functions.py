from time import sleep

def foo(N, message):
    print message + " started..."
    sleep(N)
    print message + " finished"