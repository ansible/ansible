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
    $registryKeyName = $params.name
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

If ($params.value)
{
    $registryKeyValue = $params.value
}
ElseIf ($state -eq "present")
{
    Fail-Json $result "missing required argument: value"
}

If ($params.valuetype)
{
    $registryValueType = $params.valuetype.ToString().ToLower()
    $validRegistryValueTypes = "binary", "dword", "expandstring", "multistring", "string", "qword"
    If ($validRegistryValueTypes -notcontains $registryValueType)
    {
        Fail-Json $result "valuetype is $registryValueType; must be binary, dword, expandstring, multistring, string, or qword"
    }
}
Else
{
    $registryValueType = "string"
}

If ($params.path)
{
    $registryKeyPath = $params.path
}
Else
{
    Fail-Json $result "missing required argument: path"
}

Function Test-RegistryValue {
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
    if (Test-Path $registryKeyPath) {
        if (Test-RegistryValue -Path $registryKeyPath -Value $registryKeyName)
        {
            # Changes Type and Value
            If ((Get-Item $registryKeyPath).GetValueKind($registryKeyName) -ne $registryValueType)
            {
                Try
                {
                    Remove-ItemProperty -Path $registryKeyPath -Name $registryKeyName
                    New-ItemProperty -Path $registryKeyPath -Name $registryKeyName -Value $registryKeyValue -PropertyType $registryValueType
                    $result.changed = $true
                }
                Catch
                {
                    Fail-Json $result $_.Exception.Message
                }
            }
            # Only Changes Value
            ElseIf ((Get-ItemProperty -Path $registryKeyPath | Select-Object -ExpandProperty $registryKeyName) -ne $registryKeyValue) 
            {
                Try {
                    Set-ItemProperty -Path $registryKeyPath -Name $registryKeyName -Value $registryKeyValue
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
                New-ItemProperty -Path $registryKeyPath -Name $registryKeyName -Value $registryKeyValue -PropertyType $registryValueType
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
            New-Item $registryKeyPath -Force | New-ItemProperty -Name $registryKeyName -Value $registryKeyValue -Force -PropertyType $registryValueType
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
    if (Test-Path $registryKeyPath)
    {
        if (Test-RegistryValue -Path $registryKeyPath -Value $registryKeyName) {
            Try
            {
                Remove-ItemProperty -Path $registryKeyPath -Name $registryKeyName
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
