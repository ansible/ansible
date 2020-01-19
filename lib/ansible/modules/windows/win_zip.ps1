#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Version 5.0

Set-StrictMode -Version 2.0

$ErrorActionPreference = "Stop"
#TODO/Future Enhancements
#-------------------------
# - support recurse or just content for dirs
# - support multiple source files and dirs and globs
# - "force" option to overwrite existing zip file
# - Provide an 'update' parameter to add or remove files from the zip
# - Support other archive types - $pcx_extensions = @('.bz2', '.gz', '.msu', '.tar', '.zip')

# Notes
# -----
# The operations should be atomic - the zip shouldn't be created if anything fails

# Initialize it here as it's used for the failifempty
$result = @{
    changed = $false
    source_deleted = $false
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$src = Get-AnsibleParam -obj $params -name "src" -type "path" -failifempty $true -resultobj $result -aliases path
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path" -failifempty $true -resultobj $result -aliases zip_file
$delete_src = Get-AnsibleParam -obj $params -name "delete_src" -type "bool" -default $false -aliases rm
$creates = Get-AnsibleParam -obj $params -name "creates" -type "path"

# Fixes a fail error message (when the task actually succeeds) for a
# "Convert-ToJson: The converted JSON string is in bad format"
# This happens when JSON is parsing a string that ends with a "\",
# which is possible when specifying a directory to download to.
# This catches that possible error, before assigning the JSON $result
$result.dest = $dest -replace '\\$',''
$result.src = $src -replace '\\$',''

if ($creates) {
    $result.creates = $creates
}

function Remove-BrokenZip([string]$dest) {
    #Removes the broken zip
    Remove-Item -LiteralPath $dest -Force -ErrorAction SilentlyContinue
}

function Remove-Source([string]$src) {
    try {
        if (-not $check_mode) {
            if (Test-Path -LiteralPath $src) {
                # -recurse won't cause issues for files
                Remove-Item -LiteralPath $src -Recurse -Force -ErrorAction Stop
            }
        }
        #$result.changed = $true
        $result.source_deleted = $true
    }
    catch {
        Remove-BrokenZip $dest
        Fail-Json -obj $result -message "Error removing source '$src': $($_.Exception.Message)"
    }

}

function Find-LargeFiles([string]$src, [ref]$large_files, [int]$max_size=2097152000) {
    #$large_files = New-Object -Type System.Collections.ArrayList

    if (Test-Path -LiteralPath $src -PathType Container) {
        $items = Get-ChildItem -LiteralPath $src -Recurse
        foreach ($item in $items) {
            if (($item.GetType()).Name -eq "FileInfo") {
                if ($item.length -ge $max_size) {
                    ($large_files.Value).Add($item.FullName) | Out-Null
                }
            }
        }
    }
    else {
        $item = Get-Item -LiteralPath $src
        if ($item.Length -ge $max_size) {
            ($large_files.Value).Add($item.FullName) | Out-Null
        }
    }
}

function New-ZipFile {
	param(
	[Parameter(Mandatory=$True)]
	[string]$src,
	[Parameter(Mandatory=$True)]
	[string]$dest,
	[Parameter(Mandatory=$True)]
	[CompressionUtils]$utils_available
	)

    switch ($utils_available)
    {
        "PowerShell" {
            try {
                if (-not $check_mode) {
                    Compress-Archive -LiteralPath $src -DestinationPath $dest -CompressionLevel Optimal -ErrorAction Stop
                }
                #$result.changed = $true
            }
            catch {
                Remove-BrokenZip $dest
                Fail-Json -obj $result -message "Error creating zip file '$dest': $($_.Exception.Message)"
            }
        }
        "DotNet" {
            try {
                # add type here is only needed for force testing dotnet in the calling main code
                Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop| Out-Null
                Add-Type -AssemblyName System.IO.Compression -ErrorAction Stop | Out-Null

                if (Test-Path -LiteralPath $src -PathType Container)
                {
                    if (-not $check_mode) {
                        [System.IO.Compression.ZipFile]::CreateFromDirectory($src, $dest)
                    }
                    #$result.changed = $true
                }
                else {
                    if (-not $check_mode) {
                        $archive = [System.IO.Compression.ZipFile]::Open($dest, [System.IO.Compression.ZipArchiveMode]::Create, [System.Text.Encoding]::UTF8)
                        $filename = (Get-Item -LiteralPath $src).Name
                        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $src, $filename, 0) | Out-Null
                    }
                    #$result.changed = $true
                }
            }
            catch {
                # If zip is opened but something fails afterwards, it will be left on disk. Need to cleanup
                # Duplicated here and not just finally because we have to dispose it before we can delete it
                # or the unmanaged file is locked
                if ((Get-Variable -Name archive -ErrorAction SilentlyContinue) -and ($null -ne $archive)) {
                    $archive.Dispose()
                }
                Remove-BrokenZip $dest
                Fail-Json -obj $result -message "Error creating zip file '$dest': $($_.Exception.Message)"

            }
            finally {
                # Call dispose to get rid of the unmanaged object
                if ((Get-Variable -Name archive -ErrorAction SilentlyContinue) -and ($null -ne $archive)) {
                    $archive.Dispose()
                }
            }
        }
        "Undefined" { # This should never be hit as we check, but leave in just in case the early check is modified.
            #Fail-Json -obj $result -message "Could not find any available compression utilities: $($_.Exception.Message)"
            Fail-Json -obj $result -message "Could not find any available compression utilities: PowerShell 5.0 and .NET Framework 4.5 are minimally required.  Please install the Windows Management Framework 5.0 or higher."
        }
    }

}

