#!powershell

# Copyright: 2019, rnsc(@rnsc) <github@rnsc.be>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.SID

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $false

$drive_letter = Get-AnsibleParam -obj $params -name 'drive_letter' -type 'str' -failifempty $true
$state = Get-AnsibleParam -obj $params -name 'state' -type 'str' -default 'enabled'
$settings = Get-AnsibleParam -obj $params -name 'settings' -type 'list' -default $null
$dedup_job = Get-AnsibleParam -obj $params -name 'dedup_job' -type 'list' -default $null

# In theory it works on Windows 2012, but this was only developed to work
# from 2012R2 and higher.
if ([System.Environment]::OSVersion.Version -lt [Version]"6.3.9600.0") {
    Fail-Json -message "win_data_deduplication requires Windows Server 2012R2 or higher."
}

$result = @{
	changed = $false
	reboot_required= $false
}

function Set-DataDeduplication($volume, $state, $settings, $dedup_job) {

	$current_state = 'disabled'

	try {
		$dedup_info = Get-DedupVolume -Volume "$($volume.DriveLetter):"
	} catch {
		$dedup_info = $null
	}

	if($null -ne $dedup_info) {
		if ($dedup_info.Enabled) {
			$current_state = 'enabled'
		}
	} else {
		$current_state = $null
	}

	if (($null -ne $current_state) -and ($state -ne $current_state)) {
		if($state -eq 'enabled') {
			try {
				# Enable-DedupVolume -Volume <String>
				Enable-DedupVolume -Volume "$($volume.DriveLetter):"
			} catch {
				Fail-Json $result $_.Exception.Message
			}
		} elseif ($state -eq 'disabled') {
			try {
				Disable-DedupVolume -Volume "$($volume.DriveLetter):"
			} catch {
				Fail-Json $result $_.Exception.Message
			}
		} else {
			Fail-Json $result "Unsupported state option, it can only be 'enabled' or 'disabled'."
		}

		$result.msg += " Deduplication on volume: "+$volume.DriveLetter+" set to: $state"
		$result.changed = $true
	}

	if ($state -eq 'enabled') {
    if ($null -ne $settings) {
      Set-DataDedupJobSettings -volume $volume -settings $settings
    }

    if ($null -ne $dedup_job) {
			Start-DataDedupJob -volume $volume -dedup_job $dedup_job
    }
	}
}

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

			# Set-DedupVolume -Volume <String>`
			#                 -NoCompress <bool> `
			#                 -MinimumFileAgeDays <UInt32> `
			#                 -MinimumFileSize <UInt32> (minimum 32768)
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

function Start-DataDedupJob($volume) {

	$dedup_job_queue = Get-DedupJob -Volume "$($volume.DriveLetter):" -ErrorAction SilentlyContinue

	if(( $dedup_job_queue | Select-Object -ExpandProperty State) -ne "Queued" ) {

		$command_param = @{}

		ForEach ($key in $dedup_job.keys) {

			$update_key = $key
			$update_value = $dedup_job.$($key)

			$command_param.Add($($update_key), $update_value)

		}

		# Start-DedupJob -Volume <String> `
		# 	       -Type <String>
		$dedup_job_start = Start-DedupJob -Volume "$($volume.DriveLetter):" @command_param
		$result.msg += " DedupJob "+($dedup_job_start | Select-Object -ExpandProperty State)

		$result.changed = $true
	} else {
		$result.msg += " A DedupJob is already queued for that volume."
	}

}


# Install required feature
$feature_name = "FS-Data-Deduplication"
$feature = Install-WindowsFeature -Name $feature_name

if ($feature.RestartNeeded -eq 'Yes') {
	$result.reboot_required = $true
  Fail-Json $result "$feature_name was installed but requires Windows to be rebooted to work."
  Exit-Json -obj $result
}

try {
	$volume = Get-Volume -DriveLetter $drive_letter
} catch {
	Fail-Json $result $_.Exception.Message
}
if ($null -ne $volume) {
  $result.msg += "Start setting FileDeduplication"
  Set-DataDeduplication -volume $volume -state $state -settings $settings -dedup_job $dedup_job
}

Exit-Json -obj $result
