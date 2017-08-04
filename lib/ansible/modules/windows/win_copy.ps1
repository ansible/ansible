#!powershell
# This file is part of Ansible

# (c) 2015, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy.psm1

$ErrorActionPreference = 'Stop'

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

# there are 4 modes to win_copy which are driven by the action plugins:
#   explode: src is a zip file which needs to be extracted to dest, for use with multiple files
#   query: win_copy action plugin wants to get the state of remote files to check whether it needs to send them
#   remote: all copy action is happening remotely (remote_src=True)
#   single: a single file has been copied, also used with template
$mode = Get-AnsibleParam -obj $params -name "mode" -type "str" -default "single" -validateset "explode","query","remote","single"

# used in explode, remote and single mode
$src = Get-AnsibleParam -obj $params -name "src" -type "path" -failifempty ($mode -in @("explode","process","single"))
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path" -failifempty $true

# used in query and remote mode
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $true

# used in query mode, contains the local files/directories/symlinks that are to be copied
$files = Get-AnsibleParam -obj $params -name "files" -type "list"
$directories = Get-AnsibleParam -obj $params -name "directories" -type "list"
$symlinks = Get-AnsibleParam -obj $params -name "symlinks" -type "list"

$result = @{
    changed = $false
}

if ($diff_mode) {
    $result.diff = @{}
}

Function Copy-File($source, $dest) {
    $diff = ""
    $copy_file = $false
    $source_checksum = $null
    if ($force) {
        $source_checksum = Get-FileChecksum -path $source
    }

    if (Test-Path -Path $dest -PathType Container) {
        Fail-Json -obj $result -message "cannot copy file from $source to $($dest): dest is already a folder"
    } elseif (Test-Path -Path $dest -PathType Leaf) {
        if ($force) {
            $target_checksum = Get-FileChecksum -path $dest
            if ($source_checksum -ne $target_checksum) {
                $copy_file = $true
            }
        }
    } else {
        $copy_file = $true
    }

    if ($copy_file) {
        $file_dir = [System.IO.Path]::GetDirectoryName($dest)
        # validate the parent dir is not a file and that it exists
        if (Test-Path -Path $file_dir -PathType Leaf) {
            Fail-Json -obj $result -message "cannot copy file from $source to $($dest): object at dest parent dir is not a folder"
        } elseif (-not (Test-Path -Path $file_dir)) {
            # directory doesn't exist, need to create
            New-Item -Path $file_dir -ItemType Directory -WhatIf:$check_mode | Out-Null
            $diff += "+$file_dir`n"
        }

        if (Test-Path -Path $dest -PathType Leaf) {
            Remove-Item -Path $dest -Force -Recurse | Out-Null
            $diff += "-$dest`n"
        }

        if (-not $check_mode) {
            # cannot run with -WhatIf:$check_mode as if the parent dir didn't
            # exist and was created above would still not exist in check mode
            Copy-Item -Path $source -Destination $dest -Force | Out-Null
        }
        $diff += "+$dest`n"

        # make sure we set the attributes accordingly
        if (-not $check_mode) {
            $source_file = Get-Item -Path $source -Force
            $dest_file = Get-Item -Path $dest -Force
            $dest_file.Attributes = $source_file.Attributes
            $dest_file.SetAccessControl($source_file.GetAccessControl())
        }

        $result.changed = $true
    }

    # ugly but to save us from running the checksum twice, let's return it for
    # the main code to add it to $result
    return ,@{ diff = $diff; checksum = $source_checksum }
}

