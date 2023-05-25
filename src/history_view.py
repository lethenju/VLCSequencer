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

from colors import *
from logger import PrintTraceInUi
from listboxes_base import BasePagingList

class HistoryListboxEntry(tk.Frame):
    """! Represents an entry in the history list view."""
    timestamp_label = None
    video_name_label = None

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.timestamp_label = tk.Label(self, font=(
            'calibri', 11, 'bold'), bg=UI_BACKGROUND_COLOR, fg="white")
        self.timestamp_label.pack(side=tk.LEFT, expand=False)

        self.video_name_label = tk.Label(self,  font=(
            'calibri', 11), bg=UI_BACKGROUND_COLOR, fg="white")
        self.video_name_label.pack(side=tk.RIGHT, expand=True)

    def setup(self, timestamp, video_name):
        """! Setup the widget with the timestamp and video_name """
        PrintTraceInUi("History list entry ", timestamp, " - ", video_name)

        self.timestamp_label.configure(text=timestamp)
        self.video_name_label.configure(text=video_name)

    def destroy(self):
        self.timestamp_label.pack_forget()
        self.video_name_label.pack_forget()

        self.timestamp_label.destroy()
        self.video_name_label.destroy()

class HistoryListbox(BasePagingList):
    def __init__(self, tk_notebook, nb_elements = 10):
        """! Initialize the listbox
            @param tk_notebook : the tk notebook in which add the listbox
            @param nb_elements : the max nb_elements to be displayed at once
        """
        super().__init__(tk_notebook, "History", nb_elements)
        tk_notebook.add(self._view, text = "History")

    def add_entry(self, timestamp, video_name):
        """! Add an entry in the HistoryListboxEntry """
        super().add_entry(HistoryListboxEntry, timestamp=timestamp, video_name=video_name)
