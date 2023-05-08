import tkinter as tk
from tkinter import filedialog
import threading
import os
import time
import magic
import random
import xml.etree.ElementTree as ET
import copy
from datetime import datetime
from functools import partial

# Application related imports
from colors import *
from logger import PrintTraceInUi, LoggerSubscribeUI

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
    ui_button_repeat_toggle = None
    ui_button_change_video = None
    is_on_repeat = False
    last_playback = 0

    def __init__(self, block_type, block_args=None, repeat = False):
        self.inner_sequence = []
        self.ui_frame = None
        self.ui_playing_time = None
        self.ui_video_frame = None
        self.ui_label = None
        self.ui_id_label = None
        self.ui_artist_label = None
        self.ui_song_label = None
        self.ui_button_repeat_toggle = None
        self.ui_button_change_video = None
        self.block_type = block_type
        self.block_args = block_args
        self.last_playback = 0

        if repeat:
            self.is_on_repeat = True
        else:
            self.is_on_repeat = False


    def set_on_repeat(self):
        """! Toggle repeat mode """
        PrintTraceInUi("Toggling repeat mode")
        self.is_on_repeat = not self.is_on_repeat
        if self.is_on_repeat:
            self.modify_color(UI_BLOCK_REPEAT_VIDEO_COLOR)
        else:
            self.modify_color(self.get_color())

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
        # TODO "for widget in ui:"
        # Have a dictionary of widgets 
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
        self.ui_button_frame.configure(
            bg=color)
        self.ui_button_repeat_toggle.configure(
            bg=color)
        self.ui_button_change_video.configure(
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
            
            LoggerSubscribeUI(ui_trace_listbox)
            ui_trace_listbox.pack(side=tk.LEFT, fill=tk.BOTH)

            scrollbar_logs.config(command=ui_trace_listbox.yview)

    # Reference to the player object to connect the playback buttons to the associated callbacks
    ui_player = None
    # Reference to the metadata API to get the user-defined start/end playback timestamps
    metadata_manager = None
    # Reference to the plugins API
    plugin_manager = None
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

    def __init__(self, tkroot, vlc_instance, ui_player, path, metadata_manager, plugin_manager):
        """! The Sequence manager initializer

            @param path : path the sequence file 
            @return An instance of a UiSequenceManager
        """
        self.ui_player = ui_player
        self.vlc_instance = vlc_instance
        self.metadata_manager = metadata_manager
        self.plugin_manager = plugin_manager
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
        self.reload_csv_button = tk.Button(
            self.ui_playback_control_view, text="Reload Metadata",         command=self.reload_metadata,
            padx=10, pady=10, font=('calibri', 12),
            fg="white",
            bg=UI_BACKGROUND_COLOR)
        self.quit_button = tk.Button(
            self.ui_playback_control_view, text="Quit",         command=self.kill,
            padx=10, pady=10, font=('calibri', 12),
            fg="white",
            bg=UI_BACKGROUND_COLOR)
        self.pause_button.grid(column=0, row=0, padx=10, pady=10)
        self.mute_button.grid(column=1, row=0, padx=10, pady=10)
        self.next_button.grid(column=2, row=0, padx=10, pady=10)
        self.reload_csv_button.grid(column=3, row=0,padx=10, pady=10)
        self.quit_button.grid(column=4, row=0, padx=10, pady=10)
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

    def reload_metadata(self):
        PrintTraceInUi("Reloading metadata")
        if self.metadata_manager is not None:
            self.metadata_manager.reload()
        # TODO Reload UI
        
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
                repeat = child.attrib.setdefault('repeat',None)
                block = SequenceBlock("video", path, repeat= (repeat == "1"))
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

    def _load_video(self, path, video):
        """! Load video info in the block 
            @param path : full path of the video
            @param video : Reference to the video block to fill
        """
        # Storing path in the block
        video.path = path
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

            self._load_video(final_path, video)

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
                self.sequence_view, width=200, height=250, bg=UI_BACKGROUND_COLOR)
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

            block.ui_button_frame = tk.Frame(
                block.ui_video_frame,
                bg=block.get_color())
            block.ui_button_frame.pack(fill=tk.BOTH, expand=True)
            block.ui_button_repeat_toggle = tk.Button(
                block.ui_button_frame, text="Toggle Repeat", command=block.set_on_repeat,
                font=('calibri', 12),
                fg="white",
                bg=block.get_color())

            block.ui_button_repeat_toggle.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            block.ui_button_change_video = tk.Button(
                block.ui_button_frame, text="Change Video", command=partial(self._change_video, i),
                font=('calibri', 12),
                fg="white",
                bg=block.get_color())
            block.ui_button_change_video.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

            if block.is_on_repeat:
                block.modify_color(UI_BLOCK_REPEAT_VIDEO_COLOR)
            else:
                block.modify_color(block.get_color())

        # First sequence resolving. After each sequence iteration it will be called
        self._resolve_sequence()

    def _change_video(self, video_index):
        """! Modify the video of the block 
            @param video_index : Index of the video to modify
        """
        if self.index_playing_video == video_index:
            PrintTraceInUi("You cannot change the current video")
            return
        video = self.sequence_data.inner_sequence[video_index]
        PrintTraceInUi("Change video ", video_index)
        video_path = filedialog.askopenfilename(
            title='Select Video',
            filetypes=[('Video files', '*.mp4')])
        if os.path.isfile(video_path):
            self._load_video(video_path, video)
            if video.is_on_repeat:
                video.modify_color(UI_BLOCK_REPEAT_VIDEO_COLOR)
            else:   
                video.modify_color(UI_BLOCK_NORMAL_VIDEO_COLOR)

            self._reconfigure_timestamps(video_index, is_now = False)
            
    def _reconfigure_timestamps(self, from_index, is_now = True):
        """! Reconfigure all timestamps from the index chosen 
            @param from_index : Index of the first video to recompute
            @param is_now : true if the first video is to be set from now (default)
                            false if we need to take the already computed time
        """
        
        if is_now:
        # Recompute timestamps
            self.sequence_data.inner_sequence[self.index_playing_video].last_playback = time.time()
            ui_playing_label_time = datetime.fromtimestamp(
            self.sequence_data.inner_sequence[self.index_playing_video].last_playback).time()
            self.sequence_data.inner_sequence[self.index_playing_video].ui_playing_time.configure(text="{:02d}".format(ui_playing_label_time.hour) + ":" +
                                                                                              "{:02d}".format(ui_playing_label_time.minute) + ":" +
                                                                                              "{:02d}".format(ui_playing_label_time.second))   
        # Adding timestamps since the playing video
        for i in range(from_index + 1, len(self.sequence_data.inner_sequence)):
            video_modify = self.sequence_data.inner_sequence[i]
            PrintTraceInUi("Changing timestamps of video ",
                        i, " " + video_modify.path)

            self._resolve_timestamps(index=i)

            ui_playing_label_time = datetime.fromtimestamp(
                video_modify.last_playback).time()
            video_modify.ui_playing_time.configure(text="{:02d}".format(ui_playing_label_time.hour) + ":" +
                                                "{:02d}".format(ui_playing_label_time.minute) + ":" +
                                                "{:02d}".format(ui_playing_label_time.second))



    def get_next_video(self):
        video = self.sequence_data.inner_sequence[self.index_playing_video]

        # If the current video is set on repeat, we select it again
        if video.is_on_repeat:
            self._reconfigure_timestamps(self.index_playing_video)
            return (video.path, video.length)

        if self.index_playing_video > -1:
            # Reset frame options
            video.modify_color(UI_BLOCK_PLAYED_VIDEO_COLOR)
            # Remove buttons
            video.ui_button_frame.pack_forget()
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
     
        self._reconfigure_timestamps(self.index_playing_video)

        # Gathering the video details
        return (video.path, video.length)

    def kill(self):
        self.is_running_flag = False
        self.ui_player.kill()
        try:
            self.ui_sequence_manager.destroy()
        except:
            exit(1)

