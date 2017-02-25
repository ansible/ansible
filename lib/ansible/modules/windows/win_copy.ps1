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
$original_basename = Get-AnsibleParam -obj $params -name "original_basename" -type "str" -failifempty $true

$result = @{
    changed = $FALSE
    original_basename = $original_basename
    src = $src
    dest = $dest
}

# original_basename gets set if src and dest are dirs
# but includes subdir if the source folder contains sub folders
# e.g. you could get subdir/foo.txt

if (($force -eq $false) -and (Test-Path -Path $dest)) {
    $result.msg = "file already exists"
    Exit-Json $result
}

# detect if doing recursive folder copy and create any non-existent destination sub folder
$parent = Split-Path -Path $original_basename -Parent
if ($parent.length -gt 0)
{
    $dest_folder = Join-Path $dest $parent
    New-Item -Path $dest_folder -Type Directory -Force -WhatIf:$check_mode
}

# if $dest is a dir, append $original_basename so the file gets copied with its intended name.
if (Test-Path -Path $dest -PathType Container)
{
    $dest = Join-Path -Path $dest -ChildPath $original_basename
}

$orig_checksum = Get-FileChecksum ($dest)
$src_checksum = Get-FileChecksum ($src)

If ($src_checksum.Equals($orig_checksum))
{
    # if both are "3" then both are folders, ok to copy
    If ($src_checksum.Equals("3"))
    {
       # New-Item -Force creates subdirs for recursive copies
       New-Item -Path $dest -Type File -Force -WhatIf:$check_mode
       Copy-Item -Path $src -Destination $dest -Force -WhatIf:$check_mode
       $result.changed = $true
       $result.operation = "folder_copy"
    }

}
ElseIf (-Not $src_checksum.Equals($orig_checksum))
{
    If ($src_checksum.Equals("3"))
    {
        Fail-Json $result "If src is a folder, dest must also be a folder"
    }
    # The checksums don't match, there's something to do
    Copy-Item -Path $src -Destination $dest -Force -WhatIf:$check_mode

    $result.changed = $true
    $result.operation = "file_copy"
}

# Verify before we return that the file has changed
$dest_checksum = Get-FileChecksum($dest)
If (-Not $src_checksum.Equals($dest_checksum) -And -Not $check_mode)
{
    Fail-Json $result "src checksum $src_checksum did not match dest_checksum $dest_checksum, failed to place file $original_basename in $dest"
}

$info = Get-Item $dest
$result.size = $info.Length
$result.src = $src
$result.dest = $dest

Exit-Json $result
