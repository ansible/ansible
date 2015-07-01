#!powershell
# This file is part of Ansible
#
# (c) 2015, Adam Keech <akeech@chathamfinancial.com>, Josh Ludwig <jludwig@chathamfinancial.com>
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

$ErrorActionPreference = "Stop"

# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;
$result = New-Object PSObject;
Set-Attr $result "changed" $false;

If ($params.name)
{
    $registryValueName = $params.name
}
Else
{
    Fail-Json $result "missing required argument: name"
}

If ($params.state)
{
    $state = $params.state.ToString().ToLower()
    If (($state -ne "present") -and ($state -ne "absent"))
    {
        Fail-Json $result "state is $state; must be present or absent"
    }
}
Else
{
    $state = "present"
}

If ($params.data)
{
    $registryValueData = $params.data
}
ElseIf ($state -eq "present")
{
    Fail-Json $result "missing required argument: data"
}

If ($params.type)
{
    $registryDataType = $params.type.ToString().ToLower()
    $validRegistryDataTypes = "binary", "dword", "expandstring", "multistring", "string", "qword"
    If ($validRegistryDataTypes -notcontains $registryDataType)
    {
        Fail-Json $result "type is $registryDataType; must be binary, dword, expandstring, multistring, string, or qword"
    }
}
Else
{
    $registryDataType = "string"
}

If ($params.path)
{
    $registryValuePath = $params.path
}
Else
{
    Fail-Json $result "missing required argument: path"
}

Function Test-RegistryValueData {
    Param (
        [parameter(Mandatory=$true)]
        [ValidateNotNullOrEmpty()]$Path,
        [parameter(Mandatory=$true)]
        [ValidateNotNullOrEmpty()]$Value
    )
    Try {
        Get-ItemProperty -Path $Path -Name $Value
        Return $true
    }
    Catch {
        Return $false
    }
}

if($state -eq "present") {
    if (Test-Path $registryValuePath) {
        if (Test-RegistryValueData -Path $registryValuePath -Value $registryValueName)
        {
            # Changes Type and Value
            If ((Get-Item $registryValuePath).GetValueKind($registryValueName) -ne $registryDataType)
            {
                Try
                {
                    Remove-ItemProperty -Path $registryValuePath -Name $registryValueName
                    New-ItemProperty -Path $registryValuePath -Name $registryValueName -Value $registryValueData -PropertyType $registryDataType
                    $result.changed = $true
                }
                Catch
                {
                    Fail-Json $result $_.Exception.Message
                }
            }
            # Only Changes Value
            ElseIf ((Get-ItemProperty -Path $registryValuePath | Select-Object -ExpandProperty $registryValueName) -ne $registryValueData) 
            {
                Try {
                    Set-ItemProperty -Path $registryValuePath -Name $registryValueName -Value $registryValueData
                    $result.changed = $true
                }
                Catch
                {
                    Fail-Json $result $_.Exception.Message
                }
            }
        }
        else
        {
            Try
            {
                New-ItemProperty -Path $registryValuePath -Name $registryValueName -Value $registryValueData -PropertyType $registryDataType
                $result.changed = $true
            }
            Catch
            {
                Fail-Json $result $_.Exception.Message
            }
        }
    }
    else
    {
        Try 
        {
            New-Item $registryValuePath -Force | New-ItemProperty -Name $registryValueName -Value $registryValueData -Force -PropertyType $registryDataType
            $result.changed = $true
        }
        Catch
        {
            Fail-Json $result $_.Exception.Message
        }
    }
}
else
{
    if (Test-Path $registryValuePath)
    {
        if (Test-RegistryValueData -Path $registryValuePath -Value $registryValueName) {
            Try
            {
                Remove-ItemProperty -Path $registryValuePath -Name $registryValueName
                $result.changed = $true
            }
            Catch
            {
                Fail-Json $result $_.Exception.Message
            }
        }
    }
}

Exit-Json $result

