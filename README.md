# VLCSequencer

You have a big screen at home and you want to use it during parties, displaying video clips, but without having to deal with either
a premium Youtube subscription or ads on cable TV or Youtube ?

You want to automate a video blindtest ?

You want to display long videos in a particular order repeatedly ?

You want audio crossfade between the end of a video and the beginning of the next one ?

You want to mimic 20th century's MTV, have clips, jingles and fake ads, and even display messages on the screen during a party, and give the audience the possibility to add their own messages ?

Thats all what VLCSequencer does !

You give it a sequence file, some metadatas and you're off !

TODO put screenshots of the program

## Requirements and installation

You'll need Python3, VLC and some pip packages :

### For Windows

```powershell
python.exe -m pip install python-vlc python-magic-bin=0.4.14 pillow
```

### For Linux

```bash
sudo apt install vlc libvlc-dev python3-pil python3-pil.imagetk
python3 -m pip install python-vlc python-magic pillow
```

## Usage

### Sequence file

### Metadata file

### Runtime controls

### TODO

Plugins :

- Add screen preview on the sequence window
- Add clear message button to clear the database table
- And Delete message button on each message
- VLC Sound management as a module
- Choose the next music (music queue list (maybe via the webpage ???))

Ui :

- Add Metadata-related info on the sequence (if fade-in/out are activated, etc..)
- Add a button to get back to the beginning of the current video

Video playback :

- Gather the actual device output volume to enable automatic volume correction (Cross platform ? We need windows API and ALSA/portaudio API for linux)
- Fix mute mode

Sequencing :

- For sequencing : Add '\<if sooner_than="time"/>' and '\<if later_than="time" />' statements parsing

Other :

- Better separate UI code from fonctionnal code
- Documentation and refactors
- Documentation in readme
- Linting