# Copyright (C) 2023 Julien LE THENO
#
# This file is part of the VLCSequencer package
# See github.com/lethenju/VLCSequencer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""! The LOGGER module """
import inspect
import time
import tkinter as tk

# Static data
LOGGER = None
# To be set when the app is stopping
_IS_STOPPING = False


class Logger():
    """! Logger class : handles logs printing
        Both in a console and in a user-defined
        ui listbox
    """
    # Reference to the tkinter listbox used to gather the logs
    ui_trace_listbox = None

    def __init__(self):
        """! Logging module initialization """

    def set_ui_listbox(self, ui_trace_listbox):
        """! Set the UI listbox to be printing logs into"""
        self.ui_trace_listbox = ui_trace_listbox

    def log(self, trace):
        try:
            if self.ui_trace_listbox is not None:
                self.ui_trace_listbox.insert(tk.END, " " + trace)
                self.ui_trace_listbox.yview(tk.END)
        except:
            print("Log listbox incorrect !")


def logger_subscribe_ui(ui_trace_listbox):
    """! Subscribe a ui listbox into the logger singleton """
    global LOGGER
    # Logger is a singleton
    if LOGGER is None:
        LOGGER = Logger()
    LOGGER.set_ui_listbox(ui_trace_listbox)


def logger_set_is_stopping():
    """! Asks the logger to stop """
    global _IS_STOPPING
    _IS_STOPPING = True


def print_trace_in_ui(*args):
    """! Prints a trace both in the UI and in the console"""
    global LOGGER

    function_caller_name = inspect.stack()[1].function
    trace = time.strftime('%H:%M:%S') + " " + function_caller_name + "() : "
    for arg in args:
        trace = trace + arg.__str__()
    if not _IS_STOPPING:
        # Logger is a singleton
        if LOGGER is None:
            LOGGER = Logger()
        LOGGER.log(trace)
        print(trace)
    else:
        print(trace)
