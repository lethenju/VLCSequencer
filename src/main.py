
import vlc
import tkinter as tk
from tkinter import filedialog
import threading
import os
import time
import magic
import csv
import random
import sys
import argparse
import xml.etree.ElementTree as ET
import copy
import inspect
from datetime import datetime

# Application related imports
from colors import *
from song_info_plugin import SongInfoPlugin

# Reference to the tkinter listbox used to gather the logs
# TODO have a static module for that, and subscribe a listbox instead of relying on this one
ui_trace_listbox = None


def PrintTraceInUi(*args):
    function_caller_name = inspect.stack()[1].function
    trace = time.strftime('%H:%M:%S') + " " + function_caller_name + "() : "
    for arg in args:
        trace = trace + arg.__str__()
    print(trace)
    if ui_trace_listbox is not None:
        ui_trace_listbox.insert(tk.ANCHOR, " " + trace)
        ui_trace_listbox.yview(tk.END)


class UiPlayer():
    """! Main UI Window

        Display the videos in 2 separate frames
        One frame is hidden while the other displays the video
        At the end of a video, the other frame gets the new video and the other frame gets hidden
        But the video playback of the first video is still going. This enable the audio crossfade capabilities

        In the future, different transitions may be added to the program, even visual ones.
    """
    # Main window
    window = None

    is_fullscreen_flag = False  # True if this window is in fullscreen on the main monitor
    is_running_flag = False     # Flag to kill application carefully
    is_muted = False

    vlc_instance = None
    metadata_manager = None
    nb_video_played = 0
    is_next_asked = False
    is_paused = False

    fade_out_thread_active = False
    fade_in_thread_active = False

    class MediaFrame:
        """! Structure that links a Tkinter frame with a Vlc media player """
        media_player = None  # A Vlc media player
        ui_frame = None     # Tkinter frame

        def __init__(self, media_player, ui_frame):
            self.media_player = media_player
            self.ui_frame = ui_frame

    media_frames = None  # List (tuple) of media frames
    plugins = []
    #frame_songinfo = None # UI Frame of the song information (artist and song name)

    def __init__(self, tkroot, vlc_instance, metadata_manager):
        """! Initialize the main display window """
        # Main window initialisation
        self.window = tkroot
        self.window.title("MainUI")
        self.window.geometry("400x300")
        self.vlc_instance = vlc_instance
        self.metadata_manager = metadata_manager

        self.is_next_asked = False
        self.is_paused = False
        self.nb_video_played = 0

        # TODO Conditionning over a parameter
        self.plugins.append(SongInfoPlugin(self.window))

        self.fade_out_thread_active = False
        self.fade_in_thread_active = False
        # 2 players (one for each frame)
        # Initialize media frames with the players and new tk frames.
        self.media_frames = (self.MediaFrame(self.vlc_instance.media_player_new(),
                                             tk.Frame(self.window, bg=UI_BACKGROUND_COLOR, width=200, height=150)),
                             self.MediaFrame(self.vlc_instance.media_player_new(),
                                             tk.Frame(self.window, bg=UI_BACKGROUND_COLOR, width=200, height=150)))
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

        h = frame.winfo_id()
        if sys.platform.startswith('win'):
            player.set_hwnd(h)
        else:
            player.set_xwindow(h)
        
        # Setup the plugins
        for plugin in self.plugins:
            plugin.setup(artist, song)

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
                PrintTraceInUi("fade_in Volume : ", volume)
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
                   and nb_video_played < self.nb_video_played + 1):
                PrintTraceInUi("fade_out Volume : ", volume)
                volume = volume - 5
                player.audio_set_volume(volume)
                while self.is_paused:
                    # Waiting to get out of pause
                    time.sleep(1)
                time.sleep(0.5)
            # TODO debug when skipping quickly
            # If we changed 2 times of videos, we're on this player, we better not stop it
            # if not nb_video_played < self.nb_video_played + 1:
            player.stop()
            self.fade_out_thread_active = False
            
        # We shouldnt launch multiple concurrent fade_in
        if fade_in and not self.fade_in_thread_active:
            threading.Thread(target=fade_in_thread).start()
        elif not self.is_muted:
            player.audio_set_volume(100)

        # Fix : If the end is the actual end, we may never reach it.
        if end_s != length_s:
            end_position = end_s/length_s
        else:
            end_position = 0.95


        for plugin in self.plugins:
            plugin.on_begin()

        timer = 0
        while (player.get_position() < end_position and self.is_running_flag and not self.is_next_asked):
            PrintTraceInUi("Current media playing time " +
                           ("{:.2f}".format(player.get_position()*100))+"%")
            # Progress the plugins
            for plugin in self.plugins:
                plugin.on_progress(timer)

            if (player.get_position() < 0):
                # Problem on the video
                player.stop()
                self.is_next_asked = True
                break
            time.sleep(1)
            timer = timer + 1

        for plugin in self.plugins:
            plugin.on_exit()

        # We shouldnt launch multiple concurrent fade_out
        if fade_out and not self.fade_out_thread_active:
            threading.Thread(target=fade_out_thread).start()
        else:
            player.audio_set_volume(0)

        self.is_next_asked = False

    def play(self, path, length_s):
        """! Main play API

            @param path : Path to the video file to play
        """
        if self.is_running_flag:

            media = self.vlc_instance.media_new(path)

            self.nb_video_played = self.nb_video_played + 1

            PrintTraceInUi("Total video played ",self.nb_video_played)
            PrintTraceInUi("Playing on frame number ",self.nb_video_played % 2)

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
        # Get the active player
        return self.media_frames[self.nb_video_played % 2].media_player

    def pause_resume(self):
        self.is_paused = not self.is_paused
        player = self._get_active_media_player()
        player.pause()
        pass

    def mute_trigger(self):
        player = self._get_active_media_player()
        if player.audio_get_volume() != 0:
            self.current_volume = player.audio_get_volume()
            self.is_muted = True
            player.audio_set_volume(0)
        else:
            self.is_muted = False
            player.audio_set_volume(self.current_volume)

    def next(self):
        self.is_next_asked = True

    def kill(self):
        """! Kill the window and release the vlc instance """
        self.is_running_flag = False
        self.window.destroy()
        self.vlc_instance.release()


