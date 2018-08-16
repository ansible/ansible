#!powershell

# Copyright: (c) 2016, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$msg = Get-AnsibleParam -obj $params -name "msg" -type "str"
$msg_file = Get-AnsibleParam -obj $params -name "msg_file" -type "path"
$start_sound_path = Get-AnsibleParam -obj $params -name "start_sound_path" -type "path"
$end_sound_path = Get-AnsibleParam -obj $params -name "end_sound_path" -type "path"
$voice = Get-AnsibleParam -obj $params -name "voice" -type "str"
$speech_speed = Get-AnsibleParam -obj $params -name "speech_speed" -type "int" -default 0

$result = @{
    changed = $false
}

$words = $null

f ($speech_speed -lt -10 -or $speech_speed -gt 10) {
   Fail-Json $result "speech_speed needs to a integer in the range -10 to 10.  The value $speech_speed is outside this range."
}

if ($msg_file -and $msg) {
   Fail-Json $result "Please specify either msg_file or msg parameters, not both"
}

if (-not $msg_file -and -not $msg -and -not $start_sound_path -and -not $end_sound_path) {
   Fail-Json $result "No msg_file, msg, start_sound_path, or end_sound_path parameters have been specified.  Please specify at least one so the module has something to do"
}

if ($msg_file) {
   if (Test-Path -Path $msg_file) {
      $words = Get-Content $msg_file | Out-String
   } else {
      Fail-Json $result "Message file $msg_file could not be found or opened.  Ensure you have specified the full path to the file, and the ansible windows user has permission to read the file."
   }
}

if ($start_sound_path) {
   if (Test-Path -Path $start_sound_path) {
      if (-not $check_mode) {
         (new-object Media.SoundPlayer $start_sound_path).playSync()
      }
   } else {
      Fail-Json $result "Start sound file $start_sound_path could not be found or opened.  Ensure you have specified the full path to the file, and the ansible windows user has permission to read the file."
   }
}

if ($msg) {
   $words = $msg
}

if ($words) {
   Add-Type -AssemblyName System.speech
   $tts = New-Object System.Speech.Synthesis.SpeechSynthesizer
   if ($voice) {
      try {
         $tts.SelectVoice($voice)
      } catch  [System.Management.Automation.MethodInvocationException] {
         $result.voice_info = "Could not load voice $voice, using system default voice."
      }
   }

   $result.voice = $tts.Voice.Name
   if ($speech_speed -ne 0) {
      $tts.Rate = $speech_speed
   }
   if (-not $check_mode) {
       $tts.Speak($words)
   }
   $tts.Dispose()
}

if ($end_sound_path) {
   if (Test-Path -Path $end_sound_path) {
      if (-not $check_mode) {
         (new-object Media.SoundPlayer $end_sound_path).playSync()
      }
   } else {
      Fail-Json $result "End sound file $start_sound_path could not be found or opened.  Ensure you have specified the full path to the file, and the ansible windows user has permission to read the file."
   }
}

$result.message_text = $words

Exit-Json $result
