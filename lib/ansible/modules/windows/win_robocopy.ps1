#!powershell

# Copyright: (c) 2015, Corwin Brown <corwin.brown@maxpoint.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$src = Get-AnsibleParam -obj $params -name "src" -type "path" -failifempty $true
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path" -failifempty $true
$purge = Get-AnsibleParam -obj $params -name "purge" -type "bool" -default $false
$recurse = Get-AnsibleParam -obj $params -name "recurse" -type "bool" -default $false
$flags = Get-AnsibleParam -obj $params -name "flags" -type "str"

$result = @{
    changed = $false
    dest = $dest
    purge = $purge
    recurse = $recurse
    src = $src
}

# Search for an Error Message
# Robocopy seems to display an error after 3 '-----' separator lines
Function SearchForError($cmd_output, $default_msg) {
    $separator_count = 0
    $error_msg = $default_msg
    ForEach ($line in $cmd_output) {
        if (-not $line) {
            continue
        }

        if ($separator_count -ne 3) {
            if (Select-String -InputObject $line -pattern "^(\s+)?(\-+)(\s+)?$") {
                $separator_count += 1
            }
        } else {
            if (Select-String -InputObject $line -pattern "error") {
                $error_msg = $line
                break
            }
        }
    }

    return $error_msg
}

if (-not (Test-Path -Path $src)) {
    Fail-Json $result "$src does not exist!"
}

# Build Arguments
$robocopy_opts = @($src, $dest)

if ($check_mode) {
    $robocopy_opts += "/l"
}

if ($flags -eq $null) {
    if ($purge) {
        $robocopy_opts += "/purge"
    }

    if ($recurse) {
        $robocopy_opts += "/e"
    }
} else {
    ForEach ($f in $flags.split(" ")) {
        $robocopy_opts += $f
    }
}

$result.flags = $flags
$result.cmd = "$robocopy $robocopy_opts"

Try {
    $robocopy_output = &robocopy $robocopy_opts
    $rc = $LASTEXITCODE
} Catch {
    Fail-Json $result "Error synchronizing $src to $dest! Msg: $($_.Exception.Message)"
}

$result.msg = "Success"
$result.output = $robocopy_output
$result.return_code = $rc # Backward compatibility
$result.rc = $rc

switch ($rc) {

    0 {
        $result.msg = "No files copied."
    }
    1 {
        $result.msg = "Files copied successfully!"
        $result.changed = $true
        $result.failed = $false
    }
    2 {
        $result.msg = "Some Extra files or directories were detected. No files were copied."
        Add-Warning $result $result.msg
        $result.failed = $false
    }
    3 {
        $result.msg = "(2+1) Some files were copied. Additional files were present."
        Add-Warning $result $result.msg
        $result.changed = $true
        $result.failed = $false
    }
    4 {
        $result.msg = "Some mismatched files or directories were detected. Housekeeping might be required!"
        Add-Warning $result $result.msg
        $result.changed = $true
        $result.failed = $false
    }
    5 {
        $result.msg = "(4+1) Some files were copied. Some files were mismatched."
        Add-Warning $result $result.msg
        $result.changed = $true
        $result.failed = $false
    }
    6 {
        $result.msg = "(4+2) Additional files and mismatched files exist. No files were copied."
        $result.failed = $false
    }
    7 {
        $result.msg = "(4+1+2) Files were copied, a file mismatch was present, and additional files were present."
        Add-Warning $result $result.msg
        $result.changed = $true
        $result.failed = $false
    }
    8 {
        Fail-Json $result (SearchForError $robocopy_output "Some files or directories could not be copied!")
    }
    { @(9, 10, 11, 12, 13, 14, 15) -contains $_ } {
        Fail-Json $result (SearchForError $robocopy_output "Fatal error. Check log message!")
    }
    16 {
        Fail-Json $result (SearchForError $robocopy_output "Serious Error! No files were copied! Do you have permissions to access $src and $dest?")
    }

}

Exit-Json $result