class MainSequencer():
    """! Handle the sequencing of videos to be played back """

    is_running_flag = False
    ui_player = None
    ui_sequencer = None
    thread = None

    def __init__(self, ui_player, ui_sequencer):
        self.ui_player = ui_player
        self.ui_sequencer = ui_sequencer

    # Launch the sequencer thread
    def launch_sequencer(self):
        self.thread = threading.Thread(target=self.sequencer_thread)
        self.is_running_flag = True
        self.thread.start()

    def sequencer_thread(self):
        while (self.is_running_flag):
            (path, length_s) = self.ui_sequencer.get_next_video()
            self.ui_player.play(path=path, length_s=length_s)

    def kill(self):
        self.is_running_flag = False
        self.ui_player.kill()


class SequenceBlock:
    """! Describe a sequence block : a video or a block of videos

    Used by the Sequence loader to read the sequence description file and flatten
    the description loops, resolve random videos. Used afterward as the main sequence, 
    with its UI and block logic"""

    inner_sequence = []
    block_type = None
    block_args = None
    ui_frame = None
    ui_playing_time = None
    ui_video_frame = None
    ui_label = None
    ui_id_label = None
    ui_artist_label = None
    ui_song_label = None
    last_playback = 0

    def __init__(self, block_type, block_args=None):
        self.ui_frame = None
        self.ui_playing_time = None
        self.ui_video_frame = None
        self.ui_label = None
        self.ui_id_label = None
        self.ui_artist_label = None
        self.ui_song_label = None
        self.inner_sequence = []
        self.block_type = block_type
        self.block_args = block_args
        last_playback = 0

    def add_block(self, block):
        self.inner_sequence.append(block)

    def get_color(self):
        """! Returns the hex code of the video block """
        bg_color = UI_BLOCK_PLAYED_VIDEO_COLOR

        if self.block_type == "randomvideo":
            bg_color = UI_BLOCK_RANDOM_VIDEO_COLOR
        elif self.block_type == "video":
            bg_color = UI_BLOCK_NORMAL_VIDEO_COLOR
        return bg_color

    def select(self):
        """! Select the video by putting a different background 
                to the main ui frame of the block
        """
        self.ui_frame.configure(
            bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
        self.ui_playing_time.configure(
            bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)

    def modify_color(self, color):
        """! Modify background colors of the UI elements of the block """
        self.ui_frame.configure(
            bg=UI_BLOCK_USED_VIDEO_FRAME_COLOR)
        self.ui_playing_time.configure(
            bg=UI_BLOCK_USED_VIDEO_FRAME_COLOR)
        self.ui_video_frame.configure(
            bg=color)
        self.ui_label.configure(
            bg=color)
        self.ui_id_label.configure(
            bg=color)
        self.ui_artist_label.configure(
            bg=color)
        self.ui_song_label.configure(
            bg=color)

    def __str__(self):
        if self.block_type == "repeat":
            return "Repeat " + self.block_args + " times"
        if self.block_type == "video":
            return "Video : " + self.block_args
        if self.block_type == "randomvideo":
            return ("RandomVideo from dir : " + self.block_args[0]
                    + " and timeout " + self.block_args[1])
        if self.block_type == "sequence":
            sequence_description = ("Sequence :\n")
            for child in self.inner_sequence:
                sequence_description = sequence_description + child.__str__() + "\n"
            return sequence_description

        if self.block_type is not None:
            return self.block_type
        return "Block unknown .. Error"


class UiSequenceManager:
    """! Reads the sequence description and builds the video sequence 

        Open a UI to visualize and modify the sequence 
    """
    class ListViews:
        history_view = None
        logs_view = None
        # Tkinter Listbox of played video with time of last playback
        history_listbox = None

        def __init__(self, ui_parent):
            global ui_trace_listbox
            listviews = tk.Frame(ui_parent, background=UI_BACKGROUND_COLOR)
            listviews.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=1)
            listviews.columnconfigure(0, weight=1)
            listviews.columnconfigure(1, weight=1)
            listviews.rowconfigure(0, weight=1)

            self.history_view = tk.Frame(
                listviews, background=UI_BACKGROUND_COLOR)

            self.history_view.grid(row=0, column=0, sticky="news")

            title_history = tk.Label(self.history_view, text="History", font=(
                'calibri', 20), bg=UI_BACKGROUND_COLOR, fg="white")
            title_history.pack(side=tk.TOP, fill=tk.X)

            scrollbar_history = tk.Scrollbar(self.history_view)
            scrollbar_history.pack(side=tk.RIGHT, fill=tk.Y)

            self.history_listbox = tk.Listbox(
                self.history_view, yscrollcommand=scrollbar_history.set, width=200, background=UI_BACKGROUND_COLOR, foreground="white")

            self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
            scrollbar_history.config(command=self.history_listbox.yview)

            self.logs_view = tk.Frame(
                listviews, background=UI_BACKGROUND_COLOR)
            self.logs_view.grid(row=0, column=1,  sticky="news")

            title_logs = tk.Label(self.logs_view, text="Logs", font=(
                'calibri', 20), bg=UI_BACKGROUND_COLOR, fg="white")
            title_logs.pack(side=tk.TOP, fill=tk.X)

            scrollbar_logs = tk.Scrollbar(self.logs_view)
            scrollbar_logs.pack(side=tk.RIGHT, fill=tk.Y)

            ui_trace_listbox = tk.Listbox(
                self.logs_view, yscrollcommand=scrollbar_logs.set, width=200, background=UI_BACKGROUND_COLOR, foreground="white")
            ui_trace_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

            scrollbar_logs.config(command=ui_trace_listbox.yview)

    # Reference to the player object to connect the playback buttons to the associated callbacks
    ui_player = None
    # Reference to the metadata API to get the user-defined start/end playback timestamps
    metadata_manager = None
    #  Reference to the Vlc instance to get true metadata about the video (length..)
    vlc_instance = None

    # main Tkinter panes
    main_clock_view = None
    sequence_view = None
    ui_playback_control_view = None

    listviews = None
    # Dictionary of parsed videos
    history_knownvideos = {}
    # Parsed video sequence, as a "sequence" block
    sequence_data = None
    # path of the xml sequence file
    xml_path = ""
    # Sequence title (and so the title of the window)
    title = ""
    path_dirname = ""
    index_playing_video = -1
    is_running_flag = False

    # If the video is in pause, need to recalculate the timestamps every second
    is_paused = False

    def __init__(self, tkroot, vlc_instance, ui_player, path, metadata_manager):
        """! The Sequence manager initializer

            @param path : path the sequence file 
            @return An instance of a UiSequenceManager
        """
        self.ui_player = ui_player
        self.vlc_instance = vlc_instance
        self.metadata_manager = metadata_manager
        self.is_running_flag = True
        self.is_paused = False

        # start UI
        self.ui_sequence_manager = tk.Toplevel(tkroot)
        self.ui_sequence_manager.title("Sequence Manager")

        self.main_clock_view = tk.Frame(
            self.ui_sequence_manager, width=1000, height=200, background=UI_BACKGROUND_COLOR)
        self.main_clock_view.pack(side=tk.TOP,  fill=tk.BOTH)

        lbl = tk.Label(self.main_clock_view, font=(
            'calibri', 60, 'bold'), background=UI_BACKGROUND_COLOR, foreground='white')
        lbl.pack(side=tk.TOP,  fill=tk.BOTH, pady=50)

        # Launch clock thread
        def update_clock():
            while (self.is_running_flag):
                string = time.strftime('%H:%M:%S')
                lbl.config(text=string)
                time.sleep(1)

        threading.Thread(target=update_clock).start()

        self.sequence_view = tk.Frame(
            self.ui_sequence_manager, width=1000, height=500, background=UI_BACKGROUND_COLOR)
        self.sequence_view.pack(side=tk.TOP,  fill=tk.BOTH)

        self.ui_playback_control_view = tk.Frame(
            self.ui_sequence_manager,  width=500,  background=UI_BACKGROUND_COLOR)

        self.pause_button = tk.Button(
            self.ui_playback_control_view, text="Pause/Resume", command=self.pause_resume_callback,
            padx=10, pady=10, font=('calibri', 12),
            fg="white",
            bg=UI_BACKGROUND_COLOR)
        self.mute_button = tk.Button(
            self.ui_playback_control_view, text="Mute/Unmute",  command=self.ui_player.mute_trigger,
            padx=10, pady=10, font=('calibri', 12),
            fg="white",
            bg=UI_BACKGROUND_COLOR)
        self.next_button = tk.Button(
            self.ui_playback_control_view, text="Next",         command=self.ui_player.next,
            padx=10, pady=10, font=('calibri', 12),
            fg="white",
            bg=UI_BACKGROUND_COLOR)

        self.pause_button.grid(column=0, row=0, padx=10, pady=10)
        self.mute_button.grid(column=1, row=0, padx=10, pady=10)
        self.next_button.grid(column=2, row=0, padx=10, pady=10)

        self.ui_playback_control_view.pack(side=tk.TOP,  fill=tk.BOTH)

        self.listviews = self.ListViews(self.ui_sequence_manager)

        # Store file data
        self.xml_path = path
        self.path_dirname = os.path.dirname(path)

    def pause_resume_callback(self):
        self.ui_player.pause_resume()

        if not self.is_paused:
            self.is_paused = True
            # Activate the thread that add a second to the length of the current video

            def current_playing_is_paused_thread():
                while self.is_paused and self.is_running_flag:
                    time.sleep(1)
                    video = self.sequence_data.inner_sequence[self.index_playing_video]
                    video.length = video.length + 1

                    # Changing timestamps for the videos after the current one, if they exists
                    if self.index_playing_video + 1 < len(self.sequence_data.inner_sequence):
                        for i in range(self.index_playing_video + 1, len(self.sequence_data.inner_sequence)):
                            video = self.sequence_data.inner_sequence[i]

                            self.sequence_data.inner_sequence[
                                i].last_playback = self.sequence_data.inner_sequence[i].last_playback+1
                            # self._resolve_timestamps(index=i)

                            ui_playing_label_time = datetime.fromtimestamp(
                                video.last_playback).time()
                            video.ui_playing_time.configure(text="{:02d}".format(ui_playing_label_time.hour) + ":" +
                                                            "{:02d}".format(ui_playing_label_time.minute) + ":" +
                                                            "{:02d}".format(ui_playing_label_time.second))
            threading.Thread(target=current_playing_is_paused_thread).start()
        else:
            self.is_paused = False

    def _get_metadata(self, video_name):
            """! Gets the metadata through the API, wraps the None protection
                @param video_name : name of the video file, key in the metadata dictionary
                @return metadata object if it exists, None otherwise
            """
            metadata = None
            if self.metadata_manager is not None:
                metadata = self.metadata_manager.get_metadata(
                    video_name=video_name)
            return metadata

    def _build_sequence(self, sequence_xml_node, sequence_data_node):
        for child in sequence_xml_node:
            if child.tag == "Repeat":
                nb_times = child.attrib['nb_time']
                block = SequenceBlock("repeat", nb_times)
                self._build_sequence(
                    sequence_xml_node=child, sequence_data_node=block)
                sequence_data_node.add_block(block)
            if child.tag == "Video":
                path = child.attrib['path']
                block = SequenceBlock("video", path)
                sequence_data_node.add_block(block)
            if child.tag == "RandomVideo":
                path = child.attrib['path']
                reselect_timeout = child.attrib['reselect_timeout']
                block = SequenceBlock("randomvideo", (path, reselect_timeout))
                sequence_data_node.add_block(block)

    def _flatten_sequence(self, sequence_data_node):
        """! Resolves the repeat blocks by flattening the loops """
        for i, block in enumerate(sequence_data_node.inner_sequence):
            if (block.block_type == "repeat"):
                for _ in range(int(block.block_args)):
                    for block_child in block.inner_sequence:
                        self._flatten_sequence(block_child)
                        sequence_data_node.inner_sequence.insert(
                            i, copy.copy(block_child))
                block.inner_sequence = None
                sequence_data_node.inner_sequence.remove(block)

    def _find_random_video(self, path, timeout_m, time_programmed_s):
        """! Returns a video in the directory given by the path parameter and that hasnt played for timeout minutes 
          @param path : the path of the directory to search videos in
          @param timeout_m : Timeout of the needed video in minutes : 
                             the video must not be chosen if it has been chosen the last timeout_m minutes
          @param time_programmed_s : Timestamp in the future for the programmed video, when its gonna be played
        """
        # gather list of files
        files = os.listdir(self.path_dirname + "/" + path)
        # List of files that have been played too recently
        forbidden_files = []
        video_found = None

        while video_found is None:
            is_file_selected = False
            while not is_file_selected:
                file = files[random.randrange(len(files))]
                is_file_selected = file not in forbidden_files
            complete_path = self.path_dirname + "/" + path + "/" + file
            PrintTraceInUi("Testing " + complete_path)
            # Verify its a Media file before trying to play it

            if ("Media" in magic.from_file(complete_path)):
                if complete_path in self.history_knownvideos:
                    video = self.history_knownvideos[complete_path]

                    PrintTraceInUi("Already known video... Last playback on ", datetime.fromtimestamp(
                        video.last_playback), " and timeout ", int(timeout_m)*60, "s")
                    PrintTraceInUi(" and timestamp of the programmed video  ",
                                   datetime.fromtimestamp(time_programmed_s))
                    if (video.last_playback + int(timeout_m)*60 < time_programmed_s):
                        video_found = complete_path
                        # Overriding the last playback to now + last programmed videos time
                        self.history_knownvideos[complete_path].last_playback = time_programmed_s
                    else:
                        PrintTraceInUi("Last playback too recent.. ")
                        # Forbid this video to be tested again
                        forbidden_files.append(complete_path)
                        if len(forbidden_files) == len(files):
                            PrintTraceInUi(
                                "ERROR ! All videos are forbidden !! Selecting ", complete_path, " anyway..")
                            video_found = complete_path
                            self.history_knownvideos[complete_path].last_playback = time_programmed_s
                else:
                    # PrintTraceInUi("Unknown video for now, validating playback")
                    video_found = complete_path
            else:
                PrintTraceInUi("Not a video file")
                forbidden_files.append(complete_path)
                if len(forbidden_files) == len(files):
                    PrintTraceInUi("ERROR ! Trying again...")

        return video_found

    def _resolve_timestamps(self, index):

        video = self.sequence_data.inner_sequence[index]
        # Resolves the timestamp in the future where we need to put the video
        time_programmed_s = time.time()

        # We simply need to take the last video timestamp and add it
        if (index > 0):
            # Compute last video length
            path_video = self.sequence_data.inner_sequence[index-1].path

            # Get the metadata to gather the actual programmed playing time of the videos

            metadata = self._get_metadata(path_video.split("/").pop())

            if metadata is not None:
                if metadata.timestamp_end != 0:
                    # If there is a end timestamp, we know the length is end - start
                    playing_length_s = metadata.timestamp_end - metadata.timestamp_begin
                else:
                    # If theres a start we have to get the length and substract
                    playing_length_s = self.history_knownvideos[path_video].length - \
                        metadata.timestamp_begin
            else:
                playing_length_s = self.history_knownvideos[path_video].length

            # New time_programmed is the last playback + the length of the last track
            time_programmed_s = self.sequence_data.inner_sequence[index -
                                                                  1].last_playback + playing_length_s

        video.last_playback = time_programmed_s

    def _resolve_sequence(self):
        """! Chooses the random videos to be displayed, add length for each media and media info to blocks """
        for i, video in enumerate(self.sequence_data.inner_sequence):
            final_path = None

            self._resolve_timestamps(index=i)

            if (video.block_type == "randomvideo"):
                path = video.block_args[0]
                timeout = video.block_args[1]
                final_path = self._find_random_video(
                    path=path, timeout_m=timeout, time_programmed_s=video.last_playback)
                PrintTraceInUi("Video " + final_path + " is programmed to be played on ",
                               datetime.fromtimestamp(video.last_playback))
            elif (video.block_type == "video"):
                final_path = self.path_dirname + "/" + video.block_args

            if not os.path.isfile(final_path):
                PrintTraceInUi(final_path + " : The video doesnt exist ! ")
                exit(-1)

            # Storing path in the block
            video.path = final_path
            if (video.path in self.history_knownvideos):
                video.length = self.history_knownvideos[video.path].length
                PrintTraceInUi(video.path + " : Known video, already parsed length ", video.length)
            else:
                PrintTraceInUi(
                    video.path + " : New video, reading attributes ")
                media = self.vlc_instance.media_new(video.path)
                media.parse_with_options(1, 0)
                # Blocking the parsing time
                while True:
                    if str(media.get_parsed_status()) == 'MediaParsedStatus.done':
                        break
                video.length = media.get_duration()/1000

                # Store video in the dictionary
                self.history_knownvideos[video.path] = copy.copy(video)
                # We do not need this media anymore
                media.release()

            # Split the path and get the name after the last '/' and get the name before the extension
            video.ui_label.configure(
                text=video.path.split("/").pop().split(".")[0])
            
            metadata = self._get_metadata(video.path.split("/").pop())

            if metadata is not None:
                if metadata.artist is not None and metadata.song is not None:
                    video.ui_artist_label.configure(text=metadata.artist)
                    video.ui_artist_label.pack(padx=5, pady=5, fill="both", expand=True)
                    video.ui_song_label.configure(text=metadata.song)
                    video.ui_song_label.pack(padx=5, pady=5, fill="both", expand=True)
            else:
                video.ui_artist_label.pack_forget()
                video.ui_song_label.pack_forget()
            
            ui_playing_label_time = datetime.fromtimestamp(
                video.last_playback).time()
            video.ui_playing_time.configure(text="{:02d}".format(ui_playing_label_time.hour) + ":" +
                                                 "{:02d}".format(ui_playing_label_time.minute) + ":" +
                                                 "{:02d}".format(ui_playing_label_time.second))

    def load_sequence(self):
        xml_root = ET.parse(self.xml_path).getroot()
        if xml_root is None:
            return
        assert (xml_root.tag == 'Document')
        for child in xml_root:
            if child.tag == "Title":
                PrintTraceInUi("Title of the sequence : " + child.text)
                self.title = child.text
            if child.tag == "Sequence":
                PrintTraceInUi("Sequence found!")

                self.sequence_data = SequenceBlock("sequence")
                self._build_sequence(sequence_xml_node=child,
                                     sequence_data_node=self.sequence_data)
        self._flatten_sequence(self.sequence_data)
        PrintTraceInUi(self.sequence_data)

        # Fill the UI
        for i, block in enumerate(self.sequence_data.inner_sequence):
            block.ui_frame = tk.Frame(
                self.sequence_view, width=200, height=200, bg=UI_BACKGROUND_COLOR)
            block.ui_frame.pack(side=tk.LEFT, padx=10,
                                pady=20, fill=tk.BOTH, expand=True)
            block.ui_playing_time = tk.Label(block.ui_frame, text=block.last_playback, font=(
                'calibri', 12), bg=UI_BACKGROUND_COLOR, fg="white")
            block.ui_playing_time.pack(
                padx=5, pady=5, fill="none", expand=False)
            block.ui_video_frame = tk.Frame(
                block.ui_frame, bg=block.get_color(), width=200, height=100)

            block.ui_frame.pack_propagate(False)
            block.ui_video_frame.pack(
                side=tk.BOTTOM, fill=tk.BOTH, expand=True)

            block.ui_id_label = tk.Label(
                block.ui_video_frame, text=str(i), bg=block.get_color(), fg="black", font=('calibri', 20, "bold"))
            block.ui_id_label.pack(
                padx=5, pady=5, fill="none", expand=False)
            block.ui_label = tk.Label(
                block.ui_video_frame, text=block.block_type, bg=block.get_color(), fg="black", font=('calibri', 11, 'italic'))
            block.ui_artist_label = tk.Label(
                block.ui_video_frame, text="Artist", bg=block.get_color(), fg="black", font=('calibri', 14, 'bold'))
            block.ui_artist_label.pack(padx=5, pady=5)
            block.ui_song_label = tk.Label(
                block.ui_video_frame, text="Song", bg=block.get_color(), fg="black", font=('calibri', 14))
            block.ui_song_label.pack(padx=5, pady=5)

            block.ui_label.pack(padx=5, pady=5,  fill="none", expand=False)

        # First sequence resolving. After each sequence iteration it will be called
        self._resolve_sequence()

    def get_next_video(self):
        if self.index_playing_video > -1:
            # Reset frame options
            video = self.sequence_data.inner_sequence[self.index_playing_video]
            video.modify_color(UI_BLOCK_PLAYED_VIDEO_COLOR)
            # Add to the history

            time_last_playback = datetime.fromtimestamp(
                video.last_playback).time()
            self.listviews.history_listbox.insert(0, "{:02d}".format(time_last_playback.hour) + ":" +
                                                  "{:02d}".format(time_last_playback.minute) + ":" +
                                                  "{:02d}".format(time_last_playback.second) + " " + video.path)

        # Resolve the sext sequence
        if self.index_playing_video == len(self.sequence_data.inner_sequence) - 1:
            self._resolve_sequence()
            for block in self.sequence_data.inner_sequence:
                block.modify_color(block.get_color())
                # Reset background colors
                block.ui_frame.configure(bg=UI_BACKGROUND_COLOR)
                block.ui_playing_time.configure(bg=UI_BACKGROUND_COLOR)

        # Incrementing the sequence and setting the selected frame in color
        self.index_playing_video = (
            self.index_playing_video + 1) % len(self.sequence_data.inner_sequence)
        video = self.sequence_data.inner_sequence[self.index_playing_video]
        video.select()

        # Recompute timestamps
        self.sequence_data.inner_sequence[self.index_playing_video].last_playback = time.time(
        )
        ui_playing_label_time = datetime.fromtimestamp(
            self.sequence_data.inner_sequence[self.index_playing_video].last_playback).time()
        self.sequence_data.inner_sequence[self.index_playing_video].ui_playing_time.configure(text="{:02d}".format(ui_playing_label_time.hour) + ":" +
                                                                                              "{:02d}".format(ui_playing_label_time.minute) + ":" +
                                                                                              "{:02d}".format(ui_playing_label_time.second))

        # Adding timestamps since the playing video
        for i in range(self.index_playing_video+1, len(self.sequence_data.inner_sequence)):
            video_modify = self.sequence_data.inner_sequence[i]
            PrintTraceInUi("Changing timestamps of video ",
                           i, " " + video_modify.path)

            self._resolve_timestamps(index=i)

            ui_playing_label_time = datetime.fromtimestamp(
                video_modify.last_playback).time()
            video_modify.ui_playing_time.configure(text="{:02d}".format(ui_playing_label_time.hour) + ":" +
                                                   "{:02d}".format(ui_playing_label_time.minute) + ":" +
                                                   "{:02d}".format(ui_playing_label_time.second))

        # Gathering the video details
        return (video.path, video.length)

    def kill(self):
        self.is_running_flag = False
        # TODO Stop tkinter frames


