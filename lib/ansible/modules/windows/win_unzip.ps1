#!powershell

# Copyright: (c) 2015, Phil Schwartz <schwartzmx@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

# TODO: This module is not idempotent (it will always unzip and report change)

$ErrorActionPreference = "Stop"

$pcx_extensions = @('.bz2', '.gz', '.msu', '.tar', '.zip')

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$src = Get-AnsibleParam -obj $params -name "src" -type "path" -failifempty $true
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path" -failifempty $true
$creates = Get-AnsibleParam -obj $params -name "creates" -type "path"
$recurse = Get-AnsibleParam -obj $params -name "recurse" -type "bool" -default $false
$delete_archive = Get-AnsibleParam -obj $params -name "delete_archive" -type "bool" -default $false -aliases 'rm'

# Fixes a fail error message (when the task actually succeeds) for a
# "Convert-ToJson: The converted JSON string is in bad format"
# This happens when JSON is parsing a string that ends with a "\",
# which is possible when specifying a directory to download to.
# This catches that possible error, before assigning the JSON $result
$result = @{
    changed = $false
    dest = $dest -replace '\$',''
    removed = $false
    src = $src -replace '\$',''
}

Function Extract-Zip($src, $dest) {
    $archive = [System.IO.Compression.ZipFile]::Open($src, [System.IO.Compression.ZipArchiveMode]::Read, [System.Text.Encoding]::UTF8)
    foreach ($entry in $archive.Entries) {
        $archive_name = $entry.FullName

        $entry_target_path = [System.IO.Path]::Combine($dest, $archive_name)
        $entry_dir = [System.IO.Path]::GetDirectoryName($entry_target_path)

        # Normalize paths for further evaluation
        $full_target_path = [System.IO.Path]::GetFullPath($entry_target_path)
        $full_dest_path = [System.IO.Path]::GetFullPath($dest + [System.IO.Path]::DirectorySeparatorChar)

        # Ensure file in the archive does not escape the extraction path
        if (-not $full_target_path.StartsWith($full_dest_path)) {
            Fail-Json -obj $result -message "Error unzipping '$src' to '$dest'! Filename contains relative paths which would extract outside the destination: $entry_target_path"
        }

        if (-not (Test-Path -LiteralPath $entry_dir)) {
            New-Item -Path $entry_dir -ItemType Directory -WhatIf:$check_mode | Out-Null
            $result.changed = $true
        }

        if ((-not ($entry_target_path.EndsWith("\") -or $entry_target_path.EndsWith("/"))) -and (-not $check_mode)) {
            [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $entry_target_path, $true)
        }
        $result.changed = $true
    }
    $archive.Dispose()
}

Function Extract-ZipLegacy($src, $dest) {
    # [System.IO.Compression.ZipFile] was only added in .net 4.5, this is used
    # when .net is older than that.
    $shell = New-Object -ComObject Shell.Application
    $zip = $shell.NameSpace([IO.Path]::GetFullPath($src))
    $dest_path = $shell.NameSpace([IO.Path]::GetFullPath($dest))

    $shell = New-Object -ComObject Shell.Application

    if (-not $check_mode) {
        # https://msdn.microsoft.com/en-us/library/windows/desktop/bb787866.aspx
        # From Folder.CopyHere documentation, 1044 means:
        #  - 1024: do not display a user interface if an error occurs
        #  -   16: respond with "yes to all" for any dialog box that is displayed
        #  -    4: do not display a progress dialog box
        $dest_path.CopyHere($zip.Items(), 1044)
    }
    $result.changed = $true
}

If ($creates -and (Test-Path -LiteralPath $creates)) {
    $result.skipped = $true
    $result.msg = "The file or directory '$creates' already exists."
    Exit-Json -obj $result
}

If (-Not (Test-Path -LiteralPath $src)) {
    Fail-Json -obj $result -message "File '$src' does not exist."
}

$ext = [System.IO.Path]::GetExtension($src)

If (-Not (Test-Path -LiteralPath $dest -PathType Container)){
    Try{
        New-Item -ItemType "directory" -path $dest -WhatIf:$check_mode | out-null
    } Catch {
        Fail-Json -obj $result -message "Error creating '$dest' directory! Msg: $($_.Exception.Message)"
    }
}

If ($ext -eq ".zip" -And $recurse -eq $false) {
    # TODO: PS v5 supports zip extraction, use that if available
    $use_legacy = $false
    try {
        # determines if .net 4.5 is available, if this fails we need to fall
        # back to the legacy COM Shell.Application to extract the zip
        Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null
        Add-Type -AssemblyName System.IO.Compression | Out-Null
    } catch {
        $use_legacy = $true
    }

    if ($use_legacy) {
        try {
            Extract-ZipLegacy -src $src -dest $dest
        } catch {
            Fail-Json -obj $result -message "Error unzipping '$src' to '$dest'!. Method: COM Shell.Application, Exception: $($_.Exception.Message)"
        }
    } else {
        try {
            Extract-Zip -src $src -dest $dest
        } catch {
            Fail-Json -obj $result -message "Error unzipping '$src' to '$dest'!. Method: System.IO.Compression.ZipFile, Exception: $($_.Exception.Message)"
        }
    }
} Else {
    # Check if PSCX is installed
    $list = Get-Module -ListAvailable

    If (-Not ($list -match "PSCX")) {
        Fail-Json -obj $result -message "PowerShellCommunityExtensions PowerShell Module (PSCX) is required for non-'.zip' compressed archive types."
    } Else {
        $result.pscx_status = "present"
    }

    Try {
        Import-Module PSCX
    }
    Catch {
        Fail-Json $result "Error importing module PSCX"
    }

    Try {
        Expand-Archive -Path $src -OutputPath $dest -Force -WhatIf:$check_mode
    } Catch {
        Fail-Json -obj $result -message "Error expanding '$src' to '$dest'! Msg: $($_.Exception.Message)"
    }

    If ($recurse) {
        Get-ChildItem -LiteralPath $dest -recurse | Where-Object {$pcx_extensions -contains $_.extension} | ForEach-Object {
            Try {
                Expand-Archive $_.FullName -OutputPath $dest -Force -WhatIf:$check_mode
            } Catch {
                Fail-Json -obj $result -message "Error recursively expanding '$src' to '$dest'! Msg: $($_.Exception.Message)"
            }
            If ($delete_archive) {
                Remove-Item -LiteralPath $_.FullName -Force -WhatIf:$check_mode
                $result.removed = $true
            }
        }
    }

    $result.changed = $true
}

If ($delete_archive){
    try {
        Remove-Item -LiteralPath $src -Recurse -Force -WhatIf:$check_mode
    } catch {
        Fail-Json -obj $result -message "failed to delete archive at '$src': $($_.Exception.Message)"
    }
    $result.removed = $true
}
Exit-Json $result
