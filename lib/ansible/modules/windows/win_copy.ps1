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

$params = Parse-Args $args

$src= Get-Attr $params "src" $FALSE
If ($src -eq $FALSE)
{
    Fail-Json (New-Object psobject) "missing required argument: src"
}

$dest= Get-Attr $params "dest" $FALSE
If ($dest -eq $FALSE)
{
    Fail-Json (New-Object psobject) "missing required argument: dest"
}

$original_basename = Get-Attr $params "original_basename" $FALSE
If ($original_basename -eq $FALSE)
{
    Fail-Json (New-Object psobject) "missing required argument: original_basename "
}

$result = New-Object psobject @{
    changed = $FALSE
    original_basename = $original_basename
}

# original_basename gets set if src and dest are dirs
# but includes subdir if the source folder contains sub folders
# e.g. you could get subdir/foo.txt 

# detect if doing recursive folder copy and create any non-existent destination sub folder
$parent = Split-Path -Path $original_basename -Parent
if ($parent.length -gt 0) 
{
    $dest_folder = Join-Path $dest $parent
    New-Item -Force $dest_folder -Type directory
}

# if $dest is a dir, append $original_basename so the file gets copied with its intended name.
if (Test-Path $dest -PathType Container)
{
    $dest = Join-Path $dest $original_basename
}

$dest_checksum = Get-FileChecksum ($dest)
$src_checksum = Get-FileChecksum ($src)

If ($src_checksum.Equals($dest_checksum))
{
    # if both are "3" then both are folders, ok to copy 
    If ($src_checksum.Equals("3")) 
    {
       # New-Item -Force creates subdirs for recursive copies
       New-Item -Force $dest -Type file
       Copy-Item -Path $src -Destination $dest -Force
       $result.operation = "folder_copy"
    }

}
ElseIf (! $src_checksum.Equals($dest_checksum))
{
    If ($src_checksum.Equals("3")) 
    {
       Fail-Json (New-Object psobject) "If src is a folder, dest must also be a folder"
    }
    # The checksums don't match, there's something to do
    Copy-Item -Path $src -Destination $dest -Force
    $result.operation = "file_copy"
}

# verify before we return that the file has changed
$dest_checksum = Get-FileChecksum ($dest)
If ( $src_checksum.Equals($dest_checksum))
{
    $result.changed = $TRUE
}
Else
{
    Fail-Json (New-Object psobject) "src checksum $src_checksum did not match dest_checksum $dest_checksum  Failed to place file $original_basename in $dest"
}
# generate return values

$info = Get-Item $dest
$result.size = $info.Length

Exit-Json $result
