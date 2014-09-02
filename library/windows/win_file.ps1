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
$result = New-Object PSObject;
$force=$false;
#Set-Attr $result "changed" $true;

If (-not $params.name.GetType)
{
    Fail-Json $result "missing required arguments: name (file or directory)"
}

If (-not $params.type.GetType)
{
   Fail-Json $result "missgin required arguments: type [file] or [directory]"
}


If ($params.cwd) {
    $location = $params.cwd + "/"
    Set-Location -Path $location
    $setlocation = Get-Location
    If ( $setlocation.ToString.ToLower() -ne $location.ToString.ToLower()) {
  	Fail-Json $result "Could not change working dir to '$location'"
	}
}

$type = $params.type.ToString().ToLower()
$name = $params.name.ToString().ToLower()
$obj =  Get-Item $name -ErrorAction SilentlyContinue


If ( $obj -and ($params.override -eq $false))
{
 
 Fail-Json $result "Item '$name' already exist - use override=true to force"		
}


If ($params.override -eq $true){
    If (($obj.PSIsContainer -eq $true) -and ($type -eq "file"))
    {
	Fail-Json $result "A directory with the same name already exist - cannot procede"
    }
    
     If (($obj.PSIsContainer -eq $false) -and ($type -eq "directory"))
    {
        Fail-Json $result "A file with the same name already exist - cannot procede"
    }

    $force = $true
}

$op_status = New-Item $name -type $type -force:$force

If (-not $op_status) {
	Fail-Json $result "Could not create '$name' of type '$type' '$op_status'"
}

Set-Attr $result "changed" $true;
Exit-Json $result;
