# VLCSequencer

TODO Fill the readme

## Requirements and installation

### For Windows

You'll need Python3, VLC and some pip packages as described in the linux section 

(TODO actual powershell commands)

### For Linux

```bash
sudo apt install vlc libvlc-dev
python3 -m pip install python-vlc
python3 -m pip install python-magic
```

## Usage

### Sequence file

### Metadata file

### Runtime controls

### TODO

- Add Metadata-related info on the sequence (if fade-in/out are activated, etc..)
- Add a button to reload metadatas during a sequence (to enable correcting/modifying them as the sequence plays)
- Add a button to get back to the beginning of the current video
- Add a button to force change a video
- Gather the actual device output volume to enable automatic volume correction
- For sequencing : Add '\<if sooner_than="time"/>' and '\<if later_than="time" />' statements parsing
- Add a messaging system as a plugin (Web page to add a custom message)
- Add parameters node in sequence file
   -> Default behaviours
   -> Plugin configuration : Song info theming, messaging parameters (how long should the messages stays, max message nb etc)

