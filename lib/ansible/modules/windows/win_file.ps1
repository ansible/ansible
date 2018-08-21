#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.LinkUtil
#Requires -Module Ansible.ModuleUtils.SID

$ErrorActionPreference = "Stop"

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -default $false
$diff = Get-AnsibleParam -obj $params -name "_ansible_diff" -default $false
$_original_basename = Get-AnsibleParam -obj $params -name "_original_basename" -type "str"  # internal use only, used with template/copy

$access_time = Get-AnsibleParam -obj $params -name "access_time" -type "str"
$access_time_format = Get-AnsibleParam -obj $params -name "access_time_format" -type "str" -default "yyyyMMddHHmm.ss"
$attributes = Get-AnsibleParam -obj $params -name "attributes" -type "list"
$creation_time = Get-AnsibleParam -obj $params -name "creation_time" -type "str" -default "preserve"
$creation_time_format = Get-AnsibleParam -obj $params -name "creation_time_format" -type "str" -default "yyyyMMddHHmm.ss"
$follow = Get-AnsibleParam -obj $params -name "follow" -type "bool" -default $true
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $false
$group = Get-AnsibleParam -obj $params -name "group" -type "str"
$path = Get-AnsibleParam -obj $params -name "path" -type "path" -failifempty $true -aliases "dest","name"
$owner = Get-AnsibleParam -obj $params -name "owner" -type "str"
$src = Get-AnsibleParam -obj $params -name "src" -type "path"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -validateset "absent","directory","file","hard","junction","link","touch"
$write_time = Get-AnsibleParam -obj $params -name "write_time" -type "str"
$write_time_format = Get-AnsibleParam -obj $params -name "write_time_format" -type "str" -default "yyyyMMddHHmm.ss"

$result = @{
    changed = $false
}

Import-LinkUtil

Function Get-CurrentState {
    param([String]$Path, [bool]$Follow)

    if ([Ansible.IO.Path]::IsPathRooted($Path)) {
        $abs_path = $Path
    } else {
        $abs_path = [Ansible.IO.Path]::GetFullPath([Ansible.IO.Path]::Combine($pwd.Path, $Path))
    }
    $path_state = @{
        file = $null  # the Ansible.IO object if state != absent
        link_info = $null  # the Ansible.LinkUtil.LinkInfo object if path is a link/junction/hardlink
        abs_path = $abs_path
        path = $Path
        state = "absent"
    }
    $path_file = Get-AnsibleItem -Path $abs_path -ErrorAction SilentlyContinue
    if ($path_file) {
        try {
            $path_link_info = Get-Link -link_path $abs_path
        } catch {
            Fail-Json -obj $result -message "Failed to get the link information of the file at '$abs_path': $($_.Exception.Message)"
        }

        # get the state of the link target if Follow is set and the item is a link or junction
        # keep following down until we reach the final object
        if ($path_link_info.Type -in @("SymbolicLink", "JunctionPoint") -and $Follow) {
            return ,(Get-CurrentState -Path $path_link_info.AbsolutePath -Follow $true)
        }

        $path_state.link_info = $path_link_info
        $path_state.file = $path_file

        if ($path_link_info.Type -eq "SymbolicLink") {
            $path_state.state = "link"
        } elseif ($path_link_info.Type -eq "JunctionPoint") {
            $path_state.state = "junction"
        } elseif ($path_link_info.Type -eq "HardLink") {
            $path_state.state = "hard"
        } elseif ($path_file.Attributes.HasFlag([System.IO.FileAttributes]::Directory)) {
            $path_state.state = "directory"
        } else {
            $path_state.state = "file"
        }
    }

    return ,$path_state
}

