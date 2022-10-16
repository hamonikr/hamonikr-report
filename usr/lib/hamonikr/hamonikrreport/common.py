#!/usr/bin/python3
import gi
import imp
import os
import sys
import threading

from gi.repository import GObject

DATA_DIR = "/usr/share/hamonikr/hamonikrreport"
INFO_DIR = os.path.join(DATA_DIR, "reports")
TMP_DIR = "/tmp/hamonikrreport"

# Used as a decorator to run things in the background
def _async(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

# Used as a decorator to run things in the main loop, from another thread
def idle(func):
    def wrapper(*args):
        GObject.idle_add(func, *args)
    return wrapper

class InfoReportContainer():
    def __init__(self, uuid, path):
        self.uuid = uuid
        self.path = path
        sys.path.insert(0, path)
        import HamonikrReportInfo
        imp.reload(HamonikrReportInfo)
        self.instance = HamonikrReportInfo.Report()
        sys.path.remove(path)

