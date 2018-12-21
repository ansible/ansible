#!powershell

# Copyright: (c) 2017, Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2

If(-not (Get-Command Get-DiskImage -ErrorAction SilentlyContinue)) {
    Fail-Json -message "win_disk_image requires Windows 8+ or Windows Server 2012+"
}

$parsed_args = Parse-Args $args -supports_check_mode $true

$result = @{changed=$false}

$image_path = Get-AnsibleParam $parsed_args "image_path" -failifempty $result
$state = Get-AnsibleParam $parsed_args "state" -default "present" -validateset "present","absent"
$check_mode = Get-AnsibleParam $parsed_args "_ansible_check_mode" -default $false

$di = Get-DiskImage $image_path

If($state -eq "present") {
    If(-not $di.Attached) {
      $result.changed = $true

      If(-not $check_mode) {
        $di = Mount-DiskImage $image_path -PassThru

        # the actual mount is async, so the CIMInstance result may not immediately contain the data we need
        $retry_count = 0
        While(-not $di.Attached -and $retry_count -lt 5) {
          Sleep -Seconds 1 | Out-Null
          $di = $di | Get-DiskImage
          $retry_count++
        }

        If(-not $di.Attached) {
          Fail-Json $result -message "Timed out waiting for disk to attach"
        }
     }
  }

  # FUTURE: detect/handle "ejected" ISOs
  # FUTURE: support explicit drive letter and NTFS in-volume mountpoints.
  # VHDs don't always auto-assign, and other system settings can prevent automatic assignment

  If($di.Attached) { # only try to get the mount_path if the disk is attached (
    If($di.StorageType -eq 1) { # ISO, we can get the mountpoint directly from Get-Volume
      $drive_letters = ($di | Get-Volume).DriveLetter
    }
    ElseIf($di.StorageType -in @(2,3)) { # VHD/VHDX, need Get-Disk + Get-Partition to discover mountpoint
      $drive_letters = ($di | Get-Disk | Get-Partition).DriveLetter
    }
    # remove any null entries (no drive letter)
    $drive_letters = $drive_letters | Where-Object { $_ }

    If(-not $drive_letters) {
      Fail-Json -message "Unable to retrieve drive letter from mounted image"
    }

    # mount_path is deprecated and will be removed in 2.11, use mount_paths which contains all the partitions instead
    $result.mount_path = $drive_letters[0] + ":\"
    $result.mount_paths = @($drive_letters | ForEach-Object { "$($_):\" })
  }
}
ElseIf($state -eq "absent") {
  If($di.Attached) {
    $result.changed = $true
    If(-not $check_mode) {
      Dismount-DiskImage $image_path | Out-Null
    }
  }
}

Exit-Json $result
