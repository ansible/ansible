#!powershell

# Copyright: (c) 2018, Ansible Project
# Copyright: (c) 2018, Simon Baerlocher <s.baerlocher@sbaerlocher.ch>
# Copyright: (c) 2018, ITIGO AG <opensource@itigo.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil
#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "pinned" -validateset "pinned", "unpinned"
$version = Get-AnsibleParam -obj $params -name "version" -type "str"

# Create a new result object
$result = @{
    changed = $false
}

$choco_app = Get-Command -Name choco.exe -CommandType Application -ErrorAction SilentlyContinue
if (-not $choco_app) {
    Fail-Json -obj $result -message "Failed to find Chocolatey installation, make sure choco.exe is in the PATH env value"
}

function Get-ChocolateyPin {

    param(
        $choco_app,
        $name
    )

    $res = Run-Command -command "`"$($choco_app.Path)`" pin list -r"
    if ($res.rc -ne 0) {
        $result.stdout = $res.stdout
        $result.stderr = $res.stderr
        $result.rc = $res.rc
        Fail-Json -obj $result -message "Failed to list pinned packages, see stderr"
    }

    $res.stdout -split "`r`n" | Where-Object { $_ -ne "" } | ForEach-Object {
        $pin_split = $_ -split "\|"
        if ($name -eq $pin_split[0]) {
            return ,$true
        } else {
            return ,$false
        }
    }
}

function Set-ChocolateyPin {

    param(
        $choco_app,
        $name,
        $version
    )

    if ($version -eq $null) {
        $command = Argv-ToString -arguments @($choco_app.Path, "pin", "add", "--name", $name)
        $res = Run-Command -command $command
        if ($res.rc -ne 0) {
            $result.stdout = $res.stdout
            $result.stderr = $res.stderr
            $result.rc = $res.rc
            Fail-Json -obj $result -message "Failed to pin package $($name), see stderr"
        }
    } else {
        $command = Argv-ToString -arguments @($choco_app.Path, "pin", "add", "--name", $name, "--version", $version)
        $res = Run-Command -command $command
        $result.new_result = $res
        if ($res.rc -ne 0) {
            $result.stdout = $res.stdout
            $result.stderr = $res.stderr
            $result.rc = $res.rc
            Fail-Json -obj $result -message "Failed to pin Chocolatey Package $($name) ($($version)), see stderr"
        }
    }
}

function Remove-ChocolateyPin {

    param(
        $choco_app,
        $name
    )

    $command = Argv-ToString -arguments @($choco_app.Path, "pin", "remove", "--name", $name)
    $res = Run-Command -command $command
    if ($res.rc -ne 0) {
           $result.stdout = $res.stdout
            $result.stderr = $res.stderr
            $result.rc = $res.rc
        Fail-Json -obj $result -message "Failed to unpin Chocolatey Package '$name', see stderr"
    }
}

$pin_info = Get-ChocolateyPin -choco_app $choco_app -name $name
if ($state -eq "pinned") {
    if (-not $pin_info) {
        if (-not $check_mode) {
            Set-ChocolateyPin -choco_app $choco_app -name $name -version $version
        }
        $result.changed = $true
    }
} elseif ($state -eq "unpinned") {
    if ($pin_info) {
        if (-not $check_mode) {
            Remove-ChocolateyPin -choco_app $choco_app -name $name
        }
        $result.changed = $true
    }
}

# Return result
Exit-Json -obj $result
