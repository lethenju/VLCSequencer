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

"""! Handles the message listbox """
import tkinter as tk
import math

from colors import *
from logger import PrintTraceInUi
from listboxes_base import BasePagingList

class MessageListboxEntry(tk.Frame):
    """! Represents an entry in the message list view."""
    timestamp_label = None
    author_label  = None
    message_label  = None
    button_toggle_active = None

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.timestamp_label = tk.Label(self, font=(
            'calibri', 11), bg=UI_BACKGROUND_COLOR, fg="white")
        self.timestamp_label.pack(side=tk.LEFT, expand=False)

        self.author_label = tk.Label(self,  font=(
            'calibri', 11, 'bold'), bg=UI_BACKGROUND_COLOR, fg="white")
        self.author_label.pack(side=tk.LEFT, expand=False, padx = 10)

        self.message_label = tk.Label(self,  font=(
            'calibri', 11, 'bold'), bg=UI_BACKGROUND_COLOR, fg="white")
        self.message_label.pack(side=tk.LEFT, expand=False, padx = 10)

        self.button_toggle_active = tk.Button(self, text="Active",  font=(
            'calibri', 11, 'bold'), bg=UI_BACKGROUND_COLOR, fg="white")
        self.button_toggle_active.pack(side=tk.RIGHT, expand=False, padx = 10)

    def setup(self, timestamp, author, message, active_cb, current_cb, activate_toggle_cb):
        """! Setup the widget with the timestamp and video_name """
        PrintTraceInUi("Message list entry ", timestamp, " - ", author, " : ", message)

        self.timestamp_label.configure(text=timestamp)
        self.author_label.configure(text=author)
        self.message_label.configure(text=message)

        active_cb(self.message_active_callback)
        current_cb(self.message_current_callback)

        self.button_toggle_active.configure(command=activate_toggle_cb)

    def message_active_callback(self, is_active):
        PrintTraceInUi(f"Is this message active : {is_active}")
        if is_active:
            super().configure(bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
            self.timestamp_label.configure(bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
            self.author_label.configure(bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
            self.message_label.configure(bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
            self.button_toggle_active.configure(text="Deactivate")
        else:
            super().configure(bg=UI_BACKGROUND_COLOR)
            self.timestamp_label.configure(bg=UI_BACKGROUND_COLOR)
            self.author_label.configure(bg=UI_BACKGROUND_COLOR)
            self.message_label.configure(bg=UI_BACKGROUND_COLOR)
            self.button_toggle_active.configure(text="Activate")

    def message_current_callback(self, is_current):
        PrintTraceInUi(f"Is this message current : {is_current}")
        if is_current:
            super().configure(bg=UI_BLOCK_REPEAT_VIDEO_COLOR)
            self.timestamp_label.configure(bg=UI_BLOCK_REPEAT_VIDEO_COLOR)
            self.author_label.configure(bg=UI_BLOCK_REPEAT_VIDEO_COLOR)
            self.message_label.configure(bg=UI_BLOCK_REPEAT_VIDEO_COLOR)
        else:
            super().configure(bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
            self.timestamp_label.configure(bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
            self.author_label.configure(bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
            self.message_label.configure(bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)

    def destroy(self):
        self.timestamp_label.pack_forget()
        self.author_label.pack_forget()
        self.message_label.pack_forget()

        self.timestamp_label.destroy()
        self.author_label.destroy()
        self.message_label.destroy()

class MessageListbox(BasePagingList):

    def __init__(self, tk_frame, nb_elements = 10):
        """! Initialize the listbox
            @param tk_frame : the tkinter frame in which add the listbox
            @param nb_elements : the max nb_elements to be displayed at once
        """
        super().__init__(tk_frame, "Messages", nb_elements)

    def add_entry(self, timestamp, author, message, active_cb, current_cb, activate_toggle_cb):
        """! Adds an entry in the message list
            @param timestamp : Time of the message arrival in float as returned by time()
            @param Author : Author of the message
            @param message : Message in itself
            @param active_cb : A callback that stores a entry-defined callback in the caller
                                Args : active_cb( callback )
                                    And this param will be the one actually called :
                                        -> callback that is called when the 'active' state changes
                                        (an active message is a message that is programmed to show on the screen)
            @param current_cb : Same but for the 'current' state changes : the message is shown on the screen or not
            @param activate_toggle_cb : Simpler callback (direct callback) for when the user presses the activate/deactivate button on each row
        """
        super().add_entry(MessageListboxEntry,
                          timestamp=timestamp,
                          author=author,
                          message=message,
                          active_cb=active_cb,
                          current_cb=current_cb,
                          activate_toggle_cb=activate_toggle_cb)

