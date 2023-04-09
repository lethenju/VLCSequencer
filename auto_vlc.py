
import vlc
import tkinter as tk
import threading
import os
import time
import magic

class UiPlayer(tk.Frame):
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

    vlc_instance = None

    class MediaFrame:
        """! Structure that links a Tkinter frame with a Vlc media player """
        media_player = None # A Vlc media player
        ui_frame = None     # Tkinter frame
        def __init__(self, media_player, ui_frame):
            self.media_player = media_player
            self.ui_frame = ui_frame

    media_frames = None # List (tuple) of media frames

    def __init__(self, tkroot, vlc_instance):
        """! Initialize the main display window """

        # Main window initialisation
        self.window = tkroot
        self.window.title("MainUI")
        self.window.geometry("400x300")

        self.vlc_instance = vlc_instance

        # 2 players (one for each frame)
        # Initialize media frames with the players and new tk frames. Setting bg colors for debugging if something goes wrong
        self.media_frames = (self.MediaFrame(self.vlc_instance.media_player_new(),
                                            tk.Frame(self.window, bg="red", width=200, height=150)),
                             self.MediaFrame(self.vlc_instance.media_player_new(),
                                            tk.Frame(self.window, bg="blue", width=200, height=150)))
        for i, _ in enumerate(self.media_frames):
            self.media_frames[i].ui_frame.pack(fill="both", expand=True)

        def toggle_full_screen(event=None):
            global is_fullscreen_flag
            self.window.attributes("-fullscreen", not is_fullscreen_flag)
            is_fullscreen_flag = not is_fullscreen_flag
        self.window.bind("<F11>", toggle_full_screen)
        self.is_running_flag = True

    def _play_on_specific_frame(self, media, index_media_players):
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

        player.play()
        player.set_position(0.75) 
        def fade_in_thread():
            """! Thread to handle fade in on this player"""
            player.audio_set_volume(0)
            volume = player.audio_get_volume()
            while (volume < 100 and self.is_running_flag):
                print("fade_in Volume : " + str(volume))
                volume = volume + 5
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
        threading.Thread(target=fade_in_thread).start()

        while (player.get_position() < 0.80 and self.is_running_flag):
            time.sleep(1)
            print("Current media playing time "+("{:.2f}".format(player.get_position()*100))+"%")
        threading.Thread(target=fade_out_thread).start()


    def play(self, path):
        """! Main play API

            @param path : Path to the video file to play
        """
        if self.is_running_flag:
            media = self.vlc_instance.media_new(path)
            # 2 frames to enable crossfading between clips : a frame for each clip
            if (self.media_frames[0].media_player.is_playing()):
                self._play_on_specific_frame(media, index_media_players=1)
            else:
                self._play_on_specific_frame(media, index_media_players=0)

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
            for i, fichier in enumerate(fichiers):
                # TODO not start everyfile directly 
                # Have some static (dynamic ?) sequencing capabilities
                # For example : 
                # [
                #   -> Music  : res/clip -> Take random videos from here *2
                #   -> Jingle : res/jingle -> jingle video for the TV
                #   -> Ads    : res/ads -> Take random videos from here 
                # ]
                # Parse Sequence file
                # And build an actual sequence
                # Add a UI frame (on a different window) to preview (and control) the sequence

                # TODO Read the actual beginning and end timestamps from a file
                # TODO from that file, if needed fadein and/or fadeout
                # Csv : filename,startimestamp, endtimestamp, is_audio_fadein, is_audio_fadeout

                print("Lecture de " + fichier)
                if ("Media" in magic.from_file("res/clips/" + fichier)):
                    self.ui_player.play(path="res/clips/" + fichier)
    def kill(self):
        self.is_running_flag = False
        self.ui_player.kill()

class MetaDataManager:
    """! Reads and open up API to the video metadata csv
         
         Parses the metadata csv
         Gives the Player some data about start and end of video playbacks
         and fade in/out options
         Gives also the volume to be set by video in order to have an equalized output
    """
    def __init__(self, path):
        """! The MetaData manager initializer
            @param path : path the csv metadata file 
            @return An instance of a MetaDataManager
        """
        pass


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

        player = UiPlayer(tkroot=self.root, vlc_instance=instance)
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