Function Copy-Folder($source, $dest) {
    $diff = ""
    $copy_folder = $false

    if (-not (Test-Path -Path $dest -PathType Container)) {
        $parent_dir = [System.IO.Path]::GetDirectoryName($dest)
        if (Test-Path -Path $parent_dir -PathType Leaf) {
            Fail-Json -obj $result -message "cannot copy file from $source to $($dest): object at dest parent dir is not a folder"
        }
        if (Test-Path -Path $dest -PathType Leaf) {
            Fail-Json -obj $result -message "cannot copy folder from $source to $($dest): dest is already a file"
        }

        $diff += "+$dest`n"
        New-Item -Path $dest -ItemType Container -WhatIf:$check_mode | Out-Null
        $result.changed = $true

        if (-not $check_mode) {
            $source_folder = Get-Item -Path $source -Force
            $dest_folder = Get-Item -Path $source -Force
            $dest_folder.Attributes = $source_folder.Attributes
            $dest_folder.SetAccessControl($source_folder.GetAccessControl())
        }
    }

    $child_items = Get-ChildItem -Path $source -Force
    foreach ($child_item in $child_items) {
        $dest_child_path = Join-Path -Path $dest -ChildPath $child_item.Name
        if ($child_item.PSIsContainer) {
            $diff += (Copy-Folder -source $child_item.Fullname -dest $dest_child_path)
        } else {
            $diff += (Copy-File -source $child_item.Fullname -dest $dest_child_path).diff
        }
    }

    return $diff
}

Function Get-FileSize($path) {
    $file = Get-Item -Path $path -Force
    $size = $null
    if ($file.PSIsContainer) {
        $dir_files_sum = Get-ChildItem $file.FullName -Recurse
        if ($dir_files_sum -eq $null -or ($dir_files_sum.PSObject.Properties.name -contains 'length' -eq $false)) {
            $size = 0
        } else {
            $size = ($dir_files_sum | Measure-Object -property length -sum).Sum
        }
    } else {
        $size = $file.Length
    }

    $size
}

