#!powershell

# Copyright: (c) 2016, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
   options = @{
      msg = @{ type = "str"  }
      msg_file = @{ type = "path"  }
      start_sound_path = @{ type = "path"  }
      end_sound_path = @{ type = "path"  }
      voice = @{ type = "str"  }
      speech_speed = @{ type = "int"; default = 0  }
   }
   supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)


$msg = $module.params.msg
$msg_file = $module.params.msg_file
$start_sound_path = $module.params.start_sound_path
$end_sound_path = $module.params.end_sound_path
$voice = $module.params.voice
$speech_speed = $module.params.speech_speed

$module.Result.changed = $false

$words = $null

if ($speech_speed -lt -10 -or $speech_speed -gt 10) {
   $module.FailJson("speech_speed needs to be an integer in the range -10 to 10.  The value $speech_speed is outside this range.")
}

if ($msg_file -and $msg) {
   $module.FailJson("Please specify either msg_file or msg parameters, not both")
}

if (-not $msg_file -and -not $msg -and -not $start_sound_path -and -not $end_sound_path) {
   $module.FailJson("No msg_file, msg, start_sound_path, or end_sound_path parameters have been specified.  Please specify at least one so the module has something to do")
}

if ($msg_file) {
   if (Test-Path -Path $msg_file) {
      $words = Get-Content $msg_file | Out-String
   } else {
      $module.FailJson("Message file $msg_file could not be found or opened.  Ensure you have specified the full path to the file, and the ansible windows user has permission to read the file.")
   }
}

if ($start_sound_path) {
   if (Test-Path -Path $start_sound_path) {
      if (-not $module.CheckMode) {
         (new-object Media.SoundPlayer $start_sound_path).playSync()
      }
   } else {
      $module.FailJson("Start sound file $start_sound_path could not be found or opened.  Ensure you have specified the full path to the file, and the ansible windows user has permission to read the file.")
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
         $module.Result.voice_info = "Could not load voice '$voice', using system default voice."
         $module.Warn("Could not load voice '$voice', using system default voice.")
      }
   }

   $module.Result.voice = $tts.Voice.Name
   if ($speech_speed -ne 0) {
      $tts.Rate = $speech_speed
   }
   if (-not $module.CheckMode) {
       $tts.Speak($words)
   }
   $tts.Dispose()
}

if ($end_sound_path) {
   if (Test-Path -Path $end_sound_path) {
      if (-not $module.CheckMode) {
         (new-object Media.SoundPlayer $end_sound_path).playSync()
      }
   } else {
      $module.FailJson("End sound file $start_sound_path could not be found or opened.  Ensure you have specified the full path to the file, and the ansible windows user has permission to read the file.")
   }
}

$module.Result.message_text = $words

$module.ExitJson()
