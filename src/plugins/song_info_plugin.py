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
from time import sleep, time
from threading import Thread

from colors import *
from logger import PrintTraceInUi
from plugin_base import PluginBase

class SongInfoPlugin(PluginBase):
    """! Plugin to show the song info as it plays """
    frame_songinfo = None
    artist = ""
    song = ""
    is_hiding_info = False
    is_showing_info = False
    timestamp_show_info = 0

    thread_show_info = None
    thread_hide_info = None

# Plugin interface
    def setup(self, **kwargs):
        """! Setup """

        self.thread_show_info = Thread(name="Show song info Thread", target=self._show_song_info_thread)
        self.thread_hide_info = Thread(name="Hide song info Thread", target=self._hide_song_info_thread)

        if super().player_window is None and "player_window" in kwargs:
            super().setup(player_window=kwargs["player_window"])
        
        if "artist" in kwargs and "song" in kwargs:
            artist = kwargs["artist"]
            song = kwargs["song"]
                
            if song is not None and artist is not None:
                # TODO background image maybe ?
                self.frame_songinfo = tk.Frame(self.player_window, width=20, bg=UI_BACKGROUND_COLOR)
                font_size = int(self.player_window.winfo_height() /25);
                PrintTraceInUi("FontSize ", font_size)
                label_artist = tk.Label(self.frame_songinfo,text=artist, padx=10, pady=10, font=('calibri', font_size, 'bold'),fg="white", bg=UI_BACKGROUND_COLOR)
                label_song   = tk.Label(self.frame_songinfo,text=song, padx=10, pady=10, font=('calibri', font_size),fg="white", bg=UI_BACKGROUND_COLOR)
                
                label_artist.pack(side=tk.LEFT)
                label_song.  pack(side=tk.RIGHT)
        
        if self.maintenance_frame is None and "maintenance_frame" in kwargs:
            PrintTraceInUi("Link maintenance window to us")
            super().setup(maintenance_frame=kwargs["maintenance_frame"])
            PrintTraceInUi("Setup")
            self.maintenance_song_info_frame = tk.Frame(self.maintenance_frame,  bg=UI_BACKGROUND_COLOR)
            self.maintenance_song_info_frame.pack(fill=tk.BOTH, expand=True)

            # Provides a button to show the song info manually
            def button_show_song_info():
                if self.frame_songinfo is not None:
                    if not self.is_showing_info:
                        if self.thread_show_info.is_alive():
                            self.thread_show_info.join(timeout=0.1)
                        self.thread_show_info.start()
                    else:
                        PrintTraceInUi("It is already showing !")
                else:
                    PrintTraceInUi("Song info frame is not ready")


            self.show_button = tk.Button(self.maintenance_song_info_frame, text="Show song info", font=('calibri', 11),fg="white",
                bg=UI_BACKGROUND_COLOR, command=button_show_song_info)
            self.show_button.pack()

            
    
    def on_begin(self):
        """! Called at the beginning of a video playback """

    def on_progress(self, time_s):
        """! Called every second of a video playback """
        if self.frame_songinfo is not None:
            # And it stays only for 10 seconds
            if time_s == 10 and not self.is_showing_info:
                PrintTraceInUi("Showing song info")
                if self.thread_hide_info.is_alive():
                    self.thread_hide_info.join()
                self.thread_show_info.start()

            if time() - self.timestamp_show_info > 10 and self.is_showing_info and not self.is_hiding_info:
                PrintTraceInUi("Hiding song info")
                if self.thread_show_info.is_alive():
                    self.thread_show_info.join()
                self.thread_hide_info.start()

    def on_exit(self):
        """! Called at the end of a video playback """
        
        # If we didnt have time to delete the frame info, we do it now to prevent future weird behaviours
        if self.frame_songinfo is not None:
            PrintTraceInUi("Warning ! Deleting song info lately")
            self.frame_songinfo.destroy()
            self.frame_songinfo = None

    def is_maintenance_frame(self):
        """! Returns if the plugins has a maintenance frame """
        # Yes, we give to the user options to show manually the current song info, if available

        return True

    def get_name(self):
        return "Song info"
# Keep parent's on_destroy

# Private functions
    def _show_song_info_thread(self):
        """! Thread to handle the display of the song info pane """
        self.is_showing_info = True
        self.timestamp_show_info = time()
        for x in range(-500, 50, 5):
            if not self.is_running:
                break
            self.frame_songinfo.place(x=x, rely= 0.8)
            sleep(0.01)

    def _hide_song_info_thread(self):
        """! Thread to handle the end of display of the song info pane """
        self.is_hiding_info = True
        for x in range(50, -500, -5):
            if not self.is_running:
                break
            self.frame_songinfo.place(x=x, rely= 0.8)
            sleep(0.01)
        #self.frame_songinfo.destroy()
        #self.frame_songinfo = None
        self.is_hiding_info = False
        self.is_showing_info = False
        self.timestamp_show_info = 0