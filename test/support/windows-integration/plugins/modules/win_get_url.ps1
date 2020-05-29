#!powershell

# Copyright: (c) 2015, Paul Durivage <paul.durivage@rackspace.com>
# Copyright: (c) 2015, Tal Auslander <tal@cloudshare.com>
# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# Copyright: (c) 2019, Viktor Utkin <viktor_utkin@epam.com>
# Copyright: (c) 2019, Uladzimir Klybik <uladzimir_klybik@epam.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.FileUtil
#Requires -Module Ansible.ModuleUtils.WebRequest

$spec = @{
    options = @{
        url = @{ type="str"; required=$true }
        dest = @{ type='path'; required=$true }
        force = @{ type='bool'; default=$true }
        checksum = @{ type='str' }
        checksum_algorithm = @{ type='str'; default='sha1'; choices = @("md5", "sha1", "sha256", "sha384", "sha512") }
        checksum_url = @{ type='str' }

       # Defined for the alias backwards compatibility, remove once aliases are removed
       url_username = @{
           aliases = @("user", "username")
           deprecated_aliases = @(
               @{ name = "user"; version = "2.14" },
               @{ name = "username"; version = "2.14" }
           )
       }
       url_password = @{
           aliases = @("password")
           deprecated_aliases = @(
               @{ name = "password"; version = "2.14" }
           )
       }
    }
    mutually_exclusive = @(
        ,@('checksum', 'checksum_url')
    )
    supports_check_mode = $true
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec, @(Get-AnsibleWebRequestSpec))

$url = $module.Params.url
$dest = $module.Params.dest
$force = $module.Params.force
$checksum = $module.Params.checksum
$checksum_algorithm = $module.Params.checksum_algorithm
$checksum_url = $module.Params.checksum_url

$module.Result.elapsed = 0
$module.Result.url = $url

Function Get-ChecksumFromUri {
    param(
        [Parameter(Mandatory=$true)][Ansible.Basic.AnsibleModule]$Module,
        [Parameter(Mandatory=$true)][Uri]$Uri,
        [Uri]$SourceUri
    )

    $script = {
        param($Response, $Stream)

        $read_stream = New-Object -TypeName System.IO.StreamReader -ArgumentList $Stream
        $web_checksum = $read_stream.ReadToEnd()
        $basename = (Split-Path -Path $SourceUri.LocalPath -Leaf)
        $basename = [regex]::Escape($basename)
        $web_checksum_str = $web_checksum -split '\r?\n' | Select-String -Pattern $("\s+\.?\/?\\?" + $basename + "\s*$")
        if (-not $web_checksum_str) {
            $Module.FailJson("Checksum record not found for file name '$basename' in file from url: '$Uri'")
        }

        $web_checksum_str_splitted = $web_checksum_str[0].ToString().split(" ", 2)
        $hash_from_file = $web_checksum_str_splitted[0].Trim()
        # Remove any non-alphanumeric characters
        $hash_from_file = $hash_from_file -replace '\W+', ''

        Write-Output -InputObject $hash_from_file
    }
    $web_request = Get-AnsibleWebRequest -Uri $Uri -Module $Module

    try {
        Invoke-WithWebRequest -Module $Module -Request $web_request -Script $script
    } catch {
        $Module.FailJson("Error when getting the remote checksum from '$Uri'. $($_.Exception.Message)", $_)
    }
}

