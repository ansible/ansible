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
Set-Attr $result "data_changed" $false;
Set-Attr $result "data_type_changed" $false;

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

# Returns rue if registry data matches.
# Handles binary and string registry data
Function Compare-RegistryData {
    Param (
        [parameter(Mandatory=$true)]
        [AllowEmptyString()]$ReferenceData,
        [parameter(Mandatory=$true)]
        [AllowEmptyString()]$DifferenceData
        )
        $refType = $ReferenceData.GetType().Name

        if ($refType -eq "String" ) {
            if ($ReferenceData -eq $DifferenceData) {
                return $true
            } else {
                return $false
            }
        } elseif ($refType -eq "Object[]") {
            if (@(Compare-Object $ReferenceData $DifferenceData -SyncWindow 0).Length -eq 0) {
                return $true
            } else {
                return $false
            }
        }
}

# Simplified version of Convert-HexStringToByteArray from
# https://cyber-defense.sans.org/blog/2010/02/11/powershell-byte-array-hex-convert
# Expects a hex in the format you get when you run reg.exe export,
# and converts to a byte array so powershell can modify binary registry entries
function Convert-RegExportHexStringToByteArray
{
    Param (
     [parameter(Mandatory=$true)] [String] $String
    )

# remove 'hex:' from the front of the string if present
$String = $String.ToLower() -replace '^hex\:', ''

#remove whitespace and any other non-hex crud.
$String = $String.ToLower() -replace '[^a-f0-9\\,x\-\:]',''

# turn commas into colons
$String = $String -replace ',',':'

#Maybe there's nothing left over to convert...
if ($String.Length -eq 0) { ,@() ; return }

#Split string with or without colon delimiters.
if ($String.Length -eq 1)
{ ,@([System.Convert]::ToByte($String,16)) }
elseif (($String.Length % 2 -eq 0) -and ($String.IndexOf(":") -eq -1))
{ ,@($String -split '([a-f0-9]{2})' | foreach-object { if ($_) {[System.Convert]::ToByte($_,16)}}) }
elseif ($String.IndexOf(":") -ne -1)
{ ,@($String -split ':+' | foreach-object {[System.Convert]::ToByte($_,16)}) }
else
{ ,@() }

}

if($registryDataType -eq "binary" -and $registryData -ne $null -and $registryData.GetType().Name -eq 'String') {
      $registryData = Convert-RegExportHexStringToByteArray($registryData)
}

if($state -eq "present") {
    if ((Test-Path $registryKey) -and $registryValue -ne $null)
    {
        if (Test-RegistryValueData -Path $registryKey -Value $registryValue)
        {
            # handle binary data
            $currentRegistryData =(Get-ItemProperty -Path $registryKey | Select-Object -ExpandProperty $registryValue) 

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
                    $result.data_changed = $true
                    $result.data_type_changed = $true
                }
                Catch
                {
                    Fail-Json $result $_.Exception.Message
                }
            }
            # Changes Only Data
            elseif (-Not (Compare-RegistryData -ReferenceData $currentRegistryData -DifferenceData $registryData))
            {
                Try {
                    Set-ItemProperty -Path $registryKey -Name $registryValue -Value $registryData
                    $result.changed = $true
                    $result.data_changed = $true
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
