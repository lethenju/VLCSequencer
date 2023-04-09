
import vlc
import tkinter as tk
from tkinter import ttk
import threading
import os
import time
import magic
import csv

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

    def _play_on_specific_frame(self, media, index_media_players, 
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
        length_s =  media.get_duration()/1000

        if end_s == 0:
            end_s = length_s
        player.play()

        player.set_position(begin_s/length_s) 
        def fade_in_thread():
            """! Thread to handle fade in on this player"""
            player.audio_set_volume(0)
            volume = player.audio_get_volume()
            while (volume < 100 and self.is_running_flag):
                print("fade_in Volume : " + str(volume))
                volume = volume + 5
                if not self.is_muted:
                    player.audio_set_volume(volume)
                time.sleep(0.5)
        

        def fade_out_thread():
            """! Thread to handle fade out on this player"""
            volume = player.audio_get_volume()
            while (volume > 0 and self.is_running_flag):
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
    
        while (player.get_position() < end_position  and self.is_running_flag):
            time.sleep(1)
            print("Current media playing time "+("{:.2f}".format(player.get_position()*100))+"%")

        if fade_out:
            threading.Thread(target=fade_out_thread).start()
        else:
            player.audio_set_volume(0)

    def play(self, path):
        """! Main play API

            @param path : Path to the video file to play
        """
        if self.is_running_flag:

            media = self.vlc_instance.media_new(path)

            # TODO Blockingless parsing time : thread ?
            media.parse_with_options(1,0)
            # Blocking the parsing time
            while self.is_running_flag:
                if str(media.get_parsed_status()) == 'MediaParsedStatus.done':
                    break
            
            # If media 0 is playing, the index has to be one, otherwise its 0
            # so its equivalent to ask directly the question if the media 0 is playing
            index_to_be_played = self.media_frames[0].media_player.is_playing()

            # Try to get metadata about this video
            name_of_file = path.split("/").pop()
            metadata =  self.metadata_manager.get_metadata(video_name=name_of_file)
            
            if metadata is not None:
                self._play_on_specific_frame(media, index_media_players=index_to_be_played, 
                                            begin_s = metadata.timestamp_begin, 
                                            end_s = metadata.timestamp_end, 
                                            fade_in = metadata.fade_in, 
                                            fade_out = metadata.fade_out)
            else:
                self._play_on_specific_frame(media, index_media_players=index_to_be_played)
    
    def _get_active_media_player(self):
        # Get the active player
        index_active_player =  self.media_frames[1].media_player.is_playing()
        return self.media_frames[index_active_player].media_player

    def pause_resume(self):
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

    def kill(self):
        """! Kill the window and release the vlc instance """
        self.is_running_flag = False
        self.window.destroy()        
        self.vlc_instance.release()




class MainSequencer():
    """! Handle the sequencing of videos to be played back """

    is_running_flag = False
    ui_player =  None
    thread = None

    def __init__(self, ui_player):
        self.ui_player = ui_player

    # Launch the sequencer thread
    def launch_sequencer(self):
        self.thread = threading.Thread(target=self.sequencer_thread)
        self.is_running_flag = True
        self.thread.start()


    def sequencer_thread(self):
        #gather list of files
        fichiers = os.listdir("res/clips/")
        while self.is_running_flag:
            # TODO UiSequenceManager get sequence
            # get_next_video()
            
            for i, fichier in enumerate(fichiers):
                print("Playing " + fichier)
                # Verify its a Media file before trying to play it 
                if ("Media" in magic.from_file("res/clips/" + fichier)):
                    self.ui_player.play(path="res/clips/" + fichier)
    def kill(self):
        self.is_running_flag = False
        self.ui_player.kill()

class UiSequenceManager:
    """! Reads the sequence description and builds the video sequence 

        Open a UI to visualize and modify the sequence 
    """
    ui_player = None
    def __init__(self, tkroot, ui_player, path):
        """! The Sequence manager initializer
            @param path : path the sequence file 
            @return An instance of a UiSequenceManager
        """
        self.ui_player =ui_player
        # start UI 

        # panel to hold buttons
        self.buttons_panel = tk.Toplevel(tkroot)
        self.buttons_panel.title("")
        self.is_buttons_panel_anchor_active = False

        buttons = ttk.Frame(self.buttons_panel)

        self.pause_button= ttk.Button(buttons, text="Pause/Resume", command=self.on_pause)
        self.mute_button = ttk.Button(buttons, text="Mute/Unmute", command=self.on_mute)
        self.pause_button.pack(side=tk.LEFT)
        self.mute_button.pack(side=tk.LEFT)
        buttons.pack(side=tk.BOTTOM, fill=tk.X)
        # Read file
        pass


    def on_pause(self, *unused):
        self.ui_player.pause_resume()
        pass
    def on_mute(self, *unused):
        self.ui_player.mute_trigger()
        pass

    def build_sequence():
        pass
    def get_next_video():
        pass

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

        # VLC player
        instance = vlc.Instance(['--aout=directsound', '--directx-volume=0.35'])

        metadata_manager = MetaDataManager(path="res/metadata.csv")

        player = UiPlayer(tkroot=self.root, vlc_instance=instance, metadata_manager=metadata_manager)

        self.sequence_manager = UiSequenceManager(tkroot=self.root, ui_player=player, path="res/sequence.xml")
        
        self.sequencer = MainSequencer(ui_player=player)

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

