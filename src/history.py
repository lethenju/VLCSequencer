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

class HistoryListbox:
    _history_view = None
    
    # Tkinter Listbox of played video with time of last playback
    _history_listbox = None

    def __init__(self, tk_notebook):
        
        self._history_view = tk.Frame(
            tk_notebook, background=UI_BACKGROUND_COLOR)
        tk_notebook.add(self._history_view, text = "History")

        #self.history_view.grid(row=0, column=0, sticky="news")

        title_history = tk.Label(self._history_view, text="History", font=(
            'calibri', 20), bg=UI_BACKGROUND_COLOR, fg="white")
        title_history.pack(side=tk.TOP, fill=tk.X)

        scrollbar_history = tk.Scrollbar(self._history_view)
        scrollbar_history.pack(side=tk.RIGHT, fill=tk.Y)

        self._history_listbox = tk.Listbox(
            self._history_view, yscrollcommand=scrollbar_history.set, width=100, background=UI_BACKGROUND_COLOR, foreground="white")

        self._history_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        scrollbar_history.config(command=self._history_listbox.yview)

    def get_history_view(self):
        return self._history_view
    
    def get_history_listbox(self):
        return self._history_listbox
    
    def add_entry(self, timestamp, video_name):
        """! Add an entry in the listbox """