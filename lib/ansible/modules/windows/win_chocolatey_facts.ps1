#!powershell

# Copyright: (c) 2018, Simon Baerlocher <s.baerlocher@sbaerlocher.ch>
# Copyright: (c) 2018, ITIGO AG <opensource@itigo.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.CommandUtil
#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

# Create a new result object
$result = @{
    changed = $false
    ansible_facts = @{
        ansible_chocolatey =  @{
            config = @{}
            feature = @{}
            sources = @{}
            packages = @{}
        }
    }
}

try {
    $choco_app = Get-Command -Name choco.exe -CommandType Application -ErrorAction SilentlyContinue
} catch {
    Fail-Json -obj $result -message "Failed to find Chocolatey installation, make sure choco.exe is in the PATH env value"
}

Function Get-ChocolateyFeature {

    param($choco_app)

    $res = Run-Command -command "`"$($choco_app.Path)`" feature list -r"
    if ($res.rc -ne 0) {
        Fail-Json -obj $result -message "Failed to list Chocolatey features: $($res.stderr)"
    }
    $feature_info = @{}
    $res.stdout -split "`r`n" | Where-Object { $_ -ne "" } | ForEach-Object {
        $feature_split = $_ -split "\|"
        $feature_info."$($feature_split[0])" = $feature_split[1] -eq "Enabled"
    }

    $result.ansible_facts.ansible_chocolatey.feature =  $feature_info

}

Function Get-ChocolateyConfig {

    param($choco_app)

    $choco_config_path = "$(Split-Path -Path (Split-Path -Path $choco_app.Path))\config\chocolatey.config"
    if (-not (Test-Path -Path $choco_config_path)) {
        Fail-Json -obj $result -message "Expecting Chocolatey config file to exist at '$choco_config_path'"
    }

    try {
        [xml]$choco_config = Get-Content -Path $choco_config_path
    } catch {
        Fail-Json -obj $result -message "Failed to parse Chocolatey config file at '$choco_config_path': $($_.Exception.Message)"
    }

    $config_info = @{}
    foreach ($config in $choco_config.chocolatey.config.GetEnumerator()) {
        $config_info."$($config.key)" = $config.value
    }

    $result.ansible_facts.ansible_chocolatey.config =  $config_info
}

Function Get-ChocolateyPackages {

    param($choco_app)

    $res = Run-Command -command "`"$($choco_app.Path)`" list --local-only -r"
    if ($res.rc -ne 0) {
        Fail-Json -obj $result -message "Failed to list Chocolatey Packages: $($res.stderr)"
    }

    $packages_info = @{ }
    $res.stdout -split "`r`n" | Where-Object { $_ -ne "" } | ForEach-Object {
        $packages_split = $_ -split "\|"
        $packages_info."$($packages_split[0])" = $packages_split[1]
    }

    $result.ansible_facts.ansible_chocolatey.packages = $packages_info
}

Function Get-ChocolateySources {
    param($choco_app)

    $choco_config_path = "$(Split-Path -Path (Split-Path -Path $choco_app.Path))\config\chocolatey.config"
    if (-not (Test-Path -LiteralPath $choco_config_path)) {
        Fail-Json -obj $result -message "Expecting Chocolatey config file to exist at '$choco_config_path'"
    }

    try {
        [xml]$choco_config = Get-Content -Path $choco_config_path
    } catch {
        Fail-Json -obj $result -message "Failed to parse Chocolatey config file at '$choco_config_path': $($_.Exception.Message)"
    }

    $sources = [System.Collections.ArrayList]@()
    foreach ($xml_source in $choco_config.chocolatey.sources.GetEnumerator()) {
        $source_username = $xml_source.Attributes.GetNamedItem("user")
        if ($null -ne $source_username) {
            $source_username = $source_username.Value
        }

        # 0.9.9.9+
        $priority = $xml_source.Attributes.GetNamedItem("priority")
        if ($null -ne $priority) {
            $priority = [int]$priority.Value
        }

        # 0.9.10+
        $certificate = $xml_source.Attributes.GetNamedItem("certificate")
        if ($null -ne $certificate) {
            $certificate = $certificate.Value
        }

        # 0.10.4+
        $bypass_proxy = $xml_source.Attributes.GetNamedItem("bypassProxy")
        if ($null -ne $bypass_proxy) {
            $bypass_proxy = [System.Convert]::ToBoolean($bypass_proxy.Value)
        }
        $allow_self_service = $xml_source.Attributes.GetNamedItem("selfService")
        if ($null -ne $allow_self_service) {
            $allow_self_service = [System.Convert]::ToBoolean($allow_self_service.Value)
        }

        # 0.10.8+
        $admin_only = $xml_source.Attributes.GetNamedItem("adminOnly")
        if ($null -ne $admin_only) {
            $admin_only = [System.Convert]::ToBoolean($admin_only.Value)
        }

        $source_info = @{
            name = $xml_source.id
            source = $xml_source.value
            disabled = [System.Convert]::ToBoolean($xml_source.disabled)
            source_username = $source_username
            priority = $priority
            certificate = $certificate
            bypass_proxy = $bypass_proxy
            allow_self_service = $allow_self_service
            admin_only = $admin_only
        }
        $sources.Add($source_info) > $null
    }
    $result.ansible_facts.ansible_chocolatey.sources = $sources
}

Get-ChocolateyConfig -choco_app $choco_app
Get-ChocolateyFeature -choco_app $choco_app
Get-ChocolateyPackages -choco_app $choco_app
Get-ChocolateySources -choco_app $choco_app

# Return result
Exit-Json -obj $result
