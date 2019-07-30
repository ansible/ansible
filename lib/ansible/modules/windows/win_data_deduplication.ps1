#!powershell

# Copyright: 2019, rnsc(@rnsc) <github@rnsc.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $false

$drive_letter = Get-AnsibleParam -obj $params -name 'drive_letter' -type 'str' -failifempty $true
$enabled = Get-AnsibleParam -obj $params -name 'enabled' -type 'bool' -default $true
$settings = Get-AnsibleParam -obj $params -name 'settings' -type 'list' -default $null
$dedup_job = Get-AnsibleParam -obj $params -name 'dedup_job' -type 'list' -default $null

$result = @{
	changed = $false
}

# Enable-DedupVolume -Volume <String>

function Set-DataDeduplication($volume) {

	try {
		$dedup_info = Get-DedupVolume -Volume "$($volume.DriveLetter):"
	} catch {
		$dedup_info = $null
	}

	if($null -ne $dedup_info) {
		$is_enabled = $dedup_info.Enabled
	} else {
		$is_enabled = $null
	}

	if ($is_enabled -ne $enabled) {
		if($enabled) {
			try {
				Enable-DedupVolume -Volume "$($volume.DriveLetter):"
			} catch {
				Fail-Json $result $_.Exception.Message
			}
		} else {
			try {
				Disable-DedupVolume -Volume "$($volume.DriveLetter):"
			} catch {
				Fail-Json $result $_.Exception.Message
			}
		}
		$result.msg += " Deduplication on volume: "+$drive.Name+" set to $enabled"
		$result.changed = $true
	}

}


# Set-DedupVolume -Volume <String>`
#                 -NoCompress <bool> `
#                 -MinimumFileAgeDays <UInt32> `
#                 -MinimumFileSize <UInt32> (minimum 32768)

function Set-DataDedupJobSettings ($volume) {

	try {
		$dedup_info = Get-DedupVolume -Volume "$($volume.DriveLetter):"
	} catch {
		$dedup_info = $null
	}

	ForEach ($key in $settings.keys) {
		$update_key = $key
		$update_value = $settings.$($key)

		if ($update_key -eq "MinimumFileSize" -and $update_value -lt 32768) {
			$update_value = 32768
		}

		try {
			$current_value = ($dedup_info | Select-Object -ExpandProperty $update_key)
		} catch {
			$current_value = $null
		}

		if ($update_value -ne $current_value) {
			$command_param = @{
				$($update_key) = $update_value
			}

			try {
				Set-DedupVolume -Volume "$($volume.DriveLetter):" @command_param
				$result.msg += " Setting DedupVolume settings for $update_key"

			} catch {
				Fail-Json $result $_.Exception.Message
			}

			$result.changed = $true
		}
	}

}

# Start-DedupJob -Volume <String> `
# 	       -Type <String>
function Start-DataDedupJob($volume) {

	$dedup_job_queue = Get-DedupJob -Volume "$($volume.DriveLetter):" -ErrorAction SilentlyContinue

	if(( $dedup_job_queue | Select-Object -ExpandProperty State) -ne "Queued" ) {

		$command_param = @{}

		ForEach ($key in $dedup_job.keys) {

			$update_key = $key
			$update_value = $dedup_job.$($key)

			$command_param.Add($($update_key), $update_value)

		}

		$dedup_job_start = Start-DedupJob -Volume "$($volume.DriveLetter):" @command_param
		$result.msg += " DedupJob "+($dedup_job_start | Select-Object -ExpandProperty State)

		$result.changed = $true
	} else {
		$result.msg += " A DedupJob is already queued for that drive."
	}

}

function DataDeduplication($volume) {

	if ($null -ne $enabled) {
		Set-DataDeduplication -drive $volume
	}

	if ($null -ne $settings -and $enabled) {
		Set-DataDedupJobSettings -drive $volume
	}

	if ($null -ne $dedup_job -and $enabled) {
		Start-DataDedupJob -drive $volume
	}

}

# Check if FS-Data-Deduplication is installed
$feature_name = "FS-Data-Deduplication"
$feature = Get-WindowsFeature -Name $feature_name

if (!$feature.Installed) {
  Fail-Json $result "This module requires Windows feature '$feature_name' to be installed."
  Exit-Json -obj $result
}

$volume = Get-Volume -DriveLetter $drive_letter
if ($volume) {
  $result.msg += "Start setting FileDeduplication"
  DataDeduplication -drive $volume
}

Exit-Json -obj $result
