
import vlc
import tkinter as tk
import threading
import os, time
import magic

class UiPlayer(tk.Frame):
    thread = None    
    # Main window
    window = None
    isFullScreen = False
    isFrame1Turn = False
    MediaPlayer1 = None
    MediaPlayer2 = None

    def __init__(self, tkroot, MediaPlayer1, MediaPlayer2):
        self.window = tkroot
        self.MediaPlayer1 = MediaPlayer1
        self.MediaPlayer2 = MediaPlayer2
        self.window.title("MainUI")
        self.window.geometry("400x300")
        
        self.window.protocol("WM_DELETE_WINDOW", self.OnClose)  # XXX unnecessary (on macOS)
        
        self.frame1 = tk.Frame(self.window, bg="red", width=200, height=150)
        self.frame2 = tk.Frame(self.window, bg="blue", width=200, height=150)
        self.frame1.pack(fill="both", expand=True)
        self.frame2.pack(fill="both", expand=True)
        def ToggleFullScreen(event=None):
            global isFullScreen
            self.window.attributes("-fullscreen", not isFullScreen)
            isFullScreen = not isFullScreen
        self.window.bind("<F11>", ToggleFullScreen)

    def _Play(self, player, media, frame, otherframe):
        player.set_media(media)
        self.window.after(0, lambda:otherframe.pack_forget())
        self.window.after(0, lambda:frame.pack(fill="both", expand=True))
        h = frame.winfo_id()  # .winfo_visualid()?
        # TODO Linux comp
        player.set_hwnd(h)
        
        # TODO have a possibility of going to the next video
        # Different frame for direct control

        player.play()
        player.set_position(0.75) 
        def FadeInThread():
            player.audio_set_volume(0)
            volume = player.audio_get_volume()
            while (volume < 100):
                print("FadeInThread Volume : " + str(volume))
                volume = volume + 5
                player.audio_set_volume(volume)
                time.sleep(0.5)

        def FadeOutThread():
            volume = player.audio_get_volume()
            while (volume > 0):
                print("FadeOutThread Volume : " + str(volume))
                volume = volume - 5
                player.audio_set_volume(volume)
                time.sleep(0.5)
        fadein_thread = threading.Thread(target=FadeInThread)
        fadein_thread.start()

        while (player.get_position() < 0.80):
            time.sleep(1)
            print("Current media playing time "+("{:.2f}".format(player.get_position()*100))+"%")

        threading.Thread(target=FadeOutThread).start()


    def Play(self, media):
        self.isFrame1Turn = not self.isFrame1Turn
        # 2 frames to enable crossfading between clips : a frame for each clip
        if (self.isFrame1Turn):
            self._Play(self.MediaPlayer1, media, self.frame1, self.frame2)
        else:
            self._Play(self.MediaPlayer2, media, self.frame2, self.frame1)

    def OnClose(self):
        print("Close")
        self.thread.join()


class MainSequencer():

    def __init__(self, UiPlayer, VlcInstance):
        self.UiPlayer = UiPlayer
        self.VlcInstance = VlcInstance

    # Launch the UI on a different thread
    def LaunchSequencer(self):
        self.thread = threading.Thread(target=self.Sequencer)
        self.thread.start()


    def Sequencer(self):
        #gather list of files
        fichiers = os.listdir("res/clips/")

        for i, fichier in enumerate(fichiers):
            # TODO not start everyfile directly 
            # Have some static (dynamic ?) sequencing capabilities
            # For example : 
            # [
            #   -> Music  : res/clip -> Take random videos from here *2
            #   -> Jingle : res/jingle -> jingle video for the TV
            #   -> Ads    : res/ads -> Take random videos from here 
            # ]

            # TODO Read the actual beginning and end timestamps from a file
            # TODO from that file, if needed fadein and/or fadeout
            # Csv : filename,startimestamp, endtimestamp, is_audio_fadein, is_audio_fadeout

            print("Lecture de " + fichier)
            if ("Media" in magic.from_file("res/clips/"+fichier)):
                media = self.VlcInstance.media_new("res/clips/"+fichier)
                self.UiPlayer.Play(media)

# VLC player
args = ['--aout=directsound', '--directx-volume=0.35']
vlc.print_version()
vlc.print_python()
Instance = vlc.Instance(args)
# 2 players (one for each frame)
player1 = Instance.media_player_new()
player2 = Instance.media_player_new()

root = tk.Tk()
player = UiPlayer(tkroot=root, MediaPlayer1=player1, MediaPlayer2=player2)

sequencer = MainSequencer(UiPlayer = player, VlcInstance = Instance)

sequencer.LaunchSequencer()

root.mainloop()