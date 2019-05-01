# Copyright (c) 2017 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

#AnsibleRequires -CSharpUtil Ansible.IO

Function Test-AnsiblePath {
    <#
    .SYNOPSIS
    Checks if the item at Path exists or not.

    .PARAMETER Path
    The path to the item to check for its existence.

    .NOTES
    This is mean to replace Test-Path as it works with special files like pagefile.sys and files exceeding MAX_PATH.
    #>
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory=$true)][string]$Path
    )

    # When testing a path like Cert:\LocalMachine\My, our C# functions will
    # not work, we just revert back to using Test-Path for this
    $ps_providers = (Get-PSDrive).Name | Where-Object {
        $_ -notmatch "^[A-Za-z]$" -and $Path.StartsWith("$($_):", $true, [System.Globalization.CultureInfo]::InvariantCulture)
    }
    if ($null -ne $ps_providers) {
        return Test-Path -Path $Path
    }

    try {
        [Ansible.IO.FileSystem]::GetFileAttributeData($Path) > $null
        return $true
    } catch [System.IO.FileNotFoundException], [System.IO.DirectoryNotFoundException] {
        return $false
    }
}

Function Get-AnsibleItem {
    <#
    .SYNOPSIS
    Replacement for Get-Item to work with special files that are locked like pagefile.sys.

    .PARAMETER Path
    The path to the file to get the info for.
    #>
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory=$true)][string]$Path
    )

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
