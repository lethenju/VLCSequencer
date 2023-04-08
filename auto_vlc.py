
import vlc
import tkinter as tk
import threading
import os, time


# Main window
window = None

# Launch the UI on a different thread
def launch_ui():
    global window
    window = tk.Tk()
    window.title("Frame")
    window.geometry("400x300")
        
    frame1 = tk.Frame(window, bg="red", width=200, height=150)
    frame2 = tk.Frame(window, bg="blue", width=200, height=150)
    frame1.pack(fill="both", expand=True)
    frame2.pack(fill="both", expand=True)
    window.mainloop()

thread = threading.Thread(target=launch_ui)
thread.start()

# VLC player
args = ['--aout=directsound', '--directx-volume=0.35']
vlc.print_version()
vlc.print_python()

Instance = vlc.Instance(args)

# 2 frames to enable crossfading between clips : a frame for each clip
frame1 = window.winfo_children()[0]
frame2 = window.winfo_children()[1]

# 2 players (one for each frame)
player1 = Instance.media_player_new()
player2 = Instance.media_player_new()

#gather list of files
fichiers = os.listdir("res")


def Play(player, media, frame, otherframe):
    player.set_media(media)
    window.after(0, lambda:otherframe.pack_forget())
    window.after(0, lambda:frame.pack())
    h = frame.winfo_id()  # .winfo_visualid()?
    player.set_hwnd(h)
    # TODO have a possibility of going to the next video
    player.play()
    # TODO Set to the full frame size
    player.set_fullscreen(True)
    
    # TODO Read the actual beginning and end timestamps from a file
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

for i, fichier in enumerate(fichiers):
    print("Lecture de "+fichier)
    media = Instance.media_new("res/"+fichier)
    if (i % 2):
        Play(player1, media, frame1, frame2)
    else:
        Play(player2, media, frame2, frame1)
