# Copyright (c) 2017 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

<#
Test-Path/Get-Item cannot find/return info on files that are locked like
C:\pagefile.sys. These 2 functions are designed to work with these files and
provide similar functionality with the normal cmdlets with as minimal overhead
as possible. They work by using Get-ChildItem with a filter and return the
result from that.
#>

Function Test-FilePath($path) {
    # Basic replacement for Test-Path that tests if the file/folder exists at the path
    $directory = Split-Path -Path $path -Parent
    $filename = Split-Path -Path $path -Leaf

    $file = Get-ChildItem -Path $directory -Filter $filename -Force -ErrorAction SilentlyContinue
    if ($file -ne $null) {
        if ($file -is [Array] -and $file.Count -gt 1) {
            throw "found multiple files at path '$path', make sure no wildcards are set in the path"
        }
        return $true
    } else {
        return $false
    }
}

Function Get-FileItem($path) {
    # Replacement for Get-Item
    $directory = Split-Path -Path $path -Parent
    $filename = Split-Path -Path $path -Leaf

    $file = Get-ChildItem -Path $directory -Filter $filename -Force -ErrorAction SilentlyContinue
    if ($file -is [Array] -and $file.Count -gt 1) {
        throw "found multiple files at path '$path', make sure no wildcards are set in the path"
    }

    return $file
}

Export-ModuleMember -Function Test-FilePath, Get-FileItem
