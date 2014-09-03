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
$pre_state="absent"

$result = New-Object psobject @{
    changed = $false
    name = ""
    msg = ""
    pre_state = ""
};

If (-not $params.name.GetType)
{
    Fail-Json $result "missing required arguments: name (file or directory)"
}


If ($params.state) {
    $state = $params.state.ToString().ToLower()
    If (($state -ne 'file') -and ($state -ne 'absent') -and ($state -ne 'directory' )) {
        Fail-Json $result "state is '$state'; must be 'file' or 'directory' or 'absent'"
    }
}
Elseif (!$params.state) {
    $state = "file"
}


$type = $params.state.ToString().ToLower()
$name = $params.name.ToString().ToLower()
$obj =  Get-Item $name -ErrorAction SilentlyContinue
$force = $false;

$result.name = $name
$result.msg = "Generic Error"

If ($params.override -eq $true)
{
	$force=$true
}

If ($obj){
	If ($obj.PSIsContainer -eq $true)
	{
		$pre_state="directory"
	}
	Elseif ($obj.PSIsContainer -eq $false)
	{
		$pre_state="file"
	}	
}

$result.pre_state = $pre_state

If ( ($type -eq $pre_state) -and (-not $force) )
{
	 $result.msg="Nothing to do"
	 Exit-Json $result
}

If ( $type -eq "absent" )
{
	Remove-Item $name -Force -Recurse
	$result.msg = "Item Removed"
	$result.changed = $true

}
ElseIf ( ($type -eq "file") -and ($pre_state -ne "directory" ))
{
	$op_status = New-Item $name -type $type -force:$force
	If (-not $op_status) {
		Fail-Json $result "Could not create item as requested"
			}
	$result.msg = "Item Created"
        $result.changed = $true

}
Elseif ( ($type -eq "directory") -and ($pre_state -ne "file"))
{ 
	$op_status = New-Item $name -type $type
	 If (-not $op_status) {
                Fail-Json $result "Could not create item as requested"
	}
	$result.msg = "Item Created"
        $result.changed = $true
}
Else
{
	$changed =$false;
	Fail-Json $result "Item already exist but type mismatch"
}


Exit-Json $result;