if ($mode -eq "query") {
    # we only return a list of files/directories that need to be copied over
    # the source of the local file will be the key used
    $will_change = $false
    $changed_files = @()
    $changed_directories = @()
    $changed_symlinks = @()

    foreach ($file in $files) {
        $filename = $file.dest
        $local_checksum = $file.checksum

        $filepath = Join-Path -Path $dest -ChildPath $filename
        if (Test-Path -Path $filepath -PathType Leaf) {
            if ($force) {
                $checksum = Get-FileChecksum -path $filepath
                if ($checksum -ne $local_checksum) {
                    $will_change = $true
                    $changed_files += $file
                }
            }
        } elseif (Test-Path -Path $filepath -PathType Container) {
            Fail-Json -obj $result -message "cannot copy file to dest $($filepath): object at path is already a directory"
        } else {
            $will_change = $true
            $changed_files += $file
        }
    }

    foreach ($directory in $directories) {
        $dirname = $directory.dest

        $dirpath = Join-Path -Path $dest -ChildPath $dirname
        $parent_dir = [System.IO.Path]::GetDirectoryName($dirpath)
        if (Test-Path -Path $parent_dir -PathType Leaf) {
            Fail-Json -obj $result -message "cannot copy folder to dest $($dirpath): object at parent directory path is already a file"
        }
        if (Test-Path -Path $dirpath -PathType Leaf) {
            Fail-Json -obj $result -message "cannot copy folder to dest $($dirpath): object at path is already a file"
        } elseif (-not (Test-Path -Path $dirpath -PathType Container)) {
            $will_change = $true
            $changed_directories += $directory
        }
    }

    # TODO: Handle symlinks

    # Detect if the PS zip assemblies are available, this will control whether
    # the win_copy plugin will use explode as the mode or single
    try {
        Add-Type -Assembly System.IO.Compression.FileSystem | Out-Null
        Add-Type -Assembly System.IO.Compression | Out-Null
        $result.zip_available = $true
    } catch {
        $result.zip_available = $false
    }

    $result.will_change = $will_change
    $result.files = $changed_files
    $result.directories = $changed_directories
    $result.symlinks = $changed_symlinks
} elseif ($mode -eq "explode") {
    # a single zip file containing the files and directories needs to be
    # expanded this will always result in a change as the calculation is done
    # on the win_copy action plugin and is only run if a change needs to occur
    if (-not (Test-Path -Path $src -PathType Leaf)) {
        Fail-Json -obj $result -message "Cannot expand src zip file file: $src as it does not exist"
    }

    Add-Type -Assembly System.IO.Compression.FileSystem | Out-Null
    Add-Type -Assembly System.IO.Compression | Out-Null

    $archive = [System.IO.Compression.ZipFile]::Open($src, [System.IO.Compression.ZipArchiveMode]::Read, [System.Text.Encoding]::UTF8)
    foreach ($entry in $archive.Entries) {
        $entry_target_path = [System.IO.Path]::Combine($dest, $entry.FullName)
        $entry_dir = [System.IO.Path]::GetDirectoryName($entry_target_path)

        if (-not (Test-Path -Path $entry_dir)) {
            New-Item -Path $entry_dir -ItemType Directory -WhatIf:$check_mode | Out-Null
        }

        if (-not ($entry_target_path.EndsWith("`\") -or $entry_target_path.EndsWith("/"))) {
            if (-not $check_mode) {
                [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $entry_target_path, $true)
            }
        }
    }

    $result.changed = $true
} elseif ($mode -eq "remote") {
    # all copy actions are happening on the remote side (windows host), need
    # too copy source and dest using PS code
    $result.src = $src
    $result.dest = $dest

    if (-not (Test-Path -Path $src)) {
        Fail-Json -obj $result -message "Cannot copy src file: $src as it does not exist"
    }

    if (Test-Path -Path $src -PathType Container) {
        # we are copying a directory or the contents of a directory
        $result.operation = 'folder_copy'
        if ($src.EndsWith("/") -or $src.EndsWith("`\")) {
            # copying the folder's contents to dest
            $diff = ""
            $child_files = Get-ChildItem -Path $src -Force
            foreach ($child_file in $child_files) {
                $dest_child_path = Join-Path -Path $dest -ChildPath $child_file.Name
                if ($child_file.PSIsContainer) {
                    $diff += Copy-Folder -source $child_file.FullName -dest $dest_child_path
                } else {
                    $diff += (Copy-File -source $child_file.FullName -dest $dest_child_path).diff
                }
            }
        } else {
            # copying the folder and it's contents to dest
            $dest = Join-Path -Path $dest -ChildPath (Get-Item -Path $src -Force).Name
            $result.dest = $dest
            $diff = Copy-Folder -source $src -dest $dest
        }
    } else {
        # we are just copying a single file to dest
        $result.operation = 'file_copy'

        $source_basename = (Get-Item -Path $src -Force).Name
        $result.original_basename = $source_basename

        if ($dest.EndsWith("/") -or $dest.EndsWith("`\")) {
            $dest = Join-Path -Path $dest -ChildPath (Get-Item -Path $src -Force).Name
            $result.dest = $dest
        }
        $copy_result = Copy-File -source $src -dest $dest
        $diff = $copy_result.diff
        $result.checksum = $copy_result.checksum
    }

    # the file might not exist if running in check mode
    if (-not $check_mode -or (Test-Path -Path $dest -PathType Leaf)) {
        $result.size = Get-FileSize -path $dest
    } else {
        $result.size = $null
    }
    if ($diff_mode) {
        $result.diff.prepared = $diff
    }
} elseif ($mode -eq "single") {
    # a single file is located in src and we need to copy to dest, this will
    # always result in a change as the calculation is done on the Ansible side
    # before this is run
    if (-not (Test-Path -Path $src -PathType Leaf)) {
        Fail-Json -obj $result -message "Cannot copy src file: $src as it does not exist"
    }

    Copy-Item -Path $src -Destination $dest -Force -WhatIf:$check_mode | Out-Null
    $result.changed = $true
}

Exit-Json -obj $result
