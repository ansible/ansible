#!powershell
# This file is part of Ansible
#
# Copyright 2016, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
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

# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;
$result = New-Object PSObject;
$msg = Get-AnsibleParam -obj $params -name "msg"
$msg_file = Get-AnsibleParam -obj $params -name "msg_file"
$start_sound_path = Get-AnsibleParam -obj $params -name "start_sound_path"
$end_sound_path = Get-AnsibleParam -obj $params -name "end_sound_path"
$voice = Get-AnsibleParam -obj $params -name "voice"
$speech_speed = Get-AnsibleParam -obj $params -name "speech_speed"
$speed = 0
$words = $null

if ($speech_speed -ne $null) {
   try {
     $speed = [convert]::ToInt32($speech_speed, 10)
   } catch {
       Fail-Json $result "speech_speed needs to a integer in the range -10 to 10.  The value $speech_speed could not be converted to an integer."

   }
   if ($speed -lt -10 -or $speed -gt 10) {
       Fail-Json $result "speech_speed needs to a integer in the range -10 to 10.  The value $speech_speed is outside this range."
   }
}


if ($msg_file -ne $null -and $msg -ne $null ) {
   Fail-Json $result "Please specify either msg_file or msg parameters, not both"
}

if ($msg_file -eq $null -and $msg -eq $null -and $start_sound_path -eq $null -and $end_sound_path -eq $null) {
   Fail-Json $result "No msg_file, msg, start_sound_path, or end_sound_path parameters have been specified.  Please specify at least one so the module has something to do"

}


if ($msg_file -ne $null) {
   if (Test-Path $msg_file) {
     $words = Get-Content $msg_file | Out-String
   } else {
     Fail-Json $result "Message file $msg_file could not be found or opened.  Ensure you have specified the full path to the file, and the ansible windows user has permission to read the file."
   }
}

if ($start_sound_path -ne $null) {
  if (Test-Path $start_sound_path) {
     (new-object Media.SoundPlayer $start_sound_path).playSync();
  } else {
     Fail-Json $result "Start sound file $start_sound_path could not be found or opened.  Ensure you have specified the full path to the file, and the ansible windows user has permission to read the file."
  }
}

if ($msg -ne $null) {
   $words = $msg
} 

if ($words -ne $null) {
   Add-Type -AssemblyName System.speech
   $tts = New-Object System.Speech.Synthesis.SpeechSynthesizer
   if ($voice -ne $null) {
      try {
         $tts.SelectVoice($voice)
      } catch  [System.Management.Automation.MethodInvocationException] {
         Set-Attr $result "voice_info" "Could not load voice $voice, using system default voice."
      }
   }

   Set-Attr $result "voice" $tts.Voice.Name
   if ($speed -ne 0) {
      $tts.Rate = $speed
   }
   $tts.Speak($words)
   $tts.Dispose()
}

if ($end_sound_path -ne $null) {
  if (Test-Path $end_sound_path) {
     (new-object Media.SoundPlayer $end_sound_path).playSync();
  } else {
     Fail-Json $result "End sound file $start_sound_path could not be found or opened.  Ensure you have specified the full path to the file, and the ansible windows user has permission to read the file."
  }
}

Set-Attr $result "changed" $false;
Set-Attr $result "message_text" $words;

Exit-Json $result;
