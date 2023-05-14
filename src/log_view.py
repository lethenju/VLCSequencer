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
import tkinter as tk
from typing import Any

from colors import *
from logger import PrintTraceInUi, LoggerSubscribeUI
from listboxes_base import BaseListbox

class LogListboxEntry(tk.Frame):
    """! Represents an entry in the log list view."""
    timestamp_label = None
    log_text_label  = None

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.timestamp_label = tk.Label(self, font=(
            'calibri', 11, 'bold'), bg=UI_BACKGROUND_COLOR, fg="white")
        self.timestamp_label.pack(side=tk.LEFT, expand=False)
        
        self.log_text_label = tk.Label(self,  font=(
            'calibri', 11), bg=UI_BACKGROUND_COLOR, fg="white")
        self.log_text_label.pack(side=tk.RIGHT, expand=False, padx = 10)
    
    def setup(self, timestamp, log_text):
        """! Setup the widget with the timestamp and video_name """
        PrintTraceInUi("Log list entry ", timestamp, " - ", log_text)
    
        self.timestamp_label.configure(text=timestamp)
        self.log_text_label.configure(text=log_text)

    def destroy(self):
        self.timestamp_label.pack_forget()
        self.log_text_label.pack_forget()

        self.timestamp_label.destroy()
        self.log_text_label.destroy()

class LogListbox(BaseListbox):
    _log_view = None
    
    # Tkinter Listbox of played video with time of last playback
    _log_listbox = None

    def __init__(self, tk_notebook, nb_elements = 10):
        """! Initialize the listbox 
            @param tk_notebook : the tk notebook in which add the listbox
            @param nb_elements : the max nb_elements to be displayed at once
        """
        super().__init__(tk_notebook, "Logs", nb_elements)
        
        tk_notebook.add(super().get_view(), text = "Logs")
        LoggerSubscribeUI(super().get_listbox())

    # Actually not called because the log listbox is subcribed in the logger, and no other logs are added that way
    def add_entry(self, timestamp, log):
        """! Add an entry in the listbox """
        entry = LogListboxEntry(super().get_listbox(), bg=UI_BACKGROUND_COLOR)
        entry.setup(timestamp, log)
        entry.pack(fill=tk.X)
        super().get_listbox().insert(0, entry)