Function Set-StateAbsent {
    param([String]$Path, [bool]$DoDiff = $true)

    # the file module does not use follow when state=absent
    $current_state = Get-CurrentState -Path $Path -Follow $false
    $Path = $current_state.abs_path

    if ($current_state.state -ne "absent") {
        if (-not $check_mode) {
            try {
                if ($current_state.file -is [Ansible.IO.DirectoryInfo]) {
                    # DirectoryInfo has extra param that controls whether to delete recursively
                    $current_state.file.Delete($true)
                } else {
                    $current_state.file.Delete()
                }
            } catch [System.UnauthorizedAccessException] {
                Fail-Json -obj $result -message "Unable to delete $($current_state.state) at '$Path' due to access permissions: $($_.Exception.Message)"
            } catch [System.IO.IOException] {
                Fail-Json -obj $result -message "IOException while deleting $($current_state.state) at '$Path': $($_.Exception.Message)"
            } catch {
                Fail-Json -obj $result -message "Unknown exception while deleting $($current_state.state) at '$Path': $($_.Exception.Message)"
            }
        }
        $result.changed = $true
        if ($diff -and $DoDiff) {
            $result.diff.before.state = $current_state.state
            $result.diff.after.state = "absent"
        }
    }
    $result.path = $Path
}

Function Set-StateDirectory {
    param([String]$Path, [bool]$Follow)

    $current_state = Get-CurrentState -Path $Path -Follow $Follow
    $Path = $current_state.abs_path

    # return all the directories that were created so we apply the attributes to each
    $created_paths = [System.Collections.ArrayList]@()
    if ($current_state.state -eq "absent") {
        # create the directory
        if (-not $check_mode) {
            # determine what directories we need to create and set attributes on
            $current_dir = $Path
            do {
                $created_paths.Add($current_dir) > $null
                $current_dir = [Ansible.IO.Directory]::GetParent($current_dir).FullName
            } while (-not [Ansible.IO.Directory]::Exists($current_dir))

            # create the dir at Path which will create all parent directories
            try {
                [Ansible.IO.Directory]::CreateDirectory($Path) > $null
            } catch [System.UnauthorizedAccessException] {
                Fail-Json -obj $result -message "Unable to create directory at '$Path' due to access permissions: $($_.Exception.Message)"
            } catch {
                Fail-Json -obj $result -message "Unknown exception while creating directory at '$Path': $($_.Exception.Message)"
            }
        }
        $result.changed = $true
        if ($diff) {
            $result.diff.before.state = $current_state.state
            $result.diff.after.state = "directory"
        }
    } elseif ($current_state.state -ne "directory") {
        Fail-Json -obj $result -message "'$Path' already exists as a $($current_state.state)"
    } else {
        # add to created_paths so Set-StateAttribute will apply attributes accordingly
        $created_paths.Add($Path) > $null
    }
    $result.path = $Path

    return ,$created_paths
}

Function Set-StateFile {
    param([String]$Path, [bool]$Follow)

    $current_state = Get-CurrentState -Path $Path -Follow $Follow
    $Path = $current_state.abs_path

    # Ansible 2.11 will actually create the missing file, for now we need to keep backwards compatibility
    if ($current_state.state -eq "absent") {
        Add-DeprecationWarning -obj $result -message "In a future version of Ansible state=file will create the file if it does not exist" -version 2.11
    }
    if ($current_state.state -notin @("file", "hard")) {
        # state=file is pretty useless, will fail if the path is not a file
        Fail-Json -obj $result -message "file '$Path' is $($current_state.state), cannot continue"
    }

    $result.path = $Path
    return $Path
}

