"""
PySiQ, a Python Simple Queue system

PySiQ is a task queue or task queue implemented for Python applications.
The main objectives of task queues are to avoid running resource-intensive tasks immediately and wait for them to complete.
Instead, tasks are scheduled by adding them to a queue, where they will wait until eventually a Worker, i.e. a special
process running in separate thread, takes them out of the queue and execute the task. This concept is especially
necessary for web applications where it is not possible to handle a heavy task during a short HTTP request window.

VERSION 0.3 APRIL 2018
"""

import logging
from flask import Flask, request, jsonify
from PySiQ import Queue, TaskStatus, WorkerStatus
import os
import json
import importlib

class Application(object):
    #******************************************************************************************************************
    # CONSTRUCTORS
    #******************************************************************************************************************
    def __init__(self):
        #*******************************************************************************************
        #* SERVER DEFINITION
        #*******************************************************************************************
        self.app = Flask(__name__)
        self.settings = read_settings_file()
        self.load_functions()

        self.queue_instance = Queue()
        print("Queue ID is " + self.queue_instance.id)
        self.queue_instance.start_worker(self.settings.get("N_WORKERS", 4))

        @self.app.route(self.settings.get("SERVER_SUBDOMAIN", "") + '/api/enqueue', methods=['OPTIONS', 'POST'])
        def enqueue():
            fn = request.json.get("fn")
            fn = request.json.get("args")
            task_id = request.json.get("task_id")

            return jsonify({'success': True})
            # return (jsonify(self.content), 200, {'Content-Type': 'application/json; charset=utf-8'})

        @self.app.route(self.settings.get("SERVER_SUBDOMAIN", "") + '/api/status/<path:task_id>', methods=['OPTIONS', 'GET'])
        def check_status(task_id):
            return jsonify({'success': True, 'status': self.queue_instance.check_status(task_id).name})

    def load_functions(self):
        print("load_functions")
        for functions_source in self.settings.get("FUNCTIONS_DIRS", []):
            path = functions_source.get("path")
            if path.startswith("./") or path.startswith("../"):
                path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))).rstrip("/") + "/" + path
            files = functions_source.get("path")
            # for file in files:
            #     im

    def launch(self):
        print("launch")
        ##*******************************************************************************************
        ##* LAUNCH APPLICATION
        ##*******************************************************************************************
        self.app.run(host=self.settings.get("SERVER_HOST_NAME", "0.0.0.0"),
                     port=self.settings.get("SERVER_PORT_NUMBER", 8081),
                     debug=self.settings.get("DEBUG", False), threaded=True, use_reloader=False)

    def log(self, message, type="info"):
        if self.settings.get("DEBUG", False) == True:
            if type == "warn":
                logging.warning(message)
            elif type == "err":
                logging.error(message)
            else:
                logging.info(message)

def read_settings_file():
    conf_path = os.path.dirname(os.path.realpath(__file__)) + "/server.cfg"
    settings = {}
    if os.path.isfile(conf_path):
        config = json.load(open(conf_path))

        SERVER_SETTINGS = config.get("SERVER_SETTINGS", {})
        settings["SERVER_HOST_NAME "] = SERVER_SETTINGS.get('SERVER_HOST_NAME', "0.0.0.0")
        settings["SERVER_SUBDOMAIN"] = SERVER_SETTINGS.get('SERVER_SUBDOMAIN', "")
        settings["SERVER_PORT_NUMBER"] = SERVER_SETTINGS.get('SERVER_PORT_NUMBER', 8081)
        settings["DEBUG"] = SERVER_SETTINGS.get('DEBUG', False)
        settings["TMP_DIRECTORY"] = SERVER_SETTINGS.get('TMP_DIRECTORY', "/tmp")

        QUEUE_SETTINGS = config.get("QUEUE_SETTINGS", {})
        settings["N_WORKERS"] = QUEUE_SETTINGS.get('N_WORKERS', 2)
        settings["FUNCTIONS_DIRS"] = QUEUE_SETTINGS.get('FUNCTIONS_DIRS',[])

    return settings

