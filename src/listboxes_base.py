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

class BaseListbox:
    _view = None
    _listbox = None

    def __init__(self, tk_frame, title,  nb_elements = 10):
        """! Initialize the listbox 
            @param tk_frame : the tkinter frame in which add the listbox
            @param nb_elements : the max nb_elements to be displayed at once
        """
        self._view = tk.Frame(
            tk_frame, background=UI_BACKGROUND_COLOR, height = nb_elements)

        _title = tk.Label(self._view, text=title, font=(
            'calibri', 20), bg=UI_BACKGROUND_COLOR, fg="white")
        _title.pack(side=tk.TOP, fill=tk.X)

        _scrollbar = tk.Scrollbar(self._view)
        _scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._listbox = tk.Listbox(
            self._view, yscrollcommand=_scrollbar.set, width=100, height = nb_elements,
                                                     background=UI_BACKGROUND_COLOR, foreground="white")

        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        _scrollbar.config(command=self._listbox.yview)

    def get_view(self):
        return self._view
    
    def get_listbox(self):
        return self._listbox
    
    def add_entry(self):
        """! Add an entry in the listbox  : base implementation """
        print("BASE CLASS - SHOULD NOT BE CALLED")
        assert(0)
