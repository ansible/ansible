#!powershell

# Copyright: (c) 2016, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.LinkUtil

$spec = @{
    options = @{
        paths = @{ type = "list"; elements = "str"; required = $true }
        age = @{ type = "str" }
        age_stamp = @{ type = "str"; default = "mtime"; choices = "mtime", "ctime", "atime" }
        file_type = @{ type = "str"; default = "file"; choices = "file", "directory" }
        follow = @{ type = "bool"; default = $false }
        hidden = @{ type = "bool"; default = $false }
        patterns = @{ type = "list"; elements = "str"; aliases = "regex", "regexp" }
        recurse = @{ type = "bool"; default = $false }
        size = @{ type = "str" }
        use_regex = @{ type = "bool"; default = $false }
        get_checksum = @{ type = "bool"; default = $true }
        checksum_algorithm = @{ type = "str"; default = "sha1"; choices = "md5", "sha1", "sha256", "sha384", "sha512" }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$paths = $module.Params.paths
$age = $module.Params.age
$age_stamp = $module.Params.age_stamp
$file_type = $module.Params.file_type
$follow = $module.Params.follow
$hidden = $module.Params.hidden
$patterns = $module.Params.patterns
$recurse = $module.Params.recurse
$size = $module.Params.size
$use_regex = $module.Params.use_regex
$get_checksum = $module.Params.get_checksum
$checksum_algorithm = $module.Params.checksum_algorithm

$module.Result.examined = 0
$module.Result.files = @()
$module.Result.matched = 0

Load-LinkUtils

Function Assert-Age {
    Param (
        [System.IO.FileSystemInfo]$File,
        [System.Int64]$Age,
        [System.String]$AgeStamp
    )

    $actual_age = switch ($AgeStamp) {
        mtime { $File.LastWriteTime.Ticks }
        ctime { $File.CreationTime.Ticks }
        atime { $File.LastAccessTime.Ticks }
    }

    if ($Age -ge 0) {
        return $Age -ge $actual_age
    } else {
        return ($Age * -1) -le $actual_age
    }
}

Function Assert-FileType {
    Param (
        [System.IO.FileSystemInfo]$File,
        [System.String]$FileType
    )

    $is_dir = $File.Attributes.HasFlag([System.IO.FileAttributes]::Directory)
    return ($FileType -eq 'directory' -and $is_dir) -or ($FileType -eq 'file' -and -not $is_dir)
}

Function Assert-FileHidden {
    Param (
        [System.IO.FileSystemInfo]$File,
        [Switch]$IsHidden
    )

    $file_is_hidden = $File.Attributes.HasFlag([System.IO.FileAttributes]::Hidden)
    return $IsHidden.IsPresent -eq $file_is_hidden
}


Function Assert-FileNamePattern {
    Param (
        [System.IO.FileSystemInfo]$File,
        [System.String[]]$Patterns,
        [Switch]$UseRegex
    )

    $valid_match = $false
    foreach ($pattern in $Patterns) {
        if ($UseRegex) {
            if ($File.Name -match $pattern) {
                $valid_match = $true
                break
            }
        } else {
            if ($File.Name -like $pattern) {
                $valid_match = $true
                break
            }
        }
    }
    return $valid_match
}

Function Assert-FileSize {
    Param (
        [System.IO.FileSystemInfo]$File,
        [System.Int64]$Size
    )

    if ($Size -ge 0) {
        return $File.Length -ge $Size
    } else {
        return $File.Length -le ($Size * -1)
    }
}

Function Get-FileChecksum {
    Param (
        [System.String]$Path,
        [System.String]$Algorithm
    )

    $sp = switch ($algorithm) {
        'md5' { New-Object -TypeName System.Security.Cryptography.MD5CryptoServiceProvider }
        'sha1' { New-Object -TypeName System.Security.Cryptography.SHA1CryptoServiceProvider }
        'sha256' { New-Object -TypeName System.Security.Cryptography.SHA256CryptoServiceProvider }
        'sha384' { New-Object -TypeName System.Security.Cryptography.SHA384CryptoServiceProvider }
        'sha512' { New-Object -TypeName System.Security.Cryptography.SHA512CryptoServiceProvider }
    }

    $fp = [System.IO.File]::Open($Path, [System.IO.Filemode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    try {
        $hash = [System.BitConverter]::ToString($sp.ComputeHash($fp)).Replace("-", "").ToLower()
    } finally {
        $fp.Dispose()
    }

    return $hash
}

Function Search-Path {
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory=$true)]
        [System.String]
        $Path,

        [Parameter(Mandatory=$true)]
        [AllowEmptyCollection()]
        [System.Collections.Generic.HashSet`1[System.String]]
        $CheckedPaths,

        [Parameter(Mandatory=$true)]
        [Object]
        $Module,

        [System.Int64]
        $Age,

        [System.String]
        $AgeStamp,

        [System.String]
        $FileType,

        [Switch]
        $Follow,

        [Switch]
        $GetChecksum,

        [Switch]
        $IsHidden,

        [System.String[]]
        $Patterns,

        [Switch]
        $Recurse,

        [System.Int64]
        $Size,

        [Switch]
        $UseRegex
    )

    $dir_obj = New-Object -TypeName System.IO.DirectoryInfo -ArgumentList $Path
    if ([Int32]$dir_obj.Attributes -eq -1) {
        $Module.Warn("Argument path '$Path' does not exist, skipping")
        return
    } elseif (-not $dir_obj.Attributes.HasFlag([System.IO.FileAttributes]::Directory)) {
        $Module.Warn("Argument path '$Path' is a file not a directory, skipping")
        return
    }

    $dir_files = @()
    try {
        $dir_files = $dir_obj.EnumerateFileSystemInfos("*", [System.IO.SearchOption]::TopDirectoryOnly)
    } catch [System.IO.DirectoryNotFoundException] { # Broken ReparsePoint/Symlink, cannot enumerate
    } catch [System.UnauthorizedAccessException] {}  # No ListDirectory permissions, Get-ChildItem ignored this

    foreach ($dir_child in $dir_files) {
        if ($dir_child.Attributes.HasFlag([System.IO.FileAttributes]::Directory) -and $Recurse) {
            if ($Follow -or -not $dir_child.Attributes.HasFlag([System.IO.FileAttributes]::ReparsePoint)) {
                $PSBoundParameters.Remove('Path') > $null
                Search-Path -Path $dir_child.FullName @PSBoundParameters
            }
        }

        # Check to see if we've already encountered this path and skip if we have.
        if (-not $CheckedPaths.Add($dir_child.FullName.ToLowerInvariant())) {
            continue
        }

        $Module.Result.examined++

        if ($PSBoundParameters.ContainsKey('Age')) {
            $age_match = Assert-Age -File $dir_child -Age $Age -AgeStamp $AgeStamp
        } else {
            $age_match = $true
        }

        $file_type_match = Assert-FileType -File $dir_child -FileType $FileType
        $hidden_match = Assert-FileHidden -File $dir_child -IsHidden:$IsHidden

        if ($PSBoundParameters.ContainsKey('Patterns')) {
            $pattern_match = Assert-FileNamePattern -File $dir_child -Patterns $Patterns -UseRegex:$UseRegex.IsPresent
        } else {
            $pattern_match = $true
        }

        if ($PSBoundParameters.ContainsKey('Size')) {
            $size_match = Assert-FileSize -File $dir_child -Size $Size
        } else {
            $size_match = $true
        }

        if (-not ($age_match -and $file_type_match -and $hidden_match -and $pattern_match -and $size_match)) {
            continue
        }

        # It passed all our filters so add it
        $module.Result.matched++

        # TODO: Make this generic so it can be shared with win_find and win_stat.
        $epoch = New-Object -Type System.DateTime -ArgumentList 1970, 1, 1, 0, 0, 0, 0
        $file_info = @{
            attributes = $dir_child.Attributes.ToString()
            checksum = $null
            creationtime = (New-TimeSpan -Start $epoch -End $dir_child.CreationTime).TotalSeconds
            exists = $true
            extension = $null
            filename = $dir_child.Name
            isarchive = $dir_child.Attributes.HasFlag([System.IO.FileAttributes]::Archive)
            isdir = $dir_child.Attributes.HasFlag([System.IO.FileAttributes]::Directory)
            ishidden = $dir_child.Attributes.HasFlag([System.IO.FileAttributes]::Hidden)
            isreadonly = $dir_child.Attributes.HasFlag([System.IO.FileAttributes]::ReadOnly)
            isreg = $false
            isshared = $false
            lastaccesstime = (New-TimeSpan -Start $epoch -End $dir_child.LastAccessTime).TotalSeconds
            lastwritetime = (New-TimeSpan -Start $epoch -End $dir_child.LastWriteTime).TotalSeconds
            owner = $null
            path = $dir_child.FullName
            sharename = $null
            size = $null
        }

        try {
            $file_info.owner = $dir_child.GetAccessControl().Owner
        } catch {}  # May not have rights to get the Owner, historical behaviour is to ignore.

        if ($dir_child.Attributes.HasFlag([System.IO.FileAttributes]::Directory)) {
            $share_info = Get-CimInstance -ClassName Win32_Share -Filter "Path='$($dir_child.FullName -replace '\\', '\\')'"
            if ($null -ne $share_info) {
                $file_info.isshared = $true
                $file_info.sharename = $share_info.Name
            }
        } else {
            $file_info.extension = $dir_child.Extension
            $file_info.isreg = $true
            $file_info.size = $dir_child.Length

            if ($GetChecksum) {
                try {
                    $file_info.checksum = Get-FileChecksum -Path $dir_child.FullName -Algorithm $checksum_algorithm
                } catch {}  # Just keep the checksum as $null in the case of a failure.
            }
        }

        # Append the link information if the path is a link
        $link_info = @{
            isjunction = $false
            islnk = $false
            nlink = 1
            lnk_source = $null
            lnk_target = $null
            hlnk_targets = @()
        }
        $link_stat = Get-Link -link_path $dir_child.FullName
        if ($null -ne $link_stat) {
            switch ($link_stat.Type) {
                "SymbolicLink" {
                    $link_info.islnk = $true
                    $link_info.isreg = $false
                    $link_info.lnk_source = $link_stat.AbsolutePath
                    $link_info.lnk_target = $link_stat.TargetPath
                    break
                }
                "JunctionPoint" {
                    $link_info.isjunction = $true
                    $link_info.isreg = $false
                    $link_info.lnk_source = $link_stat.AbsolutePath
                    $link_info.lnk_target = $link_stat.TargetPath
                    break
                }
                "HardLink" {
                    $link_info.nlink = $link_stat.HardTargets.Count

                    # remove current path from the targets
                    $hlnk_targets = $link_info.HardTargets | Where-Object { $_ -ne $dir_child.FullName }
                    $link_info.hlnk_targets = @($hlnk_targets)
                    break
                }
            }
        }
        foreach ($kv in $link_info.GetEnumerator()) {
            $file_info.$($kv.Key) = $kv.Value
        }

        # Output the file_info object
        $file_info
    }
}

$search_params = @{
    CheckedPaths = [System.Collections.Generic.HashSet`1[System.String]]@()
    GetChecksum = $get_checksum
    Module = $module
    FileType = $file_type
    Follow = $follow
    IsHidden = $hidden
    Recurse = $recurse
}

if ($null -ne $age) {
    $seconds_per_unit = @{'s'=1; 'm'=60; 'h'=3600; 'd'=86400; 'w'=604800}
    $seconds_pattern = '^(-?\d+)(s|m|h|d|w)?$'
    $match = $age -match $seconds_pattern
    if ($Match) {
        $specified_seconds = [Int64]$Matches[1]
        if ($null -eq $Matches[2]) {
            $chosen_unit = 's'
        } else {
            $chosen_unit = $Matches[2]
        }

        $total_seconds = $specified_seconds * ($seconds_per_unit.$chosen_unit)

        if ($total_seconds -ge 0) {
            $search_params.Age = (Get-Date).AddSeconds($total_seconds * -1).Ticks
        } else {
            # Make sure we add the positive value of seconds to current time then make it negative for later comparisons.
            $age = (Get-Date).AddSeconds($total_seconds).Ticks
            $search_params.Age = $age * -1
        }
        $search_params.AgeStamp = $age_stamp
    } else {
        $module.FailJson("Invalid age pattern specified")
    }
}

if ($null -ne $patterns) {
    $search_params.Patterns = $patterns
    $search_params.UseRegex = $use_regex
}

if ($null -ne $size) {
    $bytes_per_unit = @{'b'=1; 'k'=1KB; 'm'=1MB; 'g'=1GB;'t'=1TB}
    $size_pattern = '^(-?\d+)(b|k|m|g|t)?$'
    $match = $size -match $size_pattern
    if ($Match) {
        $specified_size = [Int64]$Matches[1]
        if ($null -eq $Matches[2]) {
            $chosen_byte = 'b'
        } else {
            $chosen_byte = $Matches[2]
        }

        $search_params.Size = $specified_size * ($bytes_per_unit.$chosen_byte)
    } else {
        $module.FailJson("Invalid size pattern specified")
    }
}

$matched_files = foreach ($path in $paths) {
    # Ensure we pass in an absolute path. We use the ExecutionContext as this is based on the PSProvider path not the
    # process location which can be different.
    $abs_path = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($path)
    Search-Path -Path $abs_path @search_params
}

# Make sure we sort the files in alphabetical order.
$module.Result.files = @() + ($matched_files | Sort-Object -Property {$_.path})

$module.ExitJson()

