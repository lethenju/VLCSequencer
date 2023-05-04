
import inspect
import time
import tkinter as tk

# Static data
logger = None

class Logger():
    # Reference to the tkinter listbox used to gather the logs
    ui_trace_listbox = None

    def __init__(self):
        """! Logging module initialization """

    def add_ui_listbox(self, ui_trace_listbox):
        self.ui_trace_listbox = ui_trace_listbox

    def log(self, trace):
        if self.ui_trace_listbox is not None:
            self.ui_trace_listbox.insert(tk.END, " " + trace)
            self.ui_trace_listbox.yview(tk.END)


def LoggerSubscribeUI(ui_trace_listbox):
    global logger
    # Logger is a singleton
    if (logger is None):
        logger = Logger()
    logger.add_ui_listbox(ui_trace_listbox)


def PrintTraceInUi(*args):
    global logger
    # Logger is a singleton
    if (logger is None):
        logger = Logger()

    function_caller_name = inspect.stack()[1].function
    trace = time.strftime('%H:%M:%S') + " " + function_caller_name + "() : "
    for arg in args:
        trace = trace + arg.__str__()
    print(trace)
    logger.log(trace)