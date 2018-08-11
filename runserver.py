#!/usr/bin/env python

try:
    from server import Application
except Exception as ex:
    from server.server import Application

application = Application()
application.launch()