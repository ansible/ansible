#!powershell
# This file is part of Ansible

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.FileUtil
#Requires -Module Ansible.ModuleUtils.LinkUtil

function DateTo-Timestamp($start_date, $end_date) {
    if ($start_date -and $end_date) {
        return (New-TimeSpan -Start $start_date -End $end_date).TotalSeconds
    }
}

$params = Parse-Args $args -supports_check_mode $true

$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -aliases "dest","name"
$get_md5 = Get-AnsibleParam -obj $params -name "get_md5" -type "bool" -default $false
$get_checksum = Get-AnsibleParam -obj $params -name "get_checksum" -type "bool" -default $true
$checksum_algorithm = Get-AnsibleParam -obj $params -name "checksum_algorithm" -type "str" -default "sha1" -validateset "md5","sha1","sha256","sha384","sha512"

$result = @{
    changed = $false
    stat = @{
        exists = $false
    }
}

# get_md5 will be an undocumented option in 2.9 to be removed at a later
# date if possible (3.0+)
if (Get-Member -inputobject $params -name "get_md5") {
    Add-DepreactionWarning -obj $result -message "get_md5 has been deprecated along with the md5 return value, use get_checksum=True and checksum_algorithm=md5 instead" -version 2.9
}

$info = Get-FileItem -path $path
If ($info -ne $null) {
    $epoch_date = Get-Date -Date "01/01/1970"
    $attributes = @()
    foreach ($attribute in ($info.Attributes -split ',')) {
        $attributes += $attribute.Trim()
    }

    # default values that are always set, specific values are set below this
    # but are kept commented for easier readability
    $stat = @{
        exists = $true
        attributes = $info.Attributes.ToString()
        isarchive = ($attributes -contains "Archive")
        isdir = $false
        ishidden = ($attributes -contains "Hidden")
        isjunction = $false
        islnk = $false
        isreadonly = ($attributes -contains "ReadOnly")
        isreg = $false
        isshared = $false
        nlink = 1  # Number of links to the file (hard links), overriden below if islnk
        # lnk_target = islnk or isjunction Target of the symlink. Note that relative paths remain relative
        # lnk_source = islnk os isjunction Target of the symlink normalized for the remote filesystem
        hlnk_targets = @()
        creationtime = (DateTo-Timestamp -start_date $epoch_date -end_date $info.CreationTime)
        lastaccesstime = (DateTo-Timestamp -start_date $epoch_date -end_date $info.LastAccessTime)
        lastwritetime = (DateTo-Timestamp -start_date $epoch_date -end_date $info.LastWriteTime)
        # size = a file and directory - calculated below
        path = $info.FullName
        filename = $info.Name
        # extension = a file
        # owner = set outsite this dict in case it fails
        # sharename = a directory and isshared is True
        # checksum = a file and get_checksum: True
        # md5 = a file and get_md5: True
    }
    $stat.owner = $info.GetAccessControl().Owner

    # values that are set according to the type of file
    if ($info.PSIsContainer) {
        $stat.isdir = $true
        $share_info = Get-WmiObject -Class Win32_Share -Filter "Path='$($stat.path -replace '\\', '\\')'"
        if ($share_info -ne $null) {
            $stat.isshared = $true
            $stat.sharename = $share_info.Name
        }

        $dir_files_sum = Get-ChildItem $stat.path -Recurse | Measure-Object -property length -sum
        if ($dir_files_sum -eq $null) {
            $stat.size = 0
        } else {
            $stat.size = $dir_files_sum.Sum
        }
    } else {
        $stat.extension = $info.Extension
        $stat.isreg = $true
        $stat.size = $info.Length

        if ($get_md5) {
            try {
                $stat.md5 = Get-FileChecksum -path $path -algorithm "md5"
            } catch {
                Fail-Json -obj $result -message "failed to get MD5 hash of file, remove get_md5 to ignore this error: $($_.Exception.Message)"
            }
        }
        if ($get_checksum) {
            try {
                $stat.checksum = Get-FileChecksum -path $path -algorithm $checksum_algorithm
            } catch {
                Fail-Json -obj $result -message "failed to get hash of file, set get_checksum to False to ignore this error: $($_.Exception.Message)"
            }
        }
    }

    # Get symbolic link, junction point, hard link info
    Load-LinkUtils
    try {
        $link_info = Get-Link -link_path $info.FullName
    } catch {
        Add-Warning -obj $result -message "Failed to check/get link info for file: $($_.Exception.Message)"
    }
    if ($link_info -ne $null) {
        switch ($link_info.Type) {
            "SymbolicLink" {
                $stat.islnk = $true
                $stat.isreg = $false
                $stat.lnk_target = $link_info.TargetPath
                $stat.lnk_source = $link_info.AbsolutePath                
                break
            }
            "JunctionPoint" {
                $stat.isjunction = $true
                $stat.isreg = $false
                $stat.lnk_target = $link_info.TargetPath
                $stat.lnk_source = $link_info.AbsolutePath                
                break
            }
            "HardLink" {
                $stat.lnk_type = "hard"
                $stat.nlink = $link_info.HardTargets.Count

                # remove current path from the targets
                $hlnk_targets = $link_info.HardTargets | Where-Object { $_ -ne $stat.path }
                $stat.hlnk_targets = @($hlnk_targets)
                break
            }
        }
    }

    $result.stat = $stat
}

Exit-Json $result
