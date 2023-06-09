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
"""! Ui Player 
     Displays the videos and different plugins overlays
"""
import tkinter as tk
import threading
import time
import sys

# Application related imports
from colors import UI_BACKGROUND_COLOR
from logger import print_trace_in_ui

class UiPlayer():
    """! Main UI Window

        Display the videos in 2 separate frames
        One frame is hidden while the other displays the video
        At the end of a video, the other frame gets the new video and the other frame gets hidden
        But the video playback of the first video is still going.
        This enable the audio crossfade capabilities

        In the future, different transitions may be added to the program, even visual ones.
    """
    # Main window
    window = None

    is_fullscreen_flag = False  # True if this window is in fullscreen on the main monitor
    is_running_flag = False     # Flag to kill application carefully
    is_muted = False

    vlc_instance = None
    metadata_manager = None
    plugin_manager = None
    nb_video_played = 0
    is_next_asked = False
    is_paused = False

    fade_out_thread = None
    fade_in_thread  = None
    fade_out_thread_active = False
    fade_in_thread_active  = False

    class MediaFrame:
        """! Structure that links a Tkinter frame with a Vlc media player """
        media_player = None  # A Vlc media player
        ui_frame = None     # Tkinter frame

        def __init__(self, media_player, ui_frame):
            self.media_player = media_player
            self.ui_frame = ui_frame

    media_frames = None  # List (tuple) of media frames

    def __init__(self, tkroot, vlc_instance, metadata_manager, plugin_manager):
        """! Initialize the main display window """
        # Main window initialisation
        self.window = tkroot
        self.window.title("MainUI")
        self.window.geometry("400x300")
        self.vlc_instance = vlc_instance
        self.metadata_manager = metadata_manager
        self.plugin_manager = plugin_manager

        self.is_next_asked = False
        self.is_paused = False
        self.nb_video_played = 0

        self.fade_out_thread_active = False
        self.fade_in_thread_active = False
        # 2 players (one for each frame)
        # Initialize media frames with the players and new tk frames.
        self.media_frames = (self.MediaFrame(self.vlc_instance.media_player_new(),
                                             tk.Frame(self.window,
                                                      bg=UI_BACKGROUND_COLOR,
                                                      width=200,
                                                      height=150)),
                             self.MediaFrame(self.vlc_instance.media_player_new(),
                                             tk.Frame(self.window,
                                                      bg=UI_BACKGROUND_COLOR,
                                                      width=200,
                                                      height=150)))
        for i, _ in enumerate(self.media_frames):
            self.media_frames[i].ui_frame.pack(fill="both", expand=True)

        def toggle_full_screen(*unused):
            self.window.attributes("-fullscreen", not self.is_fullscreen_flag)
            self.is_fullscreen_flag = not self.is_fullscreen_flag
        self.window.bind("<F11>", toggle_full_screen)
        self.is_running_flag = True

    def _play_on_specific_frame(self, media, index_media_players, length_s,
                                metadata = None):
        """! Main play function.
            @param media : The Vlc Media instance
            @param index_media_players the index of the media frame to use this time

            Handles audio crossfading and frame switching accordingly
        """
        if metadata is None:
            begin_s=0
            end_s=0
            fade_in=False
            fade_out=False
            artist=None
            song=None
        else:
            begin_s=metadata.timestamp_begin
            end_s=metadata.timestamp_end
            fade_in=metadata.fade_in
            fade_out=metadata.fade_out
            artist=metadata.artist
            song=metadata.song

        # Getting simpler name from now on
        frame = self.media_frames[index_media_players].ui_frame
        player = self.media_frames[index_media_players].media_player

        player.set_media(media)
        self.window.after(
            0, lambda: self.media_frames[1 - index_media_players].ui_frame.pack_forget())
        self.window.after(0, lambda: frame.pack(fill="both", expand=True))

        window_handle = frame.winfo_id()
        if sys.platform.startswith('win'):
            player.set_hwnd(window_handle)
        else:
            player.set_xwindow(window_handle)

        # Setup the plugins
        for plugin in self.plugin_manager.get_plugins():
            plugin.setup(player_window = self.window, artist=artist, song=song)

        if end_s == 0:
            end_s = length_s
        player.play()

        player.set_position(begin_s/length_s)

        def fade_in_thread():
            """! Thread to handle fade in on this player"""
            # The playing video musnt change during the thread !
            self.fade_in_thread_active = True
            nb_video_played = self.nb_video_played

            player.audio_set_volume(0)
            # Let some time for the vlc instance to set the volume. Fixes high volume spikes
            time.sleep(0.5)

            volume = player.audio_get_volume()
            while (volume < 100 and self.is_running_flag and not self.is_next_asked
                   and nb_video_played < self.nb_video_played + 1):
                print_trace_in_ui("fade_in Volume : ", volume)
                volume = min(volume + 5, 100)
                if not self.is_muted:
                    player.audio_set_volume(volume)
                while self.is_paused:
                    # Waiting to get out of pause
                    time.sleep(1)
                time.sleep(0.5)
            self.fade_in_thread_active = False

        def fade_out_thread():
            """! Thread to handle fade out on this player"""
            # The playing video musnt change twice during the thread !
            self.fade_out_thread_active = True
            nb_video_played = self.nb_video_played
            volume = player.audio_get_volume()
            while (volume > 0 and self.is_running_flag and not self.is_next_asked
                   and self.nb_video_played - nb_video_played < 2):
                volume = volume - 5
                player.audio_set_volume(volume)
                while self.is_paused:
                    # Waiting to get out of pause
                    time.sleep(1)
                time.sleep(0.5)
            # If we changed 2 times of videos, we're on this player, we better not stop it
            if self.nb_video_played - nb_video_played != 2:
                player.stop()
                self.fade_out_thread_active = False

        # We shouldnt launch multiple concurrent fade_in
        if fade_in and not self.fade_in_thread_active:
            self.fade_in_thread = threading.Thread(name="FadeIn Thread", target=fade_in_thread)
            self.fade_in_thread.start()
        elif not self.is_muted:
            player.audio_set_volume(100)

        # Fix : If the end is the actual end, we may never reach it.
        if end_s != length_s:
            end_position = end_s/length_s
        else:
            end_position = 0.95


        for plugin in self.plugin_manager.get_plugins():
            plugin.on_begin()

        timer = 0
        while (player.get_position() < end_position and \
              self.is_running_flag and not self.is_next_asked):
            print_trace_in_ui("Current media playing time " +
                           ("{:.2f}".format(player.get_position()*100))+"%")
            # Progress the plugins
            for plugin in self.plugin_manager.get_plugins():
                plugin.on_progress(timer)

            if (player.get_position() < 0):
                # Problem on the video
                player.stop()
                self.is_next_asked = True
                break
            time.sleep(1)
            timer = timer + 1

        print_trace_in_ui("End of video")

        for plugin in self.plugin_manager.get_plugins():
            plugin.on_exit()

        # We shouldnt launch multiple concurrent fade_out
        if fade_out and not self.fade_out_thread_active:
            self.fade_out_thread = threading.Thread(name="FadeOut Thread", target=fade_out_thread)
            self.fade_out_thread.start()
        else:
            player.audio_set_volume(0)

        if not self.is_running_flag:
            print_trace_in_ui("Stopping UI_Player ")
            if self.fade_in_thread is not None and self.fade_in_thread.is_alive():
                self.fade_in_thread.join()
            if self.fade_out_thread is not None and self.fade_out_thread.is_alive():
                self.fade_out_thread.join()

        self.is_next_asked = False


    def play(self, path, length_s):
        """! Main play API

            @param path : Path to the video file to play
        """
        if self.is_running_flag:

            media = self.vlc_instance.media_new(path)

            self.nb_video_played = self.nb_video_played + 1

            print_trace_in_ui("Total video played ",self.nb_video_played)
            print_trace_in_ui("Playing on frame number ",self.nb_video_played % 2)

            # Try to get metadata about this video
            name_of_file = path.split("/").pop()
            metadata = None
            if self.metadata_manager is not None:
                metadata = self.metadata_manager.get_metadata(
                    video_name=name_of_file)
            if metadata is not None:
                self._play_on_specific_frame(media, index_media_players=self.nb_video_played % 2,
                                             length_s=length_s,
                                             metadata=metadata)
            else:
                self._play_on_specific_frame(
                    media, index_media_players=self.nb_video_played % 2,  length_s=length_s)

    def _get_active_media_player(self):
        """! Get the active player object """
        return self.media_frames[self.nb_video_played % 2].media_player

    def pause_resume(self):
        """! Toggle play/pause state of the ui_player
             doesnt affect plugins
        """
        self.is_paused = not self.is_paused
        player = self._get_active_media_player()
        player.pause()

    def mute_trigger(self):
        """! Toggle mute level
             FIXME isnt working properly
        """
        player = self._get_active_media_player()
        if player.audio_get_volume() != 0:
            self.is_muted = True
            player.audio_set_volume(0)
        else:
            self.is_muted = False
            player.audio_set_volume(100)

    def next(self):
        """! Asks to move to the next video now"""
        self.is_next_asked = True

    def kill(self):
        """! Kill the window and release the vlc instance """
        self.is_running_flag = False
        time.sleep(1) # Wait for all processes to stop
        self.vlc_instance.release()
