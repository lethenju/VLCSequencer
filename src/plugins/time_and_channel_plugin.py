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
from time import strftime
from PIL import Image, ImageTk


from colors import *
from logger import print_trace_in_ui
from plugin_base import PluginBase


PATH_LOGO_PNG = "PathLogoPng"

class TimeAndChannelPlugin(PluginBase):
    """! Plugin to show the song info as it plays """
    frame_time_channel = None

    font_size = 0       # Stored font size, update if the window height changes
    label_time = None   # Label of the current time

# Plugin interface
    def setup(self, **kwargs):
        """! Setup """

        if super().player_window is None and "player_window" in kwargs:
            super().setup(player_window=kwargs["player_window"])

            self.frame_time_channel = tk.Frame(self.player_window, width=20, bg=UI_BACKGROUND_COLOR)
            self.font_size = int(self.player_window.winfo_height() /30);
            self.label_time = tk.Label(self.frame_time_channel,text="00:00", padx=2, pady=2, font=('calibri', self.font_size, 'bold'),fg="white", bg=UI_BACKGROUND_COLOR)
            self.label_time.pack(side=tk.LEFT)
            self.frame_time_channel.place(relx = 0.85, rely = 0.06)

            if PATH_LOGO_PNG in self.params:
                try:
                    display = ImageTk.PhotoImage(Image.open(self.params[PATH_LOGO_PNG]))

                    self.label_channel = tk.Label(self.frame_time_channel, image=display)
                    self.label_channel.image = display
                    self.label_channel.pack(side=tk.RIGHT)
                except:
                    print_trace_in_ui(f"ERR No such file or directory : ", self.params[PATH_LOGO_PNG])

            print("Show")
    def on_begin(self):
        """! Called at the beginning of a video playback """

    def on_progress(self, time_s):
        """! Called every second of a video playback """
        if self.frame_time_channel is not None:
            # TODO Update time
            new_font_size = int(self.player_window.winfo_height() /25);
            if new_font_size != self.font_size:
                print_trace_in_ui("Update font size from ", self.font_size, " to ", new_font_size)
                self.font_size = new_font_size
                self.label_time.configure(font=('calibri', self.font_size, 'bold'))

            self.label_time.configure(text=strftime('%H:%M'))
            self.frame_time_channel.place(relx = 0.85, rely = 0.06)

    def on_exit(self):
        """! Called at the end of a video playback """

    def is_maintenance_frame(self):
        """! Returns if the plugins has a maintenance frame """
        # No maintenance frame for this plugin, as for now
        return False

    def get_name(self):
        return "Time and Channel"

    def on_destroy(self):
        super().on_destroy()

