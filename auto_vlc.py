
import vlc
import tkinter as tk
from tkinter import ttk
import threading
import os
import time
import magic
import csv
import random
import xml.etree.ElementTree as ET
import copy

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
    is_next_asked = False

    class MediaFrame:
        """! Structure that links a Tkinter frame with a Vlc media player """
        media_player = None # A Vlc media player
        ui_frame = None     # Tkinter frame

        def __init__(self, media_player, ui_frame):
            self.media_player = media_player
            self.ui_frame = ui_frame

    media_frames = None # List (tuple) of media frames


    def __init__(self, tkroot, vlc_instance, metadata_manager):
        """! Initialize the main display window """
        # Main window initialisation
        self.window = tkroot
        self.window.title("MainUI")
        self.window.geometry("400x300")

        self.vlc_instance = vlc_instance
        self.metadata_manager = metadata_manager

        self.is_next_asked = False

        # 2 players (one for each frame)
        # Initialize media frames with the players and new tk frames. Setting bg colors for debugging if something goes wrong
        self.media_frames = (self.MediaFrame(self.vlc_instance.media_player_new(),
                                            tk.Frame(self.window, bg="red", width=200, height=150)),
                             self.MediaFrame(self.vlc_instance.media_player_new(),
                                            tk.Frame(self.window, bg="blue", width=200, height=150)))
        for i, _ in enumerate(self.media_frames):
            self.media_frames[i].ui_frame.pack(fill="both", expand=True)

        def toggle_full_screen(*unused):
            global is_fullscreen_flag
            self.window.attributes("-fullscreen", not is_fullscreen_flag)
            is_fullscreen_flag = not is_fullscreen_flag
        self.window.bind("<F11>", toggle_full_screen)
        self.is_running_flag = True

    def _play_on_specific_frame(self, media, index_media_players, length_s,
                                begin_s = 0, end_s = 0, fade_in = False, fade_out= False):
        """! Main play function.
            @param media : The Vlc Media instance 
            @param index_media_players the index of the media frame to use this time

            Handles audio crossfading and frame switching accordingly
        """
        # Getting simpler name from now on
        frame = self.media_frames[index_media_players].ui_frame
        player = self.media_frames[index_media_players].media_player

        player.set_media(media)
        self.window.after(0, lambda: self.media_frames[ 1 - index_media_players].ui_frame.pack_forget())
        self.window.after(0, lambda: frame.pack(fill="both", expand=True))

        # TODO Linux comp
        h = frame.winfo_id() 
        player.set_hwnd(h)

        if end_s == 0:
            end_s = length_s
        player.play()

        player.set_position(begin_s/length_s) 
        def fade_in_thread():
            """! Thread to handle fade in on this player"""
            player.audio_set_volume(0)
            volume = player.audio_get_volume()
            while (volume < 100 and self.is_running_flag and not self.is_next_asked):
                print("fade_in Volume : " + str(volume))
                volume = volume + 5
                if not self.is_muted:
                    player.audio_set_volume(volume)
                time.sleep(0.5)
        

        def fade_out_thread():
            """! Thread to handle fade out on this player"""
            volume = player.audio_get_volume()
            while (volume > 0 and self.is_running_flag and not self.is_next_asked):
                print("fade_out Volume : " + str(volume))
                volume = volume - 5
                player.audio_set_volume(volume)
                time.sleep(0.5)
            player.stop()
        if fade_in:
            threading.Thread(target=fade_in_thread).start()
        elif not self.is_muted:
            player.audio_set_volume(100)

        # Fix : If the end is the actual end, we may never reach it.
        if end_s != length_s:
            end_position = end_s/length_s
        else:
            end_position = 0.95
    
        while (player.get_position() < end_position  and self.is_running_flag and not self.is_next_asked):
            time.sleep(1)
            print("Current media playing time "+("{:.2f}".format(player.get_position()*100))+"%")

        if fade_out:
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

            # If media 0 is playing, the index has to be one, otherwise its 0
            # so its equivalent to ask directly the question if the media 0 is playing
            index_to_be_played = self.media_frames[0].media_player.is_playing()

            # Try to get metadata about this video
            name_of_file = path.split("/").pop()
            metadata =  self.metadata_manager.get_metadata(video_name=name_of_file)
            
            if metadata is not None:
                self._play_on_specific_frame(media, index_media_players=index_to_be_played, 
                                            length_s = length_s,
                                            begin_s = metadata.timestamp_begin, 
                                            end_s = metadata.timestamp_end, 
                                            fade_in = metadata.fade_in, 
                                            fade_out = metadata.fade_out)
            else:
                self._play_on_specific_frame(media,index_media_players=index_to_be_played,  length_s = length_s)
    
    def _get_active_media_player(self):
        # Get the active player
        index_active_player =  self.media_frames[1].media_player.is_playing()
        return self.media_frames[index_active_player].media_player

    def pause_resume(self):
        #TODO pause the fade mechanisms as well
        player = self._get_active_media_player()
        player.pause()
        pass
        
    def mute_trigger(self):
        player = self._get_active_media_player()
        if  player.audio_get_volume() != 0:
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
    ui_player =  None
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
    inner_sequence = []
    block_type = None
    block_args = None
    ui_frame = None
    ui_label = None
    def __init__(self, block_type, block_args = None):
        self.ui_frame = None
        self.ui_label = None
        self.inner_sequence = []
        self.block_type = block_type
        self.block_args = block_args

    def add_block(self, block):
        self.inner_sequence.append(block)

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
    ui_player = None
    sequence_view = None
    sequence_data = None
    xml_root = None
    vlc_instance = None # To get true metadata about the video (length..)
    title = ""
    index_playing_video = -1

    def __init__(self, tkroot, vlc_instance, ui_player, path):
        """! The Sequence manager initializer
            @param path : path the sequence file 
            @return An instance of a UiSequenceManager
        """
        self.ui_player = ui_player
        self.vlc_instance = vlc_instance
        # start UI 

        # panel to hold buttons
        self.ui_sequence_manager = tk.Toplevel(tkroot)
        self.ui_sequence_manager.title("Sequence Manager")

        buttons = ttk.Frame(self.ui_sequence_manager)

        self.pause_button= ttk.Button(buttons, text="Pause/Resume", command=self.ui_player.pause_resume)
        self.mute_button = ttk.Button(buttons, text="Mute/Unmute",  command= self.ui_player.mute_trigger)
        self.next_button = ttk.Button(buttons, text="Next",         command= self.ui_player.next)
        self.pause_button.pack(side=tk.LEFT)
        self.mute_button.pack(side=tk.LEFT)
        self.next_button.pack(side=tk.LEFT)
    
        buttons.pack(side=tk.BOTTOM, fill=tk.X)

        self.sequence_view = ttk.Frame(self.ui_sequence_manager,width=1000, height=500)
        self.sequence_view.pack(side=tk.TOP, fill=tk.X)

        # Read file
        tree = ET.parse(path)
        self.xml_root = tree.getroot()
        
    def _build_sequence(self, sequence_xml_node, sequence_data_node):
        for child in sequence_xml_node:
            if child.tag == "Repeat":
                nb_times = child.attrib['nb_time']
                block = SequenceBlock("repeat", nb_times)
                self._build_sequence(sequence_xml_node=child, sequence_data_node=block)
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
                        sequence_data_node.inner_sequence.insert(i, copy.copy(block_child))
                sequence_data_node.inner_sequence.remove(block)

    def _find_random_video(self, path, timeout):
        #gather list of files
        files = os.listdir("res/" + path)
        video_found = None
        while video_found is None:
            file = files[random.randrange(len(files))]
            complete_path = "res/" + path + "/" + file
            print("Testing " + complete_path)
            # Verify its a Media file before trying to play it 

            # TODO Verify the clip hasnt played since "timeout" minutes
            if ("Media" in magic.from_file(complete_path)):
                video_found = complete_path
        return video_found

    def _resolve_sequence(self):
        """! Chooses the random videos to be displayed, add length for each media and media info to blocks """
        for i, video in enumerate(self.sequence_data.inner_sequence):
            final_path = None
            if (video.block_type == "randomvideo"):
                path    = video.block_args[0] 
                timeout = video.block_args[1]
                final_path = self._find_random_video(path, timeout)
                pass
            if (video.block_type == "video"):    
                final_path    = "res/"+ video.block_args

            # Storing path in the block
            video.path = final_path

            media = self.vlc_instance.media_new(video.path)

            media.parse_with_options(1,0)
            # Blocking the parsing time
            while True:
                if str(media.get_parsed_status()) == 'MediaParsedStatus.done':
                    break
            video.length =  media.get_duration()/1000
            # We do not need this media anymore
            media.release()
            
            # Add also the name to the UI
            video.ui_label.configure(text=video.path.split("/").pop())

                
    def load_sequence(self):
        if self.xml_root is None:
            return
        assert(self.xml_root.tag == 'Document')
        for child in self.xml_root:
            print(child.tag, child.attrib)
            if child.tag == "Title":
                print("Title of the sequence : " + child.text)
                self.title = child.text
            if child.tag == "Sequence":
                print("Sequence found!")
                
                self.sequence_data = SequenceBlock("sequence")
                self._build_sequence(sequence_xml_node=child,
                                     sequence_data_node=self.sequence_data)
        self._flatten_sequence(self.sequence_data)
        print(self.sequence_data)

        # Fill the UI
        for i, block in enumerate(self.sequence_data.inner_sequence):
            block.ui_frame = tk.Frame(self.sequence_view, bg="white", width=200, height=50)
            block.ui_frame.pack(side=tk.LEFT, padx=10,  pady=20, fill=tk.BOTH, expand=True)
            block.ui_frame.pack_propagate(False)
            tk.Label(block.ui_frame, text=str(i)).pack(padx=5, pady=5,fill="none", expand=False)
            block.ui_label = tk.Label(block.ui_frame, text=block.block_type)
            block.ui_label.pack(padx=5, pady=5,fill="both", expand=True)

        # First sequence resolving. After each sequence iteration it will be called
        self._resolve_sequence()

    def get_next_video(self):                        
        if self.index_playing_video > -1:
            # Reset frame options
            self.sequence_data.inner_sequence[self.index_playing_video].ui_frame.configure(bg="white")
        
        # Resolve the sext sequence
        if self.index_playing_video == len(self.sequence_data.inner_sequence) - 1:
            self._resolve_sequence()

        # Incrementing the sequence and setting the selected frame in color
        self.index_playing_video = (self.index_playing_video + 1) % len(self.sequence_data.inner_sequence)
        self.sequence_data.inner_sequence[self.index_playing_video].ui_frame.configure(bg="blue")

        # Gathering the video details
        video = self.sequence_data.inner_sequence[self.index_playing_video]
        return (video.path, video.length)
            