# BEGIN: Determine which type of compression utils to use: PowerShell, .NET or COM (to follow dev standards)
# Try PowerShell native first, then .NET 4.5
Add-Type -ErrorAction SilentlyContinue -TypeDefinition @"
    public enum CompressionUtils
    {
        PowerShell,
        DotNet,
        Undefined
    }
"@

$try_dotnet = $false
try {
    # Determines if the Compress-Archive command is available (preferred use)
    # if not will check if dotnet libs are available (.NET 4.5 or greater)
    Get-Command -Name Compress-Archive | Out-Null
    $utils_available = [CompressionUtils]::PowerShell
}
catch {
    $try_dotnet = $true
}

if ($try_dotnet) {
    try {
        # determines if .net 4.5 is available, if this fails we can't
        # fall back to the legacy COM Shell.Application to extract the zip because
        # the options don't allow it to be suppressed in the UI
        Add-Type -AssemblyName System.IO.Compression.FileSystem | Out-Null
        Add-Type -AssemblyName System.IO.Compression | Out-Null
        $utils_available = [CompressionUtils]::DotNet
    }
    catch {
        # default to Undefined
        $utils_available = [CompressionUtils]::Undefined
    }

}

$result.utils_used = $utils_available.ToString()
# END: Determine which type of compression utils to use: PowerShell or .NET or COM (to follow dev standards)

if ($utils_available -eq [CompressionUtils]::Undefined) {
    Fail-Json -obj $result -message "Could not find any available compression utilities: PowerShell 5.0 and .NET Framework 4.5 are minimally required.  Please install the Windows Management Framework 5.0 or higher."
}

# Validate that the extension of the destination zip file is 'zip' - only one supported right now
$src_ext = (Split-Path $dest -Leaf).Split('.')[-1]
if ($src_ext -ne "zip") {
    Fail-Json -obj $result -message "The destination zip file specified '$dest' must have an extension of '.zip'."
}

# Validate src path exists
# Ansible.ModuleUtils.Legacy.psm1 checks this for a type of 'PATH' so right now this is duplicate
# but will help if the type is changed to 'LIST' to support single or multiple src values
# Also may want to look at adding support here for expanding environment vars when moving to list
# https://github.com/ansible/ansible/blob/v2.4.1.0-1/lib/ansible/module_utils/powershell/Ansible.ModuleUtils.Legacy.psm1#L209

If (-not (Test-Path -LiteralPath $src)) {
    Fail-Json -obj $result -message "The source path specified '$src' could not be found."
}

# Ensure dest zip DOES NOT exist unless creates attribute specified (TODO: support "FORCE" option)
if ($creates -and (Test-Path -LiteralPath $creates)) {
    Exit-Json -obj $result -message "The destination zip file '$dest' specified in the creates attribute exists.  Nothing changed"
}
elseif (Test-Path -LiteralPath $dest) {
    Fail-Json -obj $result -message "The destination zip file specified '$dest' already exists. Adding files to existing zips not yet supported"
}

# Ensure we don't have any files over 2GB in size (PowerShell & .NET Limitation)
$large_files = New-Object -Type System.Collections.ArrayList
Find-LargeFiles -src $src -large_files ([ref]$large_files)

if ($large_files) {
    $result.large_files = $large_files.ToArray()
    Fail-Json -obj $result -message "At least one file in $src is over maximum size 2,097,152,000 bytes.  See large_files attribute for full list"
}

# Attempt to create the zip file
New-ZipFile -src $src -dest $dest -utils_available $utils_available

# handle delete_src task option
if ($delete_src) {
    Remove-Source $src
}

$result.changed = $true

Exit-Json $result