# Copyright (c) 2017 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

<#
Test-Path/Get-Item cannot find/return info on files that are locked like
C:\pagefile.sys. These 2 functions are designed to work with these files and
provide similar functionality with the normal cmdlets with as minimal overhead
as possible. They work by using Get-ChildItem with a filter and return the
result from that.
#>

Function Test-AnsiblePath {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory=$true)][string]$Path
    )
    # Replacement for Test-Path
    try {
        $file_attributes = [System.IO.File]::GetAttributes($Path)
    } catch [System.IO.FileNotFoundException], [System.IO.DirectoryNotFoundException] {
        return $false
    } catch [NotSupportedException] {
        # When testing a path like Cert:\LocalMachine\My, System.IO.File will
        # not work, we just revert back to using Test-Path for this
        return Test-Path -Path $Path
    }

    if ([Int32]$file_attributes -eq -1) {
        return $false
    } else {
        return $true
    }
}

Function Get-AnsibleItem {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory=$true)][string]$Path
    )
    # Replacement for Get-Item
    try {
        $file_attributes = [System.IO.File]::GetAttributes($Path)
    } catch {
        # if -ErrorAction SilentlyCotinue is set on the cmdlet and we failed to
        # get the attributes, just return $null, otherwise throw the error
        if ($ErrorActionPreference -ne "SilentlyContinue") {
            throw $_
        }
        return $null
    }
    if ([Int32]$file_attributes -eq -1) {
        throw New-Object -TypeName System.Management.Automation.ItemNotFoundException -ArgumentList "Cannot find path '$Path' because it does not exist."
    } elseif ($file_attributes.HasFlag([System.IO.FileAttributes]::Directory)) {
        return New-Object -TypeName System.IO.DirectoryInfo -ArgumentList $Path
    } else {
        return New-Object -TypeName System.IO.FileInfo -ArgumentList $Path
    }
}

Export-ModuleMember -Function Test-AnsiblePath, Get-AnsibleItem
