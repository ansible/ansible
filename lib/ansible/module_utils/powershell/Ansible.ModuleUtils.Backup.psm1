# Copyright (c): 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

Function Backup-File($path, $obj=@{}, $check_mode=$false) {
<#
    .SYNOPSIS
    Helper function to make a backup of a file.
    .EXAMPLE
    Backup-File -path $path -obj $result
#>
    $backup_path = "$path.$pid." + [DateTime]::Now.ToString("yyyyMMdd-HHmmss") + ".bak";
    Try {
        Copy-Item -Path $path -Destination $backup_path -WhatIf:$check_mode
    } Catch {
        Fail-Json -obj $obj -message "Failed to create backup file '$backup_path' from '$path'. ($($_.Exception.Message))"
    }
    return $backup_path
}

# This line must stay at the bottom to ensure all defined module parts are exported
Export-ModuleMember -Alias * -Function * -Cmdlet *
