#!/usr/bin/env python

try:
    from server import Application
except Exception as ex:
    from server.server import Application

application = Application().app

if __name__ == "__main__":
    application.run()