Function Set-StateHard {
    param([String]$Path, [String]$Source, [bool]$Follow, [bool]$Force)

    # don't follow path when state=hard
    $current_state = Get-CurrentState -Path $Path -Follow $false
    $Path = $current_state.abs_path

    # in case src is not set, try and get the source from one of the existing
    # targets, otherwise just fail
    if (-not $Source) {
        if ($current_state.state -eq "hard") {
            $source_files = $current_state.link_info.HardTargets | Where-Object { $_ -ne $Path }
            if ($source_files -is [array]) {
                $Source = $source_files[0]
            } else {
                $Source = $source_files
            }
        } else {
            Fail-Json -obj $result -message "src must be defined when state=hard, path does not exist, or is not a hard link"
        }
        $src_state = Get-CurrentState -Path $Source -Follow $false
    } else {
        if (-not [Ansible.IO.Path]::IsPathRooted($Source)) {
            $Source = [Ansible.IO.Path]::GetFullPath([Ansible.IO.Path]::Combine([Ansible.IO.Path]::GetDirectoryName($Path), $Source))
        }
        $src_state = Get-CurrentState -Path $Source -Follow $Follow
    }
    $Source = $src_state.abs_path

    if ($src_state.state -eq "absent") {
        Fail-Json -obj $result -message "The src file at '$Source' does not exist, cannot create a hard link to a non-existent source"
    } else {
        if ($src_state.file.Attributes.HasFlag([System.IO.FileAttributes]::Directory)) {
            Fail-Json -obj $result -message "The src file at '$Source' is a directory, cannot create a hard link to a directory"
        }
    }

    if ($current_state.state -in @("directory", "file", "junction", "link") -and -not $Force) {
        Fail-Json -obj $result -message "Cannot convert $($current_state.state) at '$Path' to a hard link, use force=yes to override"
    } elseif ($current_state.state -eq "directory") {
        # force=yes but cannot continue if directory contains files
        if ($current_state.file.GetFileSystemInfos().Length -gt 0) {
            Fail-Json -obj $result -message "The directory '$Path' is not empty, cannot convert to a hard link"
        }
    }

    $changed = $true
    if ($current_state.state -eq "hard") {
        if ($Source -in $current_state.link_info.HardTargets) {
            $changed = $false
        } elseif ($diff) {
            $result.diff.before.src = $current_state.link_info.HardTargets
            $result.diff.after.src = $Source
        }
    } elseif ($diff) {
        $result.diff.before.state = $current_state.state
        $result.diff.after.state = "hard"
    }

    if ($changed -and (-not $check_mode)) {
        if ($current_state.state -ne "absent") {
            Set-StateAbsent -Path $Path -DoDiff $false
        }

        try {
            New-Link -link_path $Path -link_target $Source -link_type "hard"
        } catch {
            Fail-Json -obj $result -message "Failed to create hard link at '$Path' that points to '$Source': $($_.Exception.Message)"
        }
    }
    $result.changed = $changed
    $result.path = $Path

    return $Path
}

Function Set-StateJunction {
    param([String]$Path, [String]$Source, [bool]$Follow, [bool]$Force)

    # don't follow path when state=junction
    $current_state = Get-CurrentState -Path $Path -Follow $false
    $Path = $current_state.abs_path

    # in case src is not set, try and get the source from the existing juntion,
    # otherwise just fail
    if (-not $Source) {
        if ($current_state.state -eq "junction") {
            $Source = $current_state.link_info.Absolutepath
        } else {
            Fail-Json -obj $result -message "src must be defined when state=junction, path does not exist, or is not a junction point"
        }

        $src_state = Get-CurrentState -Path $Source -Follow $false
    } else {
        if (-not [Ansible.IO.Path]::IsPathRooted($Source)) {
            $Source = [Ansible.IO.Path]::GetFullPath([Ansible.IO.Path]::Combine([Ansible.IO.Path]::GetDirectoryName($Path), $Source))
        }
        $src_state = Get-CurrentState -Path $Source -Follow $Follow
    }
    $Source = $src_state.abs_path

    if ($src_state.state -eq "absent") {
        if (-not $Force) {
            Fail-Json -obj $result -message "The src file at '$Source' does not exist, use force=yes to override and create the junction point"
        }
    } else {
        if (-not $src_state.file.Attributes.HasFlag([System.IO.FileAttributes]::Directory)) {
            Fail-Json -obj $result -message "The src file at '$Source' is a file, cannot create a junction point to a file"
        }
    }

    if ($current_state.state -in @("directory", "file", "hard", "link") -and -not $Force) {
        Fail-Json -obj $result -message "Cannot convert $($current_state.state) at '$Path' to a junction point, use force=yes to override"
    } elseif ($current_state.state -eq "directory") {
        # force=yes but cannot continue if directory contains files
        if ($current_state.file.GetFileSystemInfos().Length -gt 0) {
            Fail-Json -obj $result -message "The directory '$Path' is not empty, cannot convert to a junction point"
        }
    }

    $changed = $true
    if ($current_state.state -eq "junction") {
        if ($Source -eq $current_state.link_info.AbsolutePath) {
            $changed = $false
        } elseif ($diff) {
            $result.diff.before.src = $current_state.link_info.AbsolutePath
            $result.diff.after.src = $Source
        }
    } elseif ($diff) {
        $result.diff.before.state = $current_state.state
        $result.diff.after.state = "junction"
    }

    if ($changed -and -not $check_mode) {
        if ($current_state.state -ne "absent") {
            Set-StateAbsent -Path $Path -DoDiff $false
        }

        try {
            New-Link -link_path $Path -link_target $Source -link_type "junction"
        } catch {
            Fail-Json -obj $result -message "Failed to create junction point at '$Path' that points to '$Source': $($_.Exception.Message)"
        }
    }
    $result.changed = $changed
    $result.path = $Path

    return $Path
}

