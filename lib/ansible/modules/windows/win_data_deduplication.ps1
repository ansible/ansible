#!powershell

# Copyright: 2019, rnsc(@rnsc) <github@rnsc.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

#Requires -Module Ansible.ModuleUtils.Legacy
#AnsibleRequires -OSVersion 6.3

$params = Parse-Args $args -supports_check_mode $true

$drive_letter = Get-AnsibleParam -obj $params -name 'drive_letter' -type 'str' -failifempty $true
$state = Get-AnsibleParam -obj $params -name 'state' -type 'str' -default 'present'
$settings = Get-AnsibleParam -obj $params -name 'settings' -type 'dict' -default $null
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type 'bool' -default $false

$result = @{
  changed = $false
  reboot_required = $false
	msg = ""
}

function Set-DataDeduplication($volume, $state, $settings, $dedup_job) {

  $current_state = 'absent'

	try {
    $dedup_info = Get-DedupVolume -Volume "$($volume.DriveLetter):"
  } catch {
    $dedup_info = $null
  }

  if($null -ne $dedup_info) {
    if ($dedup_info.Enabled) {
      $current_state = 'present'
    }
  } else {
    $current_state = $null
  }

  if ( $state -ne $current_state ) {
		if( -not $check_mode) {
			if($state -eq 'present') {
				# Enable-DedupVolume -Volume <String>
				Enable-DedupVolume -Volume "$($volume.DriveLetter):"
			} elseif ($state -eq 'absent') {
				Disable-DedupVolume -Volume "$($volume.DriveLetter):"
			} else {
				Fail-Json $result "Unsupported state option, it can only be 'present' or 'absent'."
			}
		}
    $result.msg += " Deduplication on volume: "+$volume.DriveLetter+" set to: $state"
    $result.changed = $true
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
			if( -not $check_mode) {
				Set-DedupVolume -Volume "$($volume.DriveLetter):" @command_param
			}
			$result.msg += " Setting DedupVolume settings for $update_key"

      $result.changed = $true
    }
  }

}

# Install required feature
$feature_name = "FS-Data-Deduplication"
if(!$check_mode) {
	$feature = Install-WindowsFeature -Name $feature_name

	if ($feature.RestartNeeded -eq 'Yes') {
		$result.reboot_required = $true
		Fail-Json $result "$feature_name was installed but requires Windows to be rebooted to work."
	}
}

$volume = Get-Volume -DriveLetter $drive_letter

Set-DataDeduplication -volume $volume -state $state -settings $settings -dedup_job $dedup_job

Exit-Json -obj $result
