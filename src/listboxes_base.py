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
import math

from colors import *
from logger import PrintTraceInUi

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


class BasePagingList:
    """! 
        It doesnt work to add custom frames in a listbox entry.
        This is a list that works with pages, and buttons to get to the next page and return to the last page

        Entries are simply packed on each other for each page
    """
    _view = None
    _listbox = None
    button_next = None
    button_previous = None

    all_elements = []
    nb_elements_by_page = 0
    current_page = 1

    def __init__(self, tk_frame, title, nb_elements = 10):
        """! Initialize the listbox 
            @param tk_frame : the tkinter frame in which add the listbox
            @param nb_elements : the max nb_elements to be displayed at once
        """
        self._view = tk.Frame(
            tk_frame, background=UI_BACKGROUND_COLOR, height = nb_elements)

        _title = tk.Label(self._view, text=title, font=(
            'calibri', 20), bg=UI_BACKGROUND_COLOR, fg="white")
        _title.pack(side=tk.TOP, fill=tk.X)
        self._listbox = tk.Frame(self._view, width=100, height = nb_elements,
                                                     background=UI_BACKGROUND_COLOR)

        self._listbox.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.nb_elements_by_page = nb_elements

        change_page_pane = tk.Frame(self._view, bg=UI_BACKGROUND_COLOR)
        change_page_pane.pack(side=tk.LEFT, fill=tk.Y)
        self.button_next = tk.Button(change_page_pane, text="+", command=self.get_next_page, fg="white", bg=UI_BACKGROUND_COLOR)
        self.button_previous = tk.Button(change_page_pane, text="-", command=self.get_previous_page, fg="white", bg=UI_BACKGROUND_COLOR)
        
        self.button_next.pack(side=tk.TOP, expand=True)
        self.button_previous.pack(side=tk.BOTTOM, expand=True)

        self._view.pack(expand=True, fill=tk.BOTH)
        

    def get_next_page(self):
        
        PrintTraceInUi(f"Button next page")
        if len(self.all_elements) < self.nb_elements_by_page:
            PrintTraceInUi(f"Not enough elements to enable paging")
            return

        begin_index_elements_to_hide = (self.current_page-1)*self.nb_elements_by_page
        end_index_elements_to_hide   = min(self.current_page*self.nb_elements_by_page, len(self.all_elements))
        PrintTraceInUi(f"Hiding elements {begin_index_elements_to_hide} to {end_index_elements_to_hide}")

        for element in self.all_elements[begin_index_elements_to_hide:end_index_elements_to_hide]:
            element.pack_forget()

        nb_pages = math.ceil(len(self.all_elements) / self.nb_elements_by_page)
        PrintTraceInUi(f"Nb pages = {nb_pages} - current page = {self.current_page}")
        self.current_page = (self.current_page % nb_pages) + 1
        PrintTraceInUi(f"current page = {self.current_page}")


        begin_index_elements_to_show = (self.current_page-1)*self.nb_elements_by_page
        end_index_elements_to_show   = min(self.current_page*self.nb_elements_by_page, len(self.all_elements))
        PrintTraceInUi(f"Showing elements {begin_index_elements_to_show} to {end_index_elements_to_show}")
        
        for element in self.all_elements[begin_index_elements_to_show:end_index_elements_to_show]:
            element.pack(fill=tk.X)

    def get_previous_page(self):
        PrintTraceInUi(f"Button previous page")
        if len(self.all_elements) < self.nb_elements_by_page:
            PrintTraceInUi(f"Not enough elements to enable paging")
            return

        begin_index_elements_to_hide = (self.current_page-1)*self.nb_elements_by_page
        end_index_elements_to_hide   = min(self.current_page*self.nb_elements_by_page, len(self.all_elements))
        PrintTraceInUi(f"Hiding elements {begin_index_elements_to_hide} to {end_index_elements_to_hide}")

        for element in self.all_elements[begin_index_elements_to_hide:end_index_elements_to_hide]:
            element.pack_forget()

        nb_pages = math.ceil(len(self.all_elements) / self.nb_elements_by_page)
        self.current_page = self.current_page - 1
        if self.current_page == 0:
            self.current_page = nb_pages

        begin_index_elements_to_show = (self.current_page-1)*self.nb_elements_by_page
        end_index_elements_to_show   = min(self.current_page*self.nb_elements_by_page, len(self.all_elements))
        PrintTraceInUi(f"Showing elements {begin_index_elements_to_show} to {end_index_elements_to_show}")
        
        for element in self.all_elements[begin_index_elements_to_show:end_index_elements_to_show]:
            element.pack(fill=tk.X)


    def add_entry(self, type, **kwargs):
        """! Add an entry in the listbox """
        entry = type(self._listbox, bg=UI_BACKGROUND_COLOR, height=100)
        entry.setup(**kwargs)

        # if on current page, pack it
        if (self.current_page-1)*self.nb_elements_by_page <= len(self.all_elements) and self.current_page*self.nb_elements_by_page > len(self.all_elements):
            entry.pack(fill=tk.X)

        self.all_elements.append(entry)