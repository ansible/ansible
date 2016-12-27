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
$ErrorActionPreference = "Stop"
$params = Parse-Args $args
$InputVariable = Get-Attr $params "pathvalue" $FALSE
$TargetSpace = Get-Attr $params "level" $FALSE
If (($InputVariable -or $TargetSpace) -eq $FALSE)
{
   
  Fail-Json (New-Object psobject) "missing required argument: pathvalue and level"
       
}
$result = New-Object psobject @{
    changed = $FALSE
}
$script = {
        Function Main{
                if($TargetSpace -eq "User" -or "Machine")
                {
                        $Value = [environment]::GetEnvironmentVariable("Path", "$TargetSpace")
                        if($Value -eq $null)
                        {
                                addnullpath
                        }
                        else
                        {
                                addpath
                        }
                }
        }

        # Function to Add/Append variable to path if System/User Path is defined
        Function addpath
        {
                $create_file = New-Item -Path $env:temp\path.txt -ItemType file
                $path = $Value -split ';' | Tee-Object -FilePath $create_file
                $content = Get-Content $create_file
                $myArray = New-Object System.Collections.ArrayList
                foreach ($line in $content)
                {
                        [void]$myArray.add($line)
                }
                $expand = [System.Environment]::ExpandEnvironmentVariables($InputVariable)
                if($myArray -eq $expand)
                {
                        #Write-Host Already ENV available in Path
                        $result.changed = $FALSE
                }
                else
                {
                        #write-host Path not available in the ENV Path so Script adding it in Path variable
                        [Environment]::SetEnvironmentVariable("Path", "$expand;" + $Value, [EnvironmentVariableTarget]::$TargetSpace)
	                $result.changed = $TRUE
                }
                Remove-Item -Path $create_file -Force
        }

        # Function to Add variable to path if System/User Path is not defined
        Function addnullpath
        {
                #write-host Variable not available in the ENV Path so Script adding it in Path variable
                $expand = [System.Environment]::ExpandEnvironmentVariables($InputVariable)
                [Environment]::SetEnvironmentVariable("Path", "$expand;", [EnvironmentVariableTarget]::$TargetSpace)
                $result.changed = $TRUE
        }

        # Call main in script block
        Main
}
Invoke-Command -Scriptblock $script
Exit-Json $result
