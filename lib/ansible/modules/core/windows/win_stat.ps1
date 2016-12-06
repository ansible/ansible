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

$params = Parse-Args $args $true;

function Date_To_Timestamp($start_date, $end_date)
{
    If($start_date -and $end_date)
    {
        Write-Output (New-TimeSpan -Start $start_date -End $end_date).TotalSeconds
    }
}

$path = Get-Attr $params "path" $FALSE;
If ($path -eq $FALSE)
{
    Fail-Json (New-Object psobject) "missing required argument: path";
}

$get_md5 = Get-Attr $params "get_md5" $TRUE | ConvertTo-Bool;
# until we support real aliasing, get the default value from get_md5
$get_checksum = Get-Attr $params "get_checksum" $get_md5 | ConvertTo-Bool;

$result = New-Object psobject @{
    stat = New-Object psobject
    changed = $false
};

If (Test-Path $path)
{
    Set-Attr $result.stat "exists" $TRUE;

    $info = Get-Item $path;
    $iscontainer = Get-Attr $info "PSIsContainer" $null;
    $length = Get-Attr $info "Length" $null;
    $extension = Get-Attr $info "Extension" $null;
    $attributes = Get-Attr $info "Attributes" "";
    If ($info)
    {
        $accesscontrol = $info.GetAccessControl();
    }
    Else
    {
        $accesscontrol = $null;
    }
    $owner = Get-Attr $accesscontrol "Owner" $null;
    $creationtime = Get-Attr $info "CreationTime" $null;
    $lastaccesstime = Get-Attr $info "LastAccessTime" $null;
    $lastwritetime = Get-Attr $info "LastWriteTime" $null;


    $epoch_date = Get-Date -Date "01/01/1970"
    If ($iscontainer)
    {
        Set-Attr $result.stat "isdir" $TRUE;
    }
    Else
    {
        Set-Attr $result.stat "isdir" $FALSE;
        Set-Attr $result.stat "size" $length;
    }
    Set-Attr $result.stat "extension" $extension;
    Set-Attr $result.stat "attributes" $attributes.ToString();
    # Set-Attr $result.stat "owner" $getaccesscontrol.Owner;
    # Set-Attr $result.stat "owner" $info.GetAccessControl().Owner;
    Set-Attr $result.stat "owner" $owner;
    Set-Attr $result.stat "creationtime" (Date_To_Timestamp $epoch_date $creationtime);
    Set-Attr $result.stat "lastaccesstime" (Date_To_Timestamp $epoch_date $lastaccesstime);
    Set-Attr $result.stat "lastwritetime" (Date_To_Timestamp $epoch_date $lastwritetime);
}
Else
{
    Set-Attr $result.stat "exists" $FALSE;
}

# only check get_checksum- it either got its value from get_md5 or was set directly.
If (($get_checksum) -and $result.stat.exists -and -not $result.stat.isdir)
{
    $hash = Get-FileChecksum($path);
    Set-Attr $result.stat "md5" $hash;
    Set-Attr $result.stat "checksum" $hash;
}

Exit-Json $result;
