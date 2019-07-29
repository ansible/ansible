#!powershell

# Copyright: (c) 2019, rnsc <github@rnsc.be>
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

function Set-DataDeduplication($drive) {

	try {
		$dedup_info = Get-DedupVolume -Volume "$($drive.Name):"
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
				Enable-DedupVolume -Volume "$($drive.Name):"
			} catch {
				Fail-Json $result $_.Exception.Message
			}
		} else {
			try {
				Disable-DedupVolume -Volume "$($drive.Name):"
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

function Set-DataDedupJobSettings ($drive) {

	try {
		$dedup_info = Get-DedupVolume -Volume "$($drive.Name):"
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
				Set-DedupVolume -Volume "$($drive.Name):" @command_param
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
function Start-DataDedupJob($drive) {

	$dedup_job_queue = Get-DedupJob -Volume "$($drive.Name):" -ErrorAction SilentlyContinue

	if(( $dedup_job_queue | Select-Object -ExpandProperty State) -ne "Queued" ) {

		$command_param = @{}

		ForEach ($key in $dedup_job.keys) {

			$update_key = $key
			$update_value = $dedup_job.$($key)

			$command_param.Add($($update_key), $update_value)

		}

		$dedup_job_start = Start-DedupJob -Volume "$($drive.Name):" @command_param
		$result.msg += " DedupJob "+($dedup_job_start | Select-Object -ExpandProperty State)

		$result.changed = $true
	} else {
		$result.msg += " A DedupJob is already queued for that drive."
	}

}

function DataDeduplication($drive) {

	if ($null -ne $enabled) {
		Set-DataDeduplication -drive $drive
	}

	if ($null -ne $settings -and $enabled) {
		Set-DataDedupJobSettings -drive $drive
	}

	if ($null -ne $dedup_job -and $enabled) {
		Start-DataDedupJob -drive $drive
	}

}

# Check if FS-Data-Deduplication is installed
$feature_name = "FS-Data-Deduplication"
$feature = Get-WindowsFeature -Name $feature_name

if (!$feature.Installed) {
  Fail-Json $result "This module requires Windows feature '$feature_name' to be installed."
  Exit-Json -obj $result
}

$drive = Get-PSDrive -Name $drive_letter
if ($drive) {
  $result.msg += "Start setting FileDeduplication"
  DataDeduplication -drive $drive
}

Exit-Json -obj $result
