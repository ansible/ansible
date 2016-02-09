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

New-PSDrive -PSProvider registry -Root HKEY_CLASSES_ROOT -Name HKCR -ErrorAction SilentlyContinue
New-PSDrive -PSProvider registry -Root HKEY_USERS -Name HKU -ErrorAction SilentlyContinue
New-PSDrive -PSProvider registry -Root HKEY_CURRENT_CONFIG -Name HCCC -ErrorAction SilentlyContinue

$params = Parse-Args $args;
$result = New-Object PSObject;
Set-Attr $result "changed" $false;

$registryKey = Get-Attr -obj $params -name "key" -failifempty $true
$registryValue = Get-Attr -obj $params -name "value" -default $null
$state = Get-Attr -obj $params -name "state" -validateSet "present","absent" -default "present"
$registryData = Get-Attr -obj $params -name "data" -default $null
$registryDataType = Get-Attr -obj $params -name "datatype" -validateSet "binary","dword","expandstring","multistring","string","qword" -default "string"

If ($state -eq "present" -and $registryData -eq $null -and $registryValue -ne $null)
{
    Fail-Json $result "missing required argument: data"
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
    if ((Test-Path $registryKey) -and $registryValue -ne $null)
    {
        if (Test-RegistryValueData -Path $registryKey -Value $registryValue)
        {
            if ($registryValue.ToLower() -eq "(default)") {
                # Special case handling for the key's default property. Because .GetValueKind() doesn't work for the (default) key property
                $oldRegistryDataType = "String"
            }
            else {
                $oldRegistryDataType = (Get-Item $registryKey).GetValueKind($registryValue)
            }

            # Changes Data and DataType
            if ($registryDataType -ne $oldRegistryDataType)
            {
                Try
                {
                    Remove-ItemProperty -Path $registryKey -Name $registryValue
                    New-ItemProperty -Path $registryKey -Name $registryValue -Value $registryData -PropertyType $registryDataType
                    $result.changed = $true
                }
                Catch
                {
                    Fail-Json $result $_.Exception.Message
                }
            }
            # Changes Only Data
            elseif ((Get-ItemProperty -Path $registryKey | Select-Object -ExpandProperty $registryValue) -ne $registryData)
            {
                Try {
                    Set-ItemProperty -Path $registryKey -Name $registryValue -Value $registryData
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
                New-ItemProperty -Path $registryKey -Name $registryValue -Value $registryData -PropertyType $registryDataType
                $result.changed = $true
            }
            Catch
            {
                Fail-Json $result $_.Exception.Message
            }
        }
    }
    elseif(-not (Test-Path $registryKey))
    {
        Try
        {
            $newRegistryKey = New-Item $registryKey -Force
            $result.changed = $true

            if($registryValue -ne $null) {
                $newRegistryKey | New-ItemProperty -Name $registryValue -Value $registryData -Force -PropertyType $registryDataType
                $result.changed = $true
            }
        }
        Catch
        {
            Fail-Json $result $_.Exception.Message
        }
    }
}
else
{
    if (Test-Path $registryKey)
    {
        if ($registryValue -eq $null) {
            Try
            {
                Remove-Item -Path $registryKey -Recurse
                $result.changed = $true
            }
            Catch
            {
                Fail-Json $result $_.Exception.Message
            }
        }
        elseif (Test-RegistryValueData -Path $registryKey -Value $registryValue) {
            Try
            {
                Remove-ItemProperty -Path $registryKey -Name $registryValue
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
