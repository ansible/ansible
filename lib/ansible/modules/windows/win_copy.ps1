#!powershell
# This file is part of Ansible
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

$params = Parse-Args $args -supports_check_mode $true

$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$src = Get-AnsibleParam -obj $params -name "src" -type "path" -failifempty $true
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path" -failifempty $true
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $true
$original_basename = Get-AnsibleParam -obj $params -name "original_basename" -type "str"

# original_basename gets set if src and dest are dirs
# but includes subdir if the source folder contains sub folders
# e.g. you could get subdir/foo.txt

$result = @{
    changed = $false
    dest = $dest
    original_basename = $original_basename
    src = $src
}

if (($force -eq $false) -and (Test-Path -Path $dest)) {
    $result.msg = "file already exists"
    Exit-Json $result
}

Function Copy-Folder($src, $dest) {
    if (Test-Path -Path $dest) {
        if (-not (Get-Item -Path $dest -Force).PSIsContainer) {
            Fail-Json $result "If src is a folder, dest must also be a folder. src: $src, dest: $dest"
        }
    } else {
        try {
            New-Item -Path $dest -ItemType Directory -Force -WhatIf:$check_mode
            $result.changed = $true
        } catch {
            Fail-Json $result "Failed to create new folder $dest $($_.Exception.Message)"
        }
    }

    foreach ($item in Get-ChildItem -Path $src) {
        $dest_path = Join-Path -Path $dest -ChildPath $item.PSChildName
        if ($item.PSIsContainer) {
            Copy-Folder -src $item.FullName -dest $dest_path
        } else {
            Copy-File -src $item.FullName -dest $dest_path
        }
    }
}

Function Copy-File($src, $dest) {
    if (Test-Path -Path $dest) {
        if ((Get-Item -Path $dest -Force).PSIsContainer) {
            Fail-Json $result "If src is a file, dest must also be a file. src: $src, dest: $dest"
        }
    }

    $src_checksum = Get-FileChecksum -Path $src
    $dest_checksum = Get-FileChecksum -Path $dest
    if ($src_checksum -ne $dest_checksum) {
        try {
            Copy-Item -Path $src -Destination $dest -Force -WhatIf:$check_mode
        } catch {
            Fail-Json $result "Failed to copy file: $($_.Exception.Message)"
        }
        $result.changed = $true
    }

    # Verify the file we copied is the same
    $dest_checksum_verify = Get-FileChecksum -Path $dest
    if (-not ($check_mode) -and ($src_checksum -ne $dest_checksum_verify)) {
        Fail-Json $result "Copied file does not match checksum. src: $src_checksum, dest: $dest_checksum_verify. Failed to copy file from $src to $dest"
    }
}

Function Get-FileSize($path) {
    $file = Get-Item -Path $path -Force
    $size = $null
    if ($file.PSIsContainer) {
        $dir_files_sum = Get-ChildItem $file.FullName -Recurse
        if ($dir_files_sum -eq $null -or ($dir_files_sum.PSObject.Properties.name -contains 'length' -eq $false)) {
            $size = 0
        } else {
            $size = ($dir_files_sum | Measure-Object -property length -sum).Sum
        }
    } else {
        $size = $file.Length
    }

    $size
}

if (-not (Test-Path -Path $src)) {
    Fail-Json $result "Cannot copy src file: $src as it does not exist"
}

# If copying from remote we need to get the original folder path and name and change dest to this path
if ($original_basename) {
    $parent_path = Split-Path -Path $original_basename -Parent
    if ($parent_path.length -gt 0) {
        $dest_folder = Join-Path -Path $dest -ChildPath $parent_path
        try {
            New-Item -Path $dest_folder -Type directory -Force -WhatIf:$check_mode
            $result.changed = $true
        } catch {
            Fail-Json $result "Failed to create directory $($dest_folder): $($_.Exception.Message)"
        }
    }

    if ((Get-Item -Path $dest -Force).PSIsContainer) {
        $dest = Join-Path $dest -ChildPath $original_basename
    }
}

# If the source is a container prepare for some recursive magic
if ((Get-Item -Path $src -Force).PSIsContainer) {
    if (Test-Path -Path $dest) {
        if (-not (Get-Item -Path $dest -Force).PSIsContainer) {
            Fail-Json $result "If src is a folder, dest must also be a folder. src: $src, dest: $dest"
        }
    }

    $folder_name = (Get-Item -Path $src -Force).Name
    $dest_path = Join-Path -Path $dest -ChildPath $folder_name
    Copy-Folder -src $src -dest $dest_path
    if ($result.changed -eq $true) {
        $result.operation = "folder_copy"
    }
} else {
    Copy-File -src $src -dest $dest
    if ($result.changed -eq $true) {
        $result.operation = "file_copy"
    }
    $result.original_basename = (Get-Item -Path $src -Force).Name
    $result.checksum = Get-FileChecksum -Path $src
}

if ($check_mode) {
    # When in check mode the dest won't exit, just get the source size
    $result.size = Get-FileSize -path $src
} else {
    $result.size = Get-FileSize -path $dest
}

Exit-Json $result
