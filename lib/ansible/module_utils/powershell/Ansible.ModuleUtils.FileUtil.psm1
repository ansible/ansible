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
        [Parameter(Mandatory = $true)][string]$Path
    )

    # First check what the provider is based on the drive or PSPath provided.
    $provider = $drive = $null
    try {
        $null = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path, [ref]$provider, [ref]$drive)
    }
    catch [System.Management.Automation.DriveNotFoundException] {
        # If the drive doesn't exist, the path cannot exist in any context to PowerShell.
        return $false
    }

    # A UNC path is always seen as the current provider location so check if it
    # starts with \\ and treat it as a FileSystem path.
    if ($provider.Name -eq "FileSystem" -or $Path.StartsWith("\\")) {
        try {
            $file_attributes = [System.IO.File]::GetAttributes($Path)
        }
        catch [System.IO.FileNotFoundException], [System.IO.DirectoryNotFoundException] {
            return $false
        }

        return [int]$file_attributes -ne -1
    }
    else {
        # Otherwise just fallback to Test-Path for the other providers.
        return Test-Path -Path $Path
    }
}

Function Get-AnsibleItem {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory = $true)][string]$Path
    )
    # Replacement for Get-Item
    try {
        $file_attributes = [System.IO.File]::GetAttributes($Path)
    }
    catch {
        # if -ErrorAction SilentlyCotinue is set on the cmdlet and we failed to
        # get the attributes, just return $null, otherwise throw the error
        if ($ErrorActionPreference -ne "SilentlyContinue") {
            throw $_
        }
        return $null
    }
    if ([Int32]$file_attributes -eq -1) {
        throw New-Object -TypeName System.Management.Automation.ItemNotFoundException -ArgumentList "Cannot find path '$Path' because it does not exist."
    }
    elseif ($file_attributes.HasFlag([System.IO.FileAttributes]::Directory)) {
        return New-Object -TypeName System.IO.DirectoryInfo -ArgumentList $Path
    }
    else {
        return New-Object -TypeName System.IO.FileInfo -ArgumentList $Path
    }
}

Export-ModuleMember -Function Test-AnsiblePath, Get-AnsibleItem
