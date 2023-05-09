
import tkinter as tk
from time import sleep
from threading import Thread

from colors import *
from logger import PrintTraceInUi
from plugin_base import PluginBase

class SongInfoPlugin(PluginBase):
    """! Plugin to show the song info as it plays """
    frame_songinfo = None
    artist = ""
    song = ""

# Plugin interface
    def setup(self, **kwargs):
        """! Setup """
        if super().player_window is None and "player_window" in kwargs:
            super().setup(player_window=kwargs["player_window"])
        elif "artist" in kwargs and "song" in kwargs:
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
    
    def on_begin(self):
        """! Called at the beginning of a video playback """

    def on_progress(self, time_s):
        """! Called every second of a video playback """
        if self.frame_songinfo is not None:
            # And it stays only for 10 seconds
            if time_s == 10:
                PrintTraceInUi("Showing song info")
                Thread(target=self._show_song_info_thread).start()
            if time_s == 20:
                PrintTraceInUi("Hiding song info")
                Thread(target=self._hide_song_info_thread).start()

    def on_exit(self):
        """! Called at the end of a video playback """
        
        # If we didnt have time to delete the frame info, we do it now to prevent future weird behaviours
        if self.frame_songinfo is not None:
            PrintTraceInUi("Warning ! Deleting song info lately")
            self.frame_songinfo.destroy()
            self.frame_songinfo = None

    def get_name(self):
        return "song_info"
# Keep parent's on_destroy

# Private functions
    def _show_song_info_thread(self):
        """! Thread to handle the display of the song info pane """
        for x in range(-500, 50, 5):
            if not self.is_running:
                break
            self.frame_songinfo.place(x=x, rely= 0.8)
            sleep(0.01)

    def _hide_song_info_thread(self):
        """! Thread to handle the end of display of the song info pane """
        for x in range(50, -500, -5):
            if not self.is_running:
                break
            self.frame_songinfo.place(x=x, rely= 0.8)
            sleep(0.01)
        self.frame_songinfo.destroy()
        self.frame_songinfo = None