Function Compare-ModifiedFile {
    <#
    .SYNOPSIS
    Compares the remote URI resource against the local Dest resource. Will
    return true if the LastWriteTime/LastModificationDate of the remote is
    newer than the local resource date.
    #>
    param(
        [Parameter(Mandatory=$true)][Ansible.Basic.AnsibleModule]$Module,
        [Parameter(Mandatory=$true)][Uri]$Uri,
        [Parameter(Mandatory=$true)][String]$Dest
    )

    $dest_last_mod = (Get-AnsibleItem -Path $Dest).LastWriteTimeUtc

    # If the URI is a file we don't need to go through the whole WebRequest
    if ($Uri.IsFile) {
        $src_last_mod = (Get-AnsibleItem -Path $Uri.AbsolutePath).LastWriteTimeUtc
    } else {
        $web_request = Get-AnsibleWebRequest -Uri $Uri -Module $Module
        $web_request.Method = switch ($web_request.GetType().Name) {
            FtpWebRequest { [System.Net.WebRequestMethods+Ftp]::GetDateTimestamp }
            HttpWebRequest { [System.Net.WebRequestMethods+Http]::Head }
        }
        $script = { param($Response, $Stream); $Response.LastModified }

        try {
            $src_last_mod = Invoke-WithWebRequest -Module $Module -Request $web_request -Script $script
        } catch {
            $Module.FailJson("Error when requesting 'Last-Modified' date from '$Uri'. $($_.Exception.Message)", $_)
        }
    }

    # Return $true if the Uri LastModification date is newer than the Dest LastModification date
    ((Get-Date -Date $src_last_mod).ToUniversalTime() -gt $dest_last_mod)
}

Function Get-Checksum {
    param(
        [Parameter(Mandatory=$true)][String]$Path,
        [String]$Algorithm = "sha1"
    )

    switch ($Algorithm) {
        'md5' { $sp = New-Object -TypeName System.Security.Cryptography.MD5CryptoServiceProvider }
        'sha1' { $sp = New-Object -TypeName System.Security.Cryptography.SHA1CryptoServiceProvider }
        'sha256' { $sp = New-Object -TypeName System.Security.Cryptography.SHA256CryptoServiceProvider }
        'sha384' { $sp = New-Object -TypeName System.Security.Cryptography.SHA384CryptoServiceProvider }
        'sha512' { $sp = New-Object -TypeName System.Security.Cryptography.SHA512CryptoServiceProvider }
    }

    $fs = [System.IO.File]::Open($Path, [System.IO.Filemode]::Open, [System.IO.FileAccess]::Read,
        [System.IO.FileShare]::ReadWrite)
    try {
        $hash = [System.BitConverter]::ToString($sp.ComputeHash($fs)).Replace("-", "").ToLower()
    } finally {
        $fs.Dispose()
    }
    return $hash
}

Function Invoke-DownloadFile {
    param(
        [Parameter(Mandatory=$true)][Ansible.Basic.AnsibleModule]$Module,
        [Parameter(Mandatory=$true)][Uri]$Uri,
        [Parameter(Mandatory=$true)][String]$Dest,
        [String]$Checksum,
        [String]$ChecksumAlgorithm
    )

    # Check $dest parent folder exists before attempting download, which avoids unhelpful generic error message.
    $dest_parent = Split-Path -LiteralPath $Dest
    if (-not (Test-Path -LiteralPath $dest_parent -PathType Container)) {
        $module.FailJson("The path '$dest_parent' does not exist for destination '$Dest', or is not visible to the current user.  Ensure download destination folder exists (perhaps using win_file state=directory) before win_get_url runs.")
    }

    $download_script = {
        param($Response, $Stream)

        # Download the file to a temporary directory so we can compare it
        $tmp_dest = Join-Path -Path $Module.Tmpdir -ChildPath ([System.IO.Path]::GetRandomFileName())
        $fs = [System.IO.File]::Create($tmp_dest)
        try {
            $Stream.CopyTo($fs)
            $fs.Flush()
        } finally {
            $fs.Dispose()
        }
        $tmp_checksum = Get-Checksum -Path $tmp_dest -Algorithm $ChecksumAlgorithm
        $Module.Result.checksum_src = $tmp_checksum

        # If the checksum has been set, verify the checksum of the remote against the input checksum.
        if ($Checksum -and $Checksum -ne $tmp_checksum) {
            $Module.FailJson(("The checksum for {0} did not match '{1}', it was '{2}'" -f $Uri, $Checksum, $tmp_checksum))
        }

        $download = $true
        if (Test-Path -LiteralPath $Dest) {
            # Validate the remote checksum against the existing downloaded file
            $dest_checksum = Get-Checksum -Path $Dest -Algorithm $ChecksumAlgorithm

            # If we don't need to download anything, save the dest checksum so we don't waste time calculating it
            # again at the end of the script
            if ($dest_checksum -eq $tmp_checksum) {
                $download = $false
                $Module.Result.checksum_dest = $dest_checksum
                $Module.Result.size = (Get-AnsibleItem -Path $Dest).Length
            }
        }

        if ($download) {
            Copy-Item -LiteralPath $tmp_dest -Destination $Dest -Force -WhatIf:$Module.CheckMode > $null
            $Module.Result.changed = $true
        }
    }
    $web_request = Get-AnsibleWebRequest -Uri $Uri -Module $Module

    try {
        Invoke-WithWebRequest -Module $Module -Request $web_request -Script $download_script
    } catch {
        $Module.FailJson("Error downloading '$Uri' to '$Dest': $($_.Exception.Message)", $_)
    }
}

