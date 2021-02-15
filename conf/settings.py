import os

SERVER_SETTINGS = {
    "SERVER_HOST_NAME": os.environ.get('SERVER_HOST_NAME', "0.0.0.0"),
    "SERVER_SUBDOMAIN": os.environ.get('SERVER_SUBDOMAIN', ""),
    "SERVER_PORT_NUMBER": os.environ.get('SERVER_PORT_NUMBER', "8081"),
    "DEBUG": str(os.environ.get('DEBUG', 'true')) in ["True", "true"],
    "TMP_DIRECTORY": os.environ.get('TMP_DIRECTORY', "/tmp")
}

QUEUE_SETTINGS = {
    "N_WORKERS": int(os.environ.get('N_WORKERS', "2")),
    "FUNCTIONS_DIRS": os.environ.get('FUNCTIONS_DIRS', "./test/test_server_functions").split(",")
}
