#Introduction
PySiQ (_Python Simple Queue_) is a job queue or task queue implemented for Python applications. The main objectives of task queues are to avoid running resource-intensive tasks immediately and wait for them to complete. Instead, tasks are scheduled by adding them to a queue, where they will wait until eventually a Worker, i.e. a special process running in separate thread, takes them out of the queue and execute the job. This concept is especially necessary for web applications where it is not possible to handle a heavy task during a short HTTP request window.

#Features
PySiQ is entirely implemented in Python and provides the following features:
 - Multi-process execution on tasks, configurable number of Workers.
 - The status of the enqueued jobs can be easily checked at any time.
 - Task result storage
 - Lightweight module. The code only takes 200 lines of code.
 - Easy to use and easy to install in your application.
 - Does not depend on other libraries or tools.
