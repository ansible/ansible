#!powershell

# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$result = @{
    changed = $false
    sources = [System.Collections.Generic.List`1[System.Collections.Hashtable]]@()
}

$choco_app = Get-Command -Name choco.exe -CommandType Application
$choco_config_path = "$(Split-Path -Path (Split-Path -Path $choco_app.Path))\config\chocolatey.config"

[xml]$choco_config = Get-Content -LiteralPath $choco_config_path
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
    $result.sources.Add($source_info)
}

Exit-Json -obj $result
