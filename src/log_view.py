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
from logger import PrintTraceInUi, LoggerSubscribeUI
from listboxes_base import BaseListbox

class LogListbox(BaseListbox):

    def __init__(self, tk_notebook, nb_elements = 10):
        """! Initialize the listbox 
            @param tk_notebook : the tk notebook in which add the listbox
            @param nb_elements : the max nb_elements to be displayed at once
        """
        super().__init__(tk_notebook, "Logs", nb_elements)
        tk_notebook.add(super().get_view(), text = "Logs")
        LoggerSubscribeUI(super().get_listbox())