Function Set-StateLink {
    param([String]$Path, [String]$Source, [bool]$Follow, [bool]$Force)

    # don't follow path when state=link
    $current_state = Get-CurrentState -Path $Path -Follow $false
    $Path = $current_state.abs_path

    # in case src is not set, try and get the source from the existing link,
    # otherwise just fail
    if (-not $Source) {
        if ($current_state.state -eq "link") {
            $src_rel = $current_state.link_info.TargetPath
            $src_abs = $current_state.link_info.AbsolutePath
        } else {
            Fail-Json -obj $result -message "src must be defined when state=link, path does not exist, or is not a symbolic link"
        }

        $src_state = Get-CurrentState -Path $src_abs -Follow $false
    } else {
        $src_rel = $Source
        if ([Ansible.IO.Path]::IsPathRooted($Source)) {
            $src_abs = $Source
        } else {
            $src_abs = [Ansible.IO.Path]::GetFullPath([Ansible.IO.Path]::Combine([Ansible.IO.Path]::GetDirectoryName($Path), $Source))
        }

        # now get src info, follow if necessary and update the rel and abs if it followed a link
        $src_state = Get-CurrentState -Path $src_abs -Follow $Follow
        if ($src_state.path -ne $src_abs) {
            $src_rel = $src_state.path
            $src_abs = $src_state.abs_path
        }
    }

    if (-not $Force -and $src_state.state -eq "absent") {
        Fail-Json -obj $result -message "The src file at '$src_abs' does not exist, use force=yes to override and create the link"
    }

    if ($current_state.state -in @("directory", "file", "hard", "junction") -and -not $Force) {
        Fail-Json -obj $result -message "Cannot convert $($current_state.state) at '$Path' to a symbolic link, use force=yes to override"
    } elseif ($current_state.state -eq "directory") {
        # force=yes but cannot continue if directory contains files
        if ($current_state.file.GetFileSystemInfos().Length -gt 0) {
            Fail-Json -obj $result -message "The directory '$Path' is not empty, cannot convert to a symbolic link"
        }
    }

    $changed = $true
    if ($current_state.state -eq "link") {
        if ($current_state.link_info.TargetPath -eq $src_rel) {
            $changed = $false
        } elseif ($diff) {
            $result.diff.before.src = $current_state.link_info.TargetPath
            $result.diff.after.src = $src_rel
        }
    } elseif ($diff) {
        $result.diff.before.state = $current_state.state
        $result.diff.after.state = "link"
    }

    if ($changed -and -not $check_mode) {
        if ($current_state.state -ne "absent") {
            Set-StateAbsent -Path $current_state.path -DoDiff $false
        }

        try {
            New-Link -link_path $Path -link_target $src_rel -link_type "link"
        } catch {
            Fail-Json -obj $result -message "Failed to create symbolic link at '$Path' that points to '$src_rel': $($_.Exception.Message)"
        }
    }
    $result.changed = $changed
    $result.path = $Path

    return $Path
}