class MetaDataManager:
    """! Reads and open up API to the video metadata csv

         Parses the metadata csv
         Gives the Player some data about start and end of video playbacks
         and fade in/out options
         Gives also the volume to be set by video in order to have an equalized output
    """
    class MetaDataEntry:
        video_name = ""
        timestamp_begin = 0
        timestamp_end = 0
        fade_in = False
        fade_out = False
        artist = None
        song = None

        def __init__(self, video_name, timestamp_begin, timestamp_end, fade_in, fade_out, artist, song):
            self.video_name = video_name
            self.timestamp_begin = timestamp_begin
            self.timestamp_end = timestamp_end
            self.fade_in = fade_in
            self.fade_out = fade_out
            self.artist = artist
            self.song = song

    metadata_list = []

    def __init__(self, path):
        """! The MetaData manager initializer
            @param path : path the csv metadata file 
            @return An instance of a MetaDataManager
        """
        with open(path, newline='') as csvfile:
            csvdata = csv.reader(csvfile, delimiter=',')
            for line in csvdata:
                # The csv has to be well formed
                assert (len(line) == 7)

                # Format the timestamps in seconds
                def get_sec(time_str):
                    m, s = time_str.split(':')
                    return int(m) * 60 + int(s)

                self.metadata_list.append(
                    self.MetaDataEntry(video_name=line[0],
                                       timestamp_begin=get_sec(line[1]),
                                       timestamp_end=get_sec(line[2]),
                                       fade_in=line[3] == 'y',
                                       fade_out=line[4] == 'y',
                                       artist=line[5],
                                       song=line[6])
                )

    def get_metadata(self, video_name):
        """! Get the stored metadata about the video in parameter 
            @param video_name : name of the video (as stored in the metadata csv)
            @return a MetaDataEntry structure
        """
        it = list(filter(lambda meta: (
            meta.video_name == video_name), self.metadata_list))
        if len(it) == 0:
            PrintTraceInUi(
                "ERROR ! No metadata entries found for video " + video_name)
        else:
            if len(it) > 1:
                PrintTraceInUi("WARNING ! Multiple metadata entries for video " +
                               video_name + ". Taking first one")
            return it[0]


