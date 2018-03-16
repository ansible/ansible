#!powershell
# This file is part of Ansible

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Author: Erwan Quelin (mail:erwan.quelin@gmail.com - GitHub: @equelin - Twitter: @erwanquelin)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = 'Stop'

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

# Modules parameters

$src = Get-AnsibleParam -obj $params -name "src" -type "string" -failifempty $true
$version = Get-AnsibleParam -obj $params -name "version" -type "string" -failifempty $false

$result = @{
    changed = $false
}

if ($diff_mode) {
    $result.diff = @{}
}

# CODE
# Test if parameter $version is valid
Try {
    $version = [version]$version
}
Catch {
    Fail-Json -obj $result -message "$version is not a valid version format"
}

# Import Pester module if available
$Module = 'Pester'

If (-not (Get-Module -Name $Module -ErrorAction SilentlyContinue)) {
    If (Get-Module -Name $Module -ListAvailable -ErrorAction SilentlyContinue) {
        Import-Module $Module
    } else {
        Fail-Json -obj $result -message "Cannot find module: $Module. Check if pester is installed, and if it is not, install using win_psmodule or win_chocolatey."
    }
}

# Add actual pester's module version in the ansible's result variable
$Pester_version = (Get-Module -Name $Module).Version.ToString()
$result.pester_version = $Pester_version

# Test if the Pester module is available with a version greater or equal than the one specified in the $version parameter
If ((-not (Get-Module -Name $Module -ErrorAction SilentlyContinue | Where-Object {$_.Version -ge $version})) -and ($version)) {
    Fail-Json -obj $result -message "$Module version is not greater or equal to $version"
}

# Cleaning up $src (removing single quote if needed). Mandatory if the value is provided by an Ansible registerd path variable. 
$src = $src -replace "'"

# Testing if test file or directory exist
If (-not (Test-Path -Path $src)) {
    Fail-Json -obj $result -message "Cannot find file or directory: '$src' as it does not exist"
}

#Prepare Invoke-Pester parameters depending of the Pester's version.
#Invoke-Pester should not ouptut 
If ($result.pester_version -ge "4.0.0") {
    $Parameters = @{
        "show" = "none"
        "PassThru" = $True
    }
} else {
    $Parameters = @{
        "quiet" = $True
        "PassThru" = $True
    }
}

# Run Pester tests
If (Test-Path -Path $src -PathType Leaf) {
    Try {
        # Run Pester tests with a specific file
        If (-not $check_mode) {
            $Pester_result = Invoke-Pester $src @Parameters
        } else {
            $Pester_result = "Run pester test in the file: $src"
        }
    }
    Catch {
        Fail-Json -obj $result -message $_.Exception
    }
} else {
    $files = Get-ChildItem -Path $src | Where-Object {$_.extension -eq ".ps1"}
    Try {
        # Run Pester tests against all the .ps1 file in the local folder
        If (-not $check_mode) {
            $Pester_result = Invoke-Pester -Script $files.FullName @Parameters
        } else {
            $Pester_result = "Run pester test(s) who are in the folder: $src"
        } 
    }
    Catch {
        Fail-Json -obj $result -message $_.Exception.Message
    }
}

$result.pester_result = $Pester_result
$result.changed = $true

Exit-Json -obj $result