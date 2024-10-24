# Copyright (c): 2018, Dag Wieers (@dagwieers) <dag@wieers.com>
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

Function Backup-File {
    <#
    .SYNOPSIS
    Helper function to make a backup of a file.
    .EXAMPLE
    Backup-File -path $path -WhatIf:$check_mode
#>
    [CmdletBinding(SupportsShouldProcess = $true)]

    Param (
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [string] $path
    )

    Process {
        $backup_path = $null
        if (Test-Path -LiteralPath $path -PathType Leaf) {

            $dirname = Split-Path -Parent $path -Resolve

            # set variables for templating purposes
            $basename = Split-Path -Path $path -Leaf -Resolve
            $stripname = Split-Path -Path $path -LeafBase -Resolve
            $extension = Split-Path -Path $path -Extension -Resolve
            $timestamp = [DateTime]::Now.ToString("yyyyMMdd-HHmmss")

            # TODO: make childpath configurable via template stirng from config
            $backup_path = Join-Path -Path $dirname -ChildPath "$basename.$pid.$timestamp.bak"
            Try {
                Copy-Item -LiteralPath $path -Destination $backup_path
            }
            Catch {
                throw "Failed to create backup file '$backup_path' from '$path'. ($($_.Exception.Message))"
            }
        }
        return $backup_path
    }
}

# This line must stay at the bottom to ensure all defined module parts are exported
Export-ModuleMember -Function Backup-File