class MainManager:
    """! Main manager of the program

         Initialize and control the different application components
    """
    sequencer = None
    root = None
    metadata_button = None
    metadata_path = ""
    sequence_button = None
    sequence_path = ""

    def __init__(self, sequence_file, metadata_file, launch_now):
        """! The main manager initializer, handles the welcome screen to 
            select a sequence file and metadata  
        """
        self.sequence_path = sequence_file
        self.metadata_path = metadata_file
        self.root = tk.Tk()
    
        if launch_now:
            if not os.path.isfile(self.sequence_path):
                print("ERROR ", self.sequence_path, " IS NOT A VALID FILE")
                exit(1)
            if not os.path.isfile(self.metadata_path):
                print("ERROR ", self.metadata_path, " IS NOT A VALID FILE")
                exit(1)
            self.start_ui()
        else:
            title_view = tk.Frame(
                self.root, width=400, height=300, background=UI_BACKGROUND_COLOR)
            title_view.pack(side=tk.TOP,  fill=tk.BOTH)

            lbl = tk.Label(title_view, font=('calibri', 80, 'bold'),
                       text="VLCSequencer", background=UI_BACKGROUND_COLOR, foreground='white')
            lbl.pack(side=tk.TOP,  fill=tk.BOTH, pady=50)

            lbl = tk.Label(title_view, font=('calibri', 20),  text="Place this window where you want the videos to be played",
                       background=UI_BACKGROUND_COLOR,
                       foreground=UI_BLOCK_NORMAL_VIDEO_COLOR)
            lbl.pack(side=tk.TOP,  fill=tk.BOTH, pady=50)

            buttons_frame = tk.Frame(
                self.root, width=400, height=300, pady=10,  background=UI_BACKGROUND_COLOR)
            buttons_frame.pack(side=tk.BOTTOM,  fill=tk.BOTH, expand=1)

            def select_metadata_file():
                self.metadata_path = filedialog.askopenfilename(
                    title='Select Metadata File',
                    filetypes=[('Csv files', '*.csv')])

                if os.path.isfile(self.metadata_path):
                    self.metadata_button.configure(
                        bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)

            def select_sequence_file():
                self.sequence_path = filedialog.askopenfilename(
                    title='Select Sequence File',
                    filetypes=[('Xml files', '*.xml')])
                if os.path.isfile(self.sequence_path):
                    self.sequence_button.configure(
                        bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
                    start_button.configure(state=tk.NORMAL)

            self.metadata_button = tk.Button(
                buttons_frame,
                text='Select Metadata file',
                command=select_metadata_file,
                padx=10, pady=10, font=('calibri', 12),
                fg="white",
                bg=UI_BACKGROUND_COLOR
            )
            self.sequence_button = tk.Button(
                buttons_frame,
                text='Select Sequence file',
                command=select_sequence_file,
                padx=10, pady=10, font=('calibri', 12),
                fg="white",
                bg=UI_BACKGROUND_COLOR
            )

            start_button = tk.Button(
                buttons_frame, text="Start", command=self.start_ui,
                padx=10, pady=10, font=('calibri', 12),
                fg="white",
                bg=UI_BACKGROUND_COLOR,
                state=tk.DISABLED)

            start_button.pack(side=tk.BOTTOM,  fill=tk.BOTH)
            self.metadata_button.pack(side=tk.BOTTOM,  fill=tk.BOTH)
            self.sequence_button.pack(side=tk.BOTTOM,  fill=tk.BOTH)

            # if the paths are already filled by the command line
            if self.metadata_path is not None and os.path.isfile(self.metadata_path):
                    self.metadata_button.configure(
                        bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
            if self.sequence_path is not None and os.path.isfile(self.sequence_path):
                    self.sequence_button.configure(
                        bg=UI_BLOCK_SELECTED_VIDEO_FRAME_COLOR)
                    start_button.configure(state=tk.NORMAL)

    def start_ui(self):
        """! Start the sequence and player UI """
        # These arguments allow audio crossfading : each player has an individual sound
        instance = vlc.Instance(['--aout=directsound', '--quiet'])
        # instance = vlc.Instance('--verbose 3')
        assert (instance is not None)

        # Clean up window for letting space for playback
        for child in self.root.winfo_children():
            child.destroy()

        metadata_manager = None
        if os.path.isfile(self.metadata_path):
            metadata_manager = MetaDataManager(path=self.metadata_path)

        player = UiPlayer(tkroot=self.root, vlc_instance=instance,
                          metadata_manager=metadata_manager)
        self.sequence_manager = UiSequenceManager(
            tkroot=self.root, vlc_instance=instance, ui_player=player, path=self.sequence_path, metadata_manager=metadata_manager)
        self.sequence_manager.load_sequence()

        self.sequencer = MainSequencer(
            ui_player=player, ui_sequencer=self.sequence_manager)
        self.sequencer.launch_sequencer()

        def on_close():
            self.sequence_manager.kill()
            self.sequencer.kill()

        self.root.protocol("WM_DELETE_WINDOW", on_close)

    def main_loop(self):
        """! mainloop of the program
        """
        self.root.mainloop()


# Prevents this code to be runned if loaded as a module
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="VLCSequencer")
    parser.add_argument('-s','--sequence', help="Path of the sequence file to use", action="store")
    parser.add_argument('-m','--metadata', help="Path of the metadata file to use", action="store")
    parser.add_argument('-l','--launch', help="Set if you want to launch directly without going through the main menu", action="store_true")
    args = parser.parse_args()
        

    MainManager(sequence_file = args.sequence,
                metadata_file = args.metadata,
                launch_now = args.launch ).main_loop()