Function Set-StateTouch {
    param(
        [String]$Path,
        [bool]$Follow,
        # we only need to know if these were set by the user, not the actual value in this cmdlet
        [String]$LastAccessTime,
        [String]$LastWriteTime
    )

    $current_state = Get-CurrentState -Path $Path -Follow $follow
    $Path = $current_state.abs_path  # update Path in case we followed a link

    if ($current_state.state -eq "absent") {
        # create empty file
        if (-not $check_mode) {
            $fs = $null
            try {
                $fs = [Ansible.IO.File]::Create($Path)
            } catch [System.UnauthorizedAccessException] {
                Fail-Json -obj $result -message "Failed to touch a new file due to access permissions at '$Path': $($_.Exception.Message)"
            } catch [System.IO.DirectoryNotFoundException] {
                # file does not create the parent dirs so we won't either
                Fail-Json -obj $result -message "Failed to touch a new file without parent directories being present at '$Path': $($_.Exception.Message)"
            } catch {
                Fail-Json -obj $result -message "Unknown failure while touching a new file at '$Path': $($_.Exception.Message)"
            } finally {
                if ($null -ne $fs) {
                    $fs.Close()
                }
            }
        }
        if ($diff) {
            $result.diff.before.state = "absent"
            $result.diff.after.state = "touch"
        }
        $result.changed = $true
    } elseif (-not $LastAccessTime -or -not $LastWriteTime) {
        # either access or write wasn't set by the user so we follow the defaults of
        # state=touch which is to set these times to now. If an explicit value was
        # set, Set-StateAttribute would handle that logic
        $now_date = Get-Date

        $new_access_time = $null
        $new_write_time = $null
        if (-not $LastAccessTime) {
            $new_access_time = $now_date
        }
        if (-not $LastWriteTime) {
            $new_write_time = $now_date
        }
        
        if (-not $check_mode) {
            try {
                if ($new_access_time) {
                    $current_state.file.LastAccessTime = $new_access_time
                }
                if ($new_write_time) {
                    $current_state.file.LastWriteTime = $new_write_time    
                }
            } catch {
                Fail-Json -obj $result -message "Failed while touching target at '$($Path)': $($_.Exception.Message)"
            }
        }

        $result.changed = $true
        if ($diff) {
            $result.diff.before.state = $current_state.state
            $result.diff.after.state = "touch"
        }
    }
    $result.path = $Path

    return $Path
}

# FUTURE: make more generic and move this and Set-FileAttributes to FileUtil with DACL/SACL supports so other modules can use it
Function Set-FileTime {
    [CmdletBinding(SupportsShouldProcess=$true)]
    param(
        [Ansible.IO.FileSystemInfo]$File,
        [DateTime]$NowDateTime,
        [String]$DateTimeType,
        [String]$DateTime,
        [String]$Format,
        [Hashtable]$Diff,
        [String]$DiffLabel
    )

    if ($DateTime -eq "now") {
        $new_time = $NowDateTime
    } else {
        try {
            $new_time = [System.DateTime]::ParseExact($DateTime, $Format, [System.Globalization.CultureInfo]::InvariantCulture)
        } catch [System.FormatException] {
            throw "Failed to convert '$DateTime' to a DateTime as the format '$Format' was invalid: $($_.Exception.Message)"
        }
    }

    $actual_time = $File."$DateTimeType"
    $changed = $false
    if ($actual_time -ne $new_time) {
        if ($PSCmdlet.ShouldProcess($File.FullName, "Set $DateTimeType to $($new_time.ToString("o"))")) {
            try {
                $File."$DateTimeType" = $new_time
            } catch {
                throw "Failed to change the $DateTimeType of '$($Path)' to '$($new_time.ToString("o"))': $($_.Exception.Message)"
            }
        }
        $changed = $true
        if ($Diff) {
            $Diff.before."$DiffLabel" = $actual_time.ToString("o")
            $Diff.after."$DiffLabel" = $new_time.ToString("o")
        }
    }
    return $changed
}

