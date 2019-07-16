#!powershell

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

function Get-EnabledPlugins($rabbitmq_plugins_cmd)
{
    $list_plugins_cmd = "$rabbitmq_plugins_cmd list -E -m"
    try {
        $enabled_plugins = @(Invoke-Expression "& $list_plugins_cmd" | Where-Object { $_  })
        return ,$enabled_plugins
    }
    catch {
        Fail-Json -obj $result -message "Can't execute `"$($list_plugins_cmd)`": $($_.Exception.Message)"
    }
}

function Enable-Plugin($rabbitmq_plugins_cmd, $plugin_name)
{
    $enable_plugin_cmd = "$rabbitmq_plugins_cmd enable $plugin_name"
    try {
        Invoke-Expression "& $enable_plugin_cmd"
    }
    catch {
        Fail-Json -obj $result -message "Can't execute `"$($enable_plugin_cmd)`": $($_.Exception.Message)"
    }
}

function Disable-Plugin($rabbitmq_plugins_cmd, $plugin_name)
{
    $enable_plugin_cmd = "$rabbitmq_plugins_cmd disable $plugin_name"
    try {
        Invoke-Expression "& $enable_plugin_cmd"
    }
    catch {
        Fail-Json -obj $result -message "Can't execute `"$($enable_plugin_cmd)`": $($_.Exception.Message)"
    }
}

function Get-RabbitmqPathFromRegistry
{
    $reg64Path = "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\RabbitMQ"
    $reg32Path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\RabbitMQ"

    if (Test-Path $reg64Path) {
        $regPath = $reg64Path
    } elseif (Test-Path $reg32Path) {
        $regPath = $reg32Path
    }

    if ($regPath) {
        $path = Split-Path -Parent (Get-ItemProperty $regPath "UninstallString").UninstallString
        $version = (Get-ItemProperty $regPath "DisplayVersion").DisplayVersion
        return "$path\rabbitmq_server-$version"
    }
}

function Get-RabbitmqBinPath($installation_path)
{
    $result = Join-Path -Path $installation_path -ChildPath 'bin'
    if (Test-Path $result) {
        return $result
    }

    $result = Join-Path -Path $installation_path -ChildPath 'sbin'
    if (Test-Path $result) {
        return $result
    }
}

$ErrorActionPreference = "Stop"

$result = @{
    changed = $false
    enabled = @()
    disabled = @()
}

$params = Parse-Args $args -supports_check_mode $true;
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_support = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$names = Get-AnsibleParam -obj $params -name "names" -type "str" -failifempty $true -aliases "name"
$new_only = Get-AnsibleParam -obj $params -name "new_only" -type "bool" -default $false
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "enabled" -validateset "enabled","disabled"
$prefix = Get-AnsibleParam -obj $params -name "prefix" -type "str"

if ($diff_support) {
    $result.diff = @{}
    $result.diff.prepared = ""
}

$plugins = $names.Split(",")

if ($prefix) {
    $rabbitmq_bin_path = Get-RabbitmqBinPath -installation_path $prefix
    if (-not $rabbitmq_bin_path) {
        Fail-Json -obj $result -message "No binary folder in prefix `"$($prefix)`""
    }
} else {
    $rabbitmq_reg_path = Get-RabbitmqPathFromRegistry
    if ($rabbitmq_reg_path) {
        $rabbitmq_bin_path = Get-RabbitmqBinPath -installation_path $rabbitmq_reg_path
    }
}

if ($rabbitmq_bin_path) {
    $rabbitmq_plugins_cmd = "'$(Join-Path -Path $rabbitmq_bin_path -ChildPath "rabbitmq-plugins")'"
} else {
    $rabbitmq_plugins_cmd = "rabbitmq-plugins"
}

$enabled_plugins = Get-EnabledPlugins -rabbitmq_plugins_cmd $rabbitmq_plugins_cmd

if ($state -eq "enabled") {
    $plugins_to_enable = $plugins | Where-Object {-not ($enabled_plugins -contains $_)}
    foreach ($plugin in $plugins_to_enable) {
        if (-not $check_mode) {
            Enable-Plugin -rabbitmq_plugins_cmd $rabbitmq_plugins_cmd -plugin_name $plugin
        }
        if ($diff_support) {
            $result.diff.prepared += "+[$plugin]`n"
        }
        $result.enabled += $plugin
        $result.changed = $true
    }

    if (-not $new_only) {
        $plugins_to_disable = $enabled_plugins | Where-Object {-not ($plugins -contains $_)}
        foreach ($plugin in $plugins_to_disable) {
            if (-not $check_mode) {
                Disable-Plugin -rabbitmq_plugins_cmd $rabbitmq_plugins_cmd -plugin_name $plugin
            }
            if ($diff_support) {
                $result.diff.prepared += "-[$plugin]`n"
            }
            $result.disabled += $plugin
            $result.changed = $true
        }
    }
} else {
    $plugins_to_disable = $enabled_plugins | Where-Object {$plugins -contains $_}
    foreach ($plugin in $plugins_to_disable) {
        if (-not $check_mode) {
            Disable-Plugin -rabbitmq_plugins_cmd $rabbitmq_plugins_cmd -plugin_name $plugin
        }
        if ($diff_support) {
            $result.diff.prepared += "-[$plugin]`n"
        }
        $result.disabled += $plugin
        $result.changed = $true
    }
}

Exit-Json $result
