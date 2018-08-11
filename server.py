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
from flask_cors import CORS
from PySiQ import Queue, TaskStatus, WorkerStatus
import os
import json
from imp import load_source
from inspect import getmembers, isfunction
from shutil import copyfile

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
        self.functions = self.load_functions()

        self.queue_instance = Queue()

        if self.settings.get("DEBUG"):
            self.queue_instance.enable_stdout_log()

        self.queue_instance.start_worker(self.settings.get("N_WORKERS", 4))

        CORS(self.app, resources=r'/api/*')

        @self.app.route(self.settings.get("SERVER_SUBDOMAIN", "") + '/api/enqueue', methods=['OPTIONS', 'POST'])
        def enqueue():
            if request.method == "OPTIONS":
                return jsonify(True)

            fn = request.json.get("fn")
            args = request.json.get("args")
            task_id = request.json.get("task_id", None)
            depend = request.json.get("depend", [])
            incompatible = request.json.get("incompatible", [])

            if fn not in self.functions:
                return jsonify({'success': False})

            task_id = self.queue_instance.enqueue(
                fn=self.functions[fn],
                args=args,
                task_id=task_id,
                depend=depend,
                incompatible=incompatible
            )

            return jsonify({'success': True, 'task_id' : task_id})

        @self.app.route(self.settings.get("SERVER_SUBDOMAIN", "") + '/api/status/<path:task_id>', methods=['OPTIONS', 'GET'])
        def check_status(task_id):
            if request.method == "OPTIONS":
                return jsonify(True)
            try: # Fix issue #2 reported by @jeremydouglass
                return jsonify({'success': True, 'status': self.queue_instance.check_status(task_id).name}) # This may work depending on the version of python
            except Exception as e:
                return jsonify({'success': True, 'status': self.queue_instance.check_status(task_id)})

        @self.app.route(self.settings.get("SERVER_SUBDOMAIN", "") + '/api/result/<path:task_id>', methods=['OPTIONS', 'GET'])
        def get_result(task_id):
            if request.method == "OPTIONS":
                return jsonify(True)
            remove = (request.args.get('remove', default=0) == 0)
            result = self.queue_instance.get_result(task_id, remove)
            if isinstance(result, TaskStatus):
                return jsonify({'success': False, 'message': "Task couldn't be found in queue"})
            return jsonify({'success': True, 'result': result})

        @self.app.route(self.settings.get("SERVER_SUBDOMAIN", "") + '/api/remove/<path:task_id>', methods=['OPTIONS', 'DELETE'])
        def remove_task(task_id):
            if request.method == "OPTIONS":
                return jsonify(True)
            self.queue_instance.remove_task(task_id)
            return jsonify({'success': True})

    def load_functions(self):
        functions = {}
        for functions_source in self.settings.get("FUNCTIONS_DIRS", []):
            path = functions_source.get("path")
            if path.startswith("./") or path.startswith("../"):
                path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))).rstrip("/") + "/" + path
            path = os.path.abspath(path).rstrip("/") + "/"
            files = functions_source.get("files")
            for _file in files:
                module_name = _file.replace(".py", "")
                module = load_source(module_name, path + _file)
                functions_list = [o for o in getmembers(module) if isfunction(o[1])]
                for _function in functions_list:
                    functions[_function[0]] = _function[1]
        return functions

    def launch(self):
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
    # Copy the default settings
    if not os.path.isfile(conf_path):
        copyfile(os.path.dirname(os.path.realpath(__file__)) + "/server.default.cfg", conf_path)

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