Function Set-FileAttributes {
    <#
    .SYNOPSIS
    Idempotently sets a file attributes, security descriptors, and timestamps based on the user input.

    .PARAMETER Path
    [String] The path to the file to set

    .PARAMETER Attributes
    [String[]] A list of attributes to try and set, valid attributes are listed below. Prefix attribute with '-' to
    make sure the attribute is removed from the file.

    .PARAMETER Group
    [String] The account name or SID of an account to set as the file's primary group.

    .PARAMETER Owner
    [String] The account name or SID of an account to set as the file's owner.

    .PARAMETER CreationTime
    [String] The datetime as a string to set on the CreationTime file timestamp.

    .PARAMETER CreationTimeFormat
    [String] The .NET format for CreationTime that is used with System.DateTime.ParseExact.

    .PARAMETER LastAccessTime
    [String] The datetime as a string to set on the LastAccessTime file timestamp.

    .PARAMETER LastAccessTimeFormat
    [String] The .NET format for LastAccessTime that is used with System.DateTime.ParseExact.

    .PARAMETER LastWriteTime
    [String] The datetime as a string to set on the LastWriteTime file timestamp.

    .PARAMETER LastWriteTimeFormat
    [String] The .NET format for LastWriteTime that is used with System.DateTime.ParseExact.

    .PARAMETER Diff
    [Hashtable] A hashtable that is used to set the diff data in

    .PArameter

    .OUTPUTS
    [Hashtable] A hashtable that contains the following values
        [bool]changed - Whether a change occurred or not
        [Hashtable] diff - diff details of the operation performed

    .NOTES
    This is designed to be generic from the win_file module so it can be moved to a shared util. This will allow other
    modules to easily expose these options without duplicating the code. This is reliant on Ansible.ModuleUitls.SID
    to resolve the owner/group sids.
    #>
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSUseOutputTypeCorrectly", "", Justification="Seems to be a bug with PSScriptAnalyzer")]
    [CmdletBinding(SupportsShouldProcess=$true)]
    param(
        [Parameter(Mandatory=$true)][String]$Path,
        [String[]]$Attributes,
        [String]$Group,
        [String]$Owner,
        [String]$CreationTime,
        [String]$CreationTimeFormat,
        [String]$LastAccessTime,
        [String]$LastAccessTimeFormat,
        [String]$LastWriteTime,
        [String]$LastWriteTimeFormat,
        [Hashtable]$Diff
    )
    $file = Get-AnsibleItem -Path $Path
    $result = @{
        changed = $false
    }

    # parse the list of attributes
    $add_attributes = [System.Collections.ArrayList]@()
    $remove_attributes = [System.Collections.ArrayList]@()
    if ($Attributes) {
        $valid_attributes = @(
            "archive",
            "compressed",
            "encrypted",
            "hidden",
            "normal",
            "no_scrub_data",
            "not_content_indexed",
            "offline",
            "read_only",
            "sparse_file",
            "system",
            "temporary"
        )

        $normal_set = $false
        foreach ($attribute in $Attributes) {
            $add = $true
            if ($attribute.StartsWith("-")) {
                $attribute = $attribute.Substring(1)
                $add = $false
            }

            if ($attribute -notin $valid_attributes) {
                throw "Invalid attribute '$attribute', valid attributes are $($valid_attributes -join ",")"
            } elseif ($attribute -eq "normal" -and $add) {
                $normal_set = $true
            }
            $attribute_enum = [System.IO.FileAttributes]([System.Globalization.CultureInfo]::InvariantCulture.TextInfo.ToTitleCase($attribute) -replace "_", "")

            if ($add) {
                $add_attributes.Add($attribute_enum) > $null
            } else {
                $remove_attributes.Add($attribute_enum) > $null
            }
        }

        # normal can only be set by itself, explicitly fail if set with other attributes to add
        if ($normal_set -and $add_attributes.Count -gt 1) {
            throw "The normal attribute is mutually exclusive from other attributes"
        }
    }

    $set_attributes = $file.Attributes
    $before_attributes = $file.Attributes
    $obj_name = "file"
    if ($set_attributes.HasFlag([System.IO.FileAttributes]::Directory)) {
        $obj_name = "directory"
    }
    $changed = $false
    foreach ($remove_attr in $remove_attributes) {
        if ($set_attributes.HasFlag($remove_attr)) {
            $set_attributes = [System.IO.FileAttributes]([int]$set_attributes - [int]$remove_attr)
            $changed = $true
        }
    }

    foreach ($add_attr in $add_attributes) {
        if (-not $set_attributes.HasFlag($add_attr)) {
            $set_attributes = [System.IO.FileAttributes]([int]$set_attributes + [int]$add_attr)
            $changed = $true
        }
    }
    # change set attribute to only be Normal as it isn't valid with any other attr
    if ($set_attributes.HasFlag([System.IO.FileAttributes]::Normal)) {
        $set_attributes = [System.IO.FileAttributes]::Normal
    }

    if ($changed) {
        if ($PSCmdlet.ShouldProcess($file.FullName, "Set attributes to '$($set_attributes.ToString())'")) {
            try {
                $file.Attributes = $set_attributes
            } catch {
                throw "Failed to set the attributes '$($set_attributes.ToString())' on $obj_name at '$($file.FullName)': $($_.Exception.Message)"
            }

            # verify the attributes were actually set
            $file.Refresh()
            $new_attributes = $file.Attributes
            if ($new_attributes.ToString() -ne $set_attributes.ToString()) {
                throw "Failed to set the attributes '$($set_attributes.ToString())' on $obj_name at '$($file.FullName)'"
            }
        } else {
            $new_attributes = $set_attributes
        }
        $result.changed = $true
        if ($Diff) {
            $Diff.before.attributes = $before_attributes.ToString()
            $Diff.after.attributes = $new_attributes.ToString()
        }
    }

    if ($Group) {
        $group_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList @(Convert-ToSID -account_name $Group)
        $current_sd = $file.GetAccessControl([System.Security.AccessControl.AccessControlSections]::Group)
        $current_group = $current_sd.GetGroup([System.Security.Principal.SecurityIdentifier])
        $before_group = "$($current_sd.GetGroup([System.Security.Principal.NTAccount]).ToString()) - $($current_group.Value)"

        if ($current_group -ne $group_sid) {
            $current_sd.SetGroup($group_sid)
            if ($PSCmdlet.ShouldProcess($file.FullName, "Set primary group to '$Group - $($group_sid.Value)'")) {
                try {
                    $file.SetAccessControl($current_sd)
                } catch {
                    throw "Failed to set the group to '$Group - $($group_sid.Value)' on $obj_name at '$($file.FullName)': $($_.Exception.Message)"
                }
            }
            $result.changed = $true
            if ($Diff) {
                $Diff.before.group = $before_group
                $Diff.after.group = "$Group - $($group_sid.Value)"
            }
        }
    }

    if ($Owner) {
        $owner_sid = New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList @(Convert-ToSID -account_name $Owner)
        $current_sd = $file.GetAccessControl([System.Security.AccessControl.AccessControlSections]::Owner)
        $current_owner = $current_sd.GetOwner([System.Security.Principal.SecurityIdentifier])
        $before_owner = "$($current_sd.GetOwner([System.Security.Principal.NTAccount]).ToString()) - $($current_owner.Value)"

        if ($current_owner -ne $owner_sid) {
            $current_sd.SetOwner($owner_sid)
            if ($PSCmdlet.ShouldProcess($file.FullName, "Set owner to '$Owner - $($owner_sid.Value)'")) {
                try {
                    $file.SetAccessControl($current_sd)
                } catch {
                    throw "Failed to set the owner to '$Owner - $($owner_sid.Value)' on $obj_name at '$($file.FullName)': $($_.Exception.Message)"
                }
            }
            $result.changed = $true
            if ($Diff) {
                $Diff.before.owner = $before_owner
                $Diff.after.owner = "$Owner - $($owner_sid.Value)"
            }
        }
    }

    $now_date = Get-Date
    if ($CreationTime -and $CreationTime -ne "preserve") {
        $changed = Set-FileTime -File $file -NowDateTime $now_date -DateTimeType "CreationTime" `
            -DateTime $CreationTime -Format $CreationTimeFormat -Diff $Diff -DiffLabel "creation_time"
        if ($changed) {
            $result.changed = $true
        }
    }
    if ($LastAccessTime -and $LastAccessTime -ne "preserve") {
        $changed = Set-FileTime -File $file -NowDateTime $now_date -DateTimeType "LastAccessTime" `
            -DateTime $LastAccessTime -Format $LastAccessTimeFormat -Diff $Diff -DiffLabel "access_time"
        if ($changed) {
            $result.changed = $true
        }
    }
    if ($LastWriteTime -and $LastWriteTime -ne "preserve") {
        $changed = Set-FileTime -File $file -NowDateTime $now_date -DateTimeType "LastWriteTime" `
            -DateTime $LastWriteTime -Format $LastWriteTimeFormat -Diff $Diff -DiffLabel "write_time"
        if ($changed) {
            $result.changed = $true
        }
    }

    return ,$result
}

# if _original_basename is supplied we need to append to the path
# This is different from the logic in the file module, it appends
# _original_basename and the filename part of src (if present) for specific
# states. While we could go down this path, we will make things simple for now
# and potentially add a new argument that controls this behaviour
if ((Test-AnsiblePath -Path $path -PathType Container) -and ($null -ne $_original_basename)) {
    $path = [Ansible.IO.Path]::Combine($path, $_original_basename)
}

# state defaults to the current state if path exists, otherwise to file
if ($null -eq $state) {
    $current_state = Get-CurrentState -Path $Path -Follow $false

    if ($current_state.state -eq "absent") {
        $state = "file"
    } else {
        $state = $current_state.state
    }
}

if ($null -ne $src -and $state -notin @("hard", "junction", "link")) {
    Fail-Json -obj $result -message "src option requires state to be 'hard', 'junction', or 'link'"
}

if ($diff) {
    $result.diff = @{
        before = @{
            path = $path
        }
        after = @{
            path = $path
        }
    }
}

$modified_paths = switch ($state) {
    absent { Set-StateAbsent -Path $path }
    directory { Set-StateDirectory -Path $path -Follow $follow }
    file { Set-StateFile -Path $path -Follow $follow }
    hard { Set-StateHard -Path $path -Source $src -Follow $follow -Force $force }
    junction { Set-StateJunction -Path $path -Source $src -Follow $follow -Force $force }
    link { Set-StateLink -Path $path -Source $src -Follow $follow -Force $force }
    # we only pass in access/write time so Set-StateTouch knows if the user set a value to be handled by
    # Set-StateAttribute (further down) or follow the default behaviour of setting to now
    touch { Set-StateTouch -Path $path -Follow $follow -LastAccessTime $access_time -LastWriteTime $write_time }
}

foreach($modified_path in $modified_paths) {
    # set's attributes, owner, group, and timestamps
    if ($check_mode -and -not (Test-AnsiblePath -path $modified_path)) {
        continue  # when in check mode we may not have created the file
    }

    $current_state = Get-CurrentState -Path $modified_path -Follow $follow
    $modified_path = $current_state.abs_path

    # there is a small chance if follow=true that the followed path may not
    # exist here (missing link target), raise warning if state is junction/link
    # like the file module does and fail if any other state
    if ($current_state.state -eq "absent") {
        if ($state -in @("junction", "link")) {
            Add-Warning -obj $result -message "Cannot set attributes on non-existent symlink or junction point target, follow should be set to False to avoid this"
            continue
        } else {
            Fail-Json -obj $result -message "Cannot set attributes on non-existent file '$modified_path'"
        }
    }
    $common_args = @{
        WhatIf = $check_mode
    }
    if ($diff) {
        $common_args.Diff = $result.diff
    }

    try {
        $res = Set-FileAttributes -Path $modified_path -Attributes $attributes -Group $group `
            -Owner $owner -CreationTime $creation_time -CreationTimeFormat $creation_time_format `
            -LastAccessTime $access_time -LastAccessTimeFormat $access_time_format `
            -LastWriteTime $write_time -LastWriteTimeFormat $write_time_format `
            @common_args
    } catch {
        Fail-Json -obj $result -message $_.Exception.Message
    }
    if ($res.changed) {
        $result.changed = $true
    }
}

Exit-Json -obj $result
