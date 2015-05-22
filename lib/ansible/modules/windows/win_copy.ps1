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

$params = Parse-Args $args;

$src= Get-Attr $params "src" $FALSE;
If ($src -eq $FALSE)
{
    Fail-Json (New-Object psobject) "missing required argument: src";
}

$dest= Get-Attr $params "dest" $FALSE;
If ($dest -eq $FALSE)
{
    Fail-Json (New-Object psobject) "missing required argument: dest";
}

# seems to be supplied by the calling environment, but
# probably shouldn't be a test for it existing in the params.
# TODO investigate.
$original_basename = Get-Attr $params "original_basename" $FALSE;
If ($original_basename -eq $FALSE)
{
    Fail-Json (New-Object psobject) "missing required argument: original_basename ";
}

$result = New-Object psobject @{
    changed = $FALSE
};

# if $dest is a dir, append $original_basename so the file gets copied with its intended name.
if (Test-Path $dest -PathType Container)
{
    $dest = Join-Path $dest $original_basename;
}

If (Test-Path $dest)
{
    $dest_checksum = Get-FileChecksum ($dest);
    $src_checksum = Get-FileChecksum ($src);

    If (! $src_checksum.CompareTo($dest_checksum))
    {
        # New-Item -Force creates subdirs for recursive copies
        New-Item -Force $dest -Type file;
        Copy-Item -Path $src -Destination $dest -Force;
    }
    $dest_checksum = Get-FileChecksum ($dest);
    If ( $src_checksum.CompareTo($dest_checksum))
    {
        $result.changed = $TRUE;
    }
    Else
    {
        Fail-Json (New-Object psobject) "Failed to place file";
    }
}
Else
{
    New-Item -Force $dest -Type file;
    Copy-Item -Path $src -Destination $dest;
    $result.changed = $TRUE;
}

$dest_checksum = Get-FileChecksum($dest);
$result.checksum = $dest_checksum;

Exit-Json $result;