class MetaDataManager:
    """! Reads and open up API to the video metadata csv
         
         Parses the metadata csv
         Gives the Player some data about start and end of video playbacks
         and fade in/out options
         Gives also the volume to be set by video in order to have an equalized output
    """
    class MetaDataEntry:
        video_name      = ""
        timestamp_begin = 0
        timestamp_end = 0
        fade_in = False
        fade_out = False
        def __init__(self, video_name, timestamp_begin, timestamp_end, fade_in, fade_out):
            self.video_name      = video_name
            self.timestamp_begin = timestamp_begin
            self.timestamp_end = timestamp_end
            self.fade_in = fade_in
            self.fade_out = fade_out

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
                assert(len(line) == 5)

                # Format the timestamps in seconds
                def get_sec(time_str):
                    m, s = time_str.split(':')
                    return int(m) * 60 + int(s)
                
                self.metadata_list.append(
                    self.MetaDataEntry(video_name=line[0], 
                                       timestamp_begin=get_sec(line[1]),
                                       timestamp_end=get_sec(line[2]),
                                       fade_in = line[3] == 'y',
                                       fade_out = line[4] == 'y')
                    )
    
    def get_metadata(self, video_name):
        """! Get the stored metadata about the video in parameter 
            @param video_name : name of the video (as stored in the metadata csv)
            @return a MetaDataEntry structure
        """
        it = list(filter(lambda meta: (meta.video_name==video_name), self.metadata_list))
        if len(it) == 0:
            print ("ERROR ! No metadata entries found for video " + video_name)
        else:
            if len(it) > 1:
                print ("WARNING ! Multiple metadata entries for video " + video_name + ". Taking first one")
            return it[0]

class MainManager:
    """! Main manager of the program
         
         Initialize and control the different application components
    """
    sequencer = None
    root = None

    def __init__(self):
        """! The main manager initializer"""
        self.root = tk.Tk()
        # These arguments allow audio crossfading : each player has an individual sound
        instance = vlc.Instance(['--aout=directsound', '--directx-volume=0.35'])
        metadata_manager = MetaDataManager(path="res/metadata.csv")
        player = UiPlayer(tkroot=self.root, vlc_instance=instance, metadata_manager=metadata_manager)
        self.sequence_manager = UiSequenceManager(tkroot=self.root, vlc_instance=instance, ui_player=player, path="res/sequence.xml")
        self.sequence_manager.load_sequence()

        self.sequencer = MainSequencer(ui_player=player, ui_sequencer=self.sequence_manager)

        def on_close():
            self.sequencer.kill()

        self.root.protocol("WM_DELETE_WINDOW", on_close)

    def main_loop(self):
        """! mainloop of the program
        """
        self.sequencer.launch_sequencer()
        self.root.mainloop()

# Prevents this code to be runned if loaded as a module
if __name__=='__main__':
    MainManager().main_loop()

