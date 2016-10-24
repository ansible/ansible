#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# this is a windows documentation stub.  actual code lives in the .ps1
# file of the same name

DOCUMENTATION = '''
---
module: win_say
version_added: "2.3"
short_description: Text to speech module for Windows to speak messages and optionally play sounds
description:
    - Uses .NET libraries to convert text to speech and optionally play .wav sounds.  Audio Service needs to be running and some kind of speakers or headphones need to be attached to the windows target(s) for the speech to be audible.
options:
  msg:
    description:
      - The text to be spoken.  Use either msg or msg_file.  Optional so that you can use this module just to play sounds.
    required: false
    default: none
  msg_file:
    description:
      - Full path to a windows format text file containing the text to be spokend.  Use either msg or msg_file.  Optional so that you can use this module just to play sounds.
    required: false
    default: none
  voice:
    description:
      - Which voice to use. See notes for how to discover installed voices.  If the requested voice is not available the default voice will be used. Example voice names from Windows 10 are 'Microsoft Zira Desktop' and 'Microsoft Hazel Desktop'.
    required: false
    default: system default voice
  speech_speed:
    description:
      - How fast or slow to speak the text.  Must be an integer value in the range -10 to 10.  -10 is slowest, 10 is fastest.
    required: false
    default: 0
  start_sound_path:
    description:
      - Full path to a C(.wav) file containing a sound to play before the text is spoken.  Useful on conference calls to alert other speakers that ansible has something to say.
    required: false
    default: null
  end_sound_path:
    description:
      - Full path to a C(.wav) file containing a sound to play after the text has been spoken.  Useful on conference calls to alert other speakers that ansible has finished speaking.
    required: false
    default: null
author: "Jon Hawkesworth (@jhawkesworth)"
notes: 
   - Needs speakers or headphones to do anything useful.
   - To find which voices are installed, run the following powershell
     Add-Type -AssemblyName System.Speech
     $speech = New-Object -TypeName System.Speech.Synthesis.SpeechSynthesizer
     $speech.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo }
     $speech.Dispose()
   - Speech can be surprisingly slow, so its best to keep message text short.   
'''

EXAMPLES = '''
  # Warn of impending deployment
- win_say:
    msg: Warning, deployment commencing in 5 minutes, please log out.
  # Using a different voice and a start sound
- win_say:
    start_sound_path: 'C:\Windows\Media\ding.wav'
    msg: Warning, deployment commencing in 5 minutes, please log out.
    voice: Microsoft Hazel Desktop
  # example with start and end sound
- win_say:
    start_sound_path: 'C:\Windows\Media\Windows Balloon.wav'
    msg: "New software installed"
    end_sound_path: 'C:\Windows\Media\chimes.wav'
  # text from file example
- win_say:
    start_sound_path: 'C:\Windows\Media\Windows Balloon.wav'
    msg_text: AppData\Local\Temp\morning_report.txt 
    end_sound_path: 'C:\Windows\Media\chimes.wav'
'''
RETURN = '''
message_text:
    description: the text that the module attempted to speak
    returned: success
    type: string
    sample: "Warning, deployment commencing in 5 minutes."
voice:
    description: the voice used to speak the text.
    returned: success
    type: string
    sample: Microsoft Hazel Desktop
voice_info:
    description: the voice used to speak the text.
    returned: when requested voice could not be loaded
    type: string
    sample: Could not load voice TestVoice, using system default voice
'''

