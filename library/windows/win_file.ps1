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


$type = $state.ToString().ToLower()
$name = $params.name.ToString().ToLower()
$obj =  Get-Item $name -ErrorAction SilentlyContinue
$force = $false;


If ($params.force -eq $true)
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

$result.name = $name
$result.msg = "Generic Error"
$result.pre_state = $pre_state

If ( ($type -eq $pre_state) -and (-not $force) )
{
	 $result.msg="Nothing to do"
	 Exit-Json $result
}

If ( $type -eq "absent" )
{	try{
	$op_status= Remove-Item $name -Force -Recurse -ErrorAction Stop
	$result.msg = "Item Removed"
	$result.changed = $true
	}
	catch {
        	Fail-Json $result $_.Exception.Message
    	}

}
ElseIf ( ($type -eq "file"))
{
      try{
	If (($pre_state -eq "directory"))
	{
	   If (-not $force)
           {
                        Fail-Json $result "state mismatch - use force=true"
           }

	  $op_status=Remove-Item $name -Force -Recurse -ErrorAction Stop
	  
	}
	$dirsplit = split-path $name
	If ($dirsplit)
	{
	   New-Item -Path $dirsplit -type directory -ErrorAction  SilentlyContinue
	}
	$op_status = New-Item -Path $name -type $type -force:$force -ErrorAction Stop
			}
	$result.msg = "Item Created"
        $result.changed = $true
	}
	 catch {
        Fail-Json $result $_.Exception.Message
    }


}
Elseif ( ($type -eq "directory"))
{
	try{ 
	If (($pre_state -eq "file"))
	{	
		If (-not $force)
		{
			Fail-Json $result "state mismatch - use force=true"
		}
		$op_status=Remove-Item $name -Force -ErrorAction Stop

	}
	$op_status = New-Item -Path $name -type $type -ErrorAction Stop
	$result.msg = "Item Created"
        $result.changed = $true
	}
	 catch {
	        Fail-Json $result $_.Exception.Message
    	}

}
Else
{
	$changed =$false;
	Fail-Json $result "Item already exist but type mismatch"
}


Exit-Json $result;
