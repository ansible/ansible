#!powershell
# This file is part of Ansible

# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

Import-Module -Name WebAdministration
$params = Parse-Args $args -supports_check_mode $true
$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true

$site = Get-Website -Name $name

$result = @{}
if ($site -eq $null) {
    $result.exists = $false
} else {
    $result.exists = $true
    $site_config = Get-WebConfiguration -Filter "System.WebServer/Security/Authentication/*" -PSPath "IIS:\Sites\$name"
    $http_bindings = $site.bindings.Collection | Where-Object { $_.protocol -eq "http" }
    $https_bindings = $site.bindings.Collection | Where-Object { $_.protocol -eq "https" }

    $result.http = @{
        binding = $http_bindings.bindingInformation
    }
    $result.https = @{
        binding = $https_bindings.bindingInformation
        sslFlags = $https_bindings.sslFlags
        store = ($https_bindings.Attributes | Where-Object { $_.Name -eq "certificateStoreName" }).Value
        hash = ($https_bindings.Attributes | Where-Object { $_.Name -eq "certificateHash" }).Value
    }
    $result.auth = @{
        anonymous = ($site_config | Where-Object { $_.ElementTagName -like "*anonymous*" }).enabled
        basic = ($site_config | Where-Object { $_.ElementTagName -like "*basic*" }).enabled
        digest = ($site_config | Where-Object { $_.ElementTagName -like "*digest*" }).enabled
        windows = ($site_config | Where-Object { $_.ElementTagName -like "*windows*" }).enabled
    }
}

Exit-Json -obj $result
