#!powershell

# Copyright: 2019, rnsc(@rnsc) <github@rnsc.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -OSVersion 6.3

$spec = @{
    options = @{
        drive_letter = @{ type = "str"; required = $true }
        state = @{ type = "str"; choices = "absent", "present"; default = "present"; }
        settings = @{
            type = "dict"
            required = $false
            options = @{
                minimum_file_size = @{ type = "int"; default = 32768 }
                minimum_file_age_days = @{ type = "int"; default = 2 }
                no_compress = @{ type = "bool"; required = $false; default = $false }
                optimize_in_use_files = @{ type = "bool"; required = $false; default = $false }
                verify = @{ type = "bool"; required = $false; default = $false }
            }
        }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$drive_letter = $module.Params.drive_letter
$state = $module.Params.state
$settings = $module.Params.settings

$module.Result.changed = $false
$module.Result.reboot_required = $false
$module.Result.msg = ""

function Set-DataDeduplication($volume, $state, $settings, $dedup_job) {

  $current_state = 'absent'

  try {
    $dedup_info = Get-DedupVolume -Volume "$($volume.DriveLetter):"
  } catch {
    $dedup_info = $null
  }

  if ($dedup_info.Enabled) {
    $current_state = 'present'
  }

  if ( $state -ne $current_state ) {
    if( -not $module.CheckMode) {
      if($state -eq 'present') {
        # Enable-DedupVolume -Volume <String>
        Enable-DedupVolume -Volume "$($volume.DriveLetter):"
      } elseif ($state -eq 'absent') {
        Disable-DedupVolume -Volume "$($volume.DriveLetter):"
      }
    }
    $module.Result.changed = $true
  }

  if ($state -eq 'present') {
    if ($null -ne $settings) {
      Set-DataDedupJobSettings -volume $volume -settings $settings
    }
  }
}

function Set-DataDedupJobSettings ($volume, $settings) {

  try {
    $dedup_info = Get-DedupVolume -Volume "$($volume.DriveLetter):"
  } catch {
    $dedup_info = $null
  }

  ForEach ($key in $settings.keys) {

    # See Microsoft documentation:
    # https://docs.microsoft.com/en-us/powershell/module/deduplication/set-dedupvolume?view=win10-ps

    $update_key = $key
    $update_value = $settings.$($key)
    # Transform Ansible style options to Powershell params
    $update_key = $update_key -replace('_', '')

    if ($update_key -eq "MinimumFileSize" -and $update_value -lt 32768) {
      $update_value = 32768
    }

    $current_value = ($dedup_info | Select-Object -ExpandProperty $update_key)

    if ($update_value -ne $current_value) {
      $command_param = @{
        $($update_key) = $update_value
      }

      # Set-DedupVolume -Volume <String>`
      #                 -NoCompress <bool> `
      #                 -MinimumFileAgeDays <UInt32> `
      #                 -MinimumFileSize <UInt32> (minimum 32768)
      if( -not $module.CheckMode ) {
        Set-DedupVolume -Volume "$($volume.DriveLetter):" @command_param
      }

      $module.Result.changed = $true
    }
  }

}

# Install required feature
$feature_name = "FS-Data-Deduplication"
if( -not $module.CheckMode) {
  $feature = Install-WindowsFeature -Name $feature_name

  if ($feature.RestartNeeded -eq 'Yes') {
    $module.Result.reboot_required = $true
    $module.FailJson("$feature_name was installed but requires Windows to be rebooted to work.")
  }
}

$volume = Get-Volume -DriveLetter $drive_letter

Set-DataDeduplication -volume $volume -state $state -settings $settings -dedup_job $dedup_job

$module.ExitJson()