# Use last part of url for dest file name if a directory is supplied for $dest
if (Test-Path -LiteralPath $dest -PathType Container) {
    $uri = [System.Uri]$url
    $basename = Split-Path -Path $uri.LocalPath -Leaf
    if ($uri.LocalPath -and $uri.LocalPath -ne '/' -and $basename) {
        $url_basename = Split-Path -Path $uri.LocalPath -Leaf
        $dest = Join-Path -Path $dest -ChildPath $url_basename
    } else {
        $dest = Join-Path -Path $dest -ChildPath $uri.Host
    }

    # Ensure we have a string instead of a PS object to avoid serialization issues
    $dest = $dest.ToString()
} elseif (([System.IO.Path]::GetFileName($dest)) -eq '') {
    # We have a trailing path separator
    $module.FailJson("The destination path '$dest' does not exist, or is not visible to the current user.  Ensure download destination folder exists (perhaps using win_file state=directory) before win_get_url runs.")
}

$module.Result.dest = $dest

if ($checksum) {
    $checksum = $checksum.Trim().ToLower()
}
if ($checksum_algorithm) {
    $checksum_algorithm = $checksum_algorithm.Trim().ToLower()
}
if ($checksum_url) {
    $checksum_url = $checksum_url.Trim()
}

# Check for case $checksum variable contain url. If yes, get file data from url and replace original value in $checksum
if ($checksum_url) {
    $checksum_uri = [System.Uri]$checksum_url
    if ($checksum_uri.Scheme -notin @("file", "ftp", "http", "https")) {
        $module.FailJson("Unsupported 'checksum_url' value for '$dest': '$checksum_url'")
    }

    $checksum = Get-ChecksumFromUri -Module $Module -Uri $checksum_uri -SourceUri $url
}

if ($force -or -not (Test-Path -LiteralPath $dest)) {
    # force=yes or dest does not exist, download the file
    # Note: Invoke-DownloadFile will compare the checksums internally if dest exists
    Invoke-DownloadFile -Module $module -Uri $url -Dest $dest -Checksum $checksum `
        -ChecksumAlgorithm $checksum_algorithm
} else {
    # force=no, we want to check the last modified dates and only download if they don't match
    $is_modified = Compare-ModifiedFile -Module $module -Uri $url -Dest $dest
    if ($is_modified) {
        Invoke-DownloadFile -Module $module -Uri $url -Dest $dest -Checksum $checksum `
            -ChecksumAlgorithm $checksum_algorithm
   }
}

if ((-not $module.Result.ContainsKey("checksum_dest")) -and (Test-Path -LiteralPath $dest)) {
    # Calculate the dest file checksum if it hasn't already been done
    $module.Result.checksum_dest = Get-Checksum -Path $dest -Algorithm $checksum_algorithm
    $module.Result.size = (Get-AnsibleItem -Path $dest).Length
}

$module.ExitJson()
