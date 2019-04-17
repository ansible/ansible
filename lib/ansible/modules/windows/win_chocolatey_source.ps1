#!powershell

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil
#Requires -Module Ansible.ModuleUtils.Legacy

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent", "disabled", "present"

$admin_only = Get-AnsibleParam -obj $params -name "admin_only" -type "bool"
$allow_self_service = Get-AnsibleParam -obj $params -name "allow_self_service" -type "bool"
$bypass_proxy = Get-AnsibleParam -obj $params -name "bypass_proxy" -type "bool"
$certificate = Get-AnsibleParam -obj $params -name "certificate" -type "str"
$certificate_password = Get-AnsibleParam -obj $params -name "certificate_password" -type "str"
$priority = Get-AnsibleParam -obj $params -name "priority" -type "int"
$source = Get-AnsibleParam -obj $params -name "source" -type "str"
$source_username = Get-AnsibleParam -obj $params -name "source_username" -type "str"
$source_password = Get-AnsibleParam -obj $params -name "source_password" -type "str" -failifempty ($null -ne $source_username)
$update_password = Get-AnsibleParam -obj $params -name "update_password" -type "str" -default "always" -validateset "always", "on_create"

$result = @{
    changed = $false
}
if ($diff) {
    $result.diff = @{
        before = @{}
        after = @{}
    }
}

Function Get-ChocolateySources {
    param($choco_app)

    $choco_config_path = "$(Split-Path -Path (Split-Path -Path $choco_app.Path))\config\chocolatey.config"
    if (-not (Test-Path -LiteralPath $choco_config_path)) {
        Fail-Json -obj $result -message "Expecting Chocolatey config file to exist at '$choco_config_path'"
    }

    # would prefer to enumerate the existing sources with an actual API but the
    # only stable interface is choco.exe source list and that does not output
    # the sources in an easily parsable list. Using -r will split each entry by
    # | like a psv but does not quote values that have a | already in it making
    # it inadequete for our tasks. Instead we will parse the chocolatey.config
    # file and get the values from there
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
    return ,$sources
}

Function New-ChocolateySource {
    param(
        $choco_app,
        $name,
        $source,
        $source_username,
        $source_password,
        $certificate,
        $certificate_password,
        $priority,
        $bypass_proxy,
        $allow_self_service,
        $admin_only
    )
    # build the base arguments
    $arguments = [System.Collections.ArrayList]@($choco_app.Path,
        "source", "add", "--name", $name, "--source", $source
    )

    # add optional arguments from user input
    if ($null -ne $source_username) {
        $arguments.Add("--user") > $null
        $arguments.Add($source_username) > $null
        $arguments.Add("--password") > $null
        $arguments.Add($source_password) > $null
    }
    if ($null -ne $certificate) {
        $arguments.Add("--cert") > $null
        $arguments.Add($certificate) > $null
    }
    if ($null -ne $certificate_password) {
        $arguments.Add("--certpassword") > $null
        $arguments.Add($certificate_password) > $null
    }
    if ($null -ne $priority) {
        $arguments.Add("--priority") > $null
        $arguments.Add($priority) > $null
    } else {
        $priority = 0
    }
    if ($bypass_proxy -eq $true) {
        $arguments.Add("--bypass-proxy") > $null
    } else {
        $bypass_proxy = $false
    }
    if ($allow_self_service -eq $true) {
        $arguments.Add("--allow-self-service") > $null
    } else {
        $allow_self_service = $false
    }
    if ($admin_only -eq $true) {
        $arguments.Add("--admin-only") > $null
    } else {
        $admin_only = $false
    }

    if ($check_mode) {
        $arguments.Add("--what-if") > $null
    }

    $command = Argv-ToString -arguments $arguments
    $res = Run-Command -command $command
    if ($res.rc -ne 0) {
        Fail-Json -obj $result -message "Failed to add Chocolatey source '$name': $($res.stderr)"
    }

    $source_info = @{
        name = $name
        source = $source
        disabled = $false
        source_username = $source_username
        priority = $priority
        certificate = $certificate
        bypass_proxy = $bypass_proxy
        allow_self_service = $allow_self_service
        admin_only = $admin_only
    }
    return ,$source_info
}

Function Remove-ChocolateySource {
    param(
        $choco_app,
        $name
    )
    $arguments = [System.Collections.ArrayList]@($choco_app.Path, "source", "remove", "--name", $name)
    if ($check_mode) {
        $arguments.Add("--what-if") > $null
    }
    $command = Argv-ToString -arguments $arguments
    $res = Run-Command -command $command
    if ($res.rc -ne 0) {
        Fail-Json -obj $result -message "Failed to remove Chocolatey source '$name': $($_.res.stderr)"
    }
}

$choco_app = Get-Command -Name choco.exe -CommandType Application -ErrorAction SilentlyContinue
if (-not $choco_app) {
    Fail-Json -obj $result -message "Failed to find Chocolatey installation, make sure choco.exe is in the PATH env value"
}
$actual_sources = Get-ChocolateySources -choco_app $choco_app
$actual_source = $actual_sources | Where-Object { $_.name -eq $name }
if ($diff) {
    if ($null -ne $actual_source) {
        $before = $actual_source.Clone()
    } else {
        $before = @{}
    }
    $result.diff.before = $before
}

if ($state -eq "absent" -and $null -ne $actual_source) {
    Remove-ChocolateySource -choco_app $choco_app -name $name
    $result.changed = $true
} elseif ($state -in ("disabled", "present")) {
    $change = $false
    if ($null -eq $actual_source) {
        if ($null -eq $source) {
            Fail-Json -obj $result -message "The source option must be set when creating a new source"
        }
        $change = $true
    } else {
        if ($null -ne $source -and $source -ne $actual_source.source) {
            $change = $true
        }
        if ($null -ne $source_username -and $source_username -ne $actual_source.source_username) {
            $change = $true
        }
        if ($null -ne $source_password -and $update_password -eq "always") {
            $change = $true
        }
        if ($null -ne $certificate -and $certificate -ne $actual_source.certificate) {
            $change = $true
        }
        if ($null -ne $certificate_password -and $update_password -eq "always") {
            $change = $true
        }
        if ($null -ne $priority -and $priority -ne $actual_source.priority) {
            $change = $true
        }
        if ($null -ne $bypass_proxy -and $bypass_proxy -ne $actual_source.bypass_proxy) {
            $change = $true
        }
        if ($null -ne $allow_self_service -and $allow_self_service -ne $actual_source.allow_self_service) {
            $change = $true
        }
        if ($null -ne $admin_only -and $admin_only -ne $actual_source.admin_only) {
            $change = $true
        }

        if ($change) {
            Remove-ChocolateySource -choco_app $choco_app -name $name
            $result.changed = $true
        }
    }

    if ($change) {
        $actual_source = New-ChocolateySource -choco_app $choco_app -name $name -source $source `
            -source_username $source_username -source_password $source_password `
            -certificate $certificate -certificate_password $certificate_password `
            -priority $priority -bypass_proxy $bypass_proxy -allow_self_service $allow_self_service `
            -admin_only $admin_only
        $result.changed = $true
    }

    # enable/disable the source if necessary
    $status_action = $null
    if ($state -ne "disabled" -and $actual_source.disabled) {
        $status_action = "enable"
    } elseif ($state -eq "disabled" -and (-not $actual_source.disabled)) {
        $status_action = "disable"
    }
    if ($null -ne $status_action) {
        $arguments = [System.Collections.ArrayList]@($choco_app.Path, "source", $status_action, "--name", $name)
        if ($check_mode) {
            $arguments.Add("--what-if") > $null
        }
        $command = Argv-ToString -arguments $arguments
        $res = Run-Command -command $command
        if ($res.rc -ne 0) {
            Fail-Json -obj $result -message "Failed to $status_action Chocolatey source '$name': $($res.stderr)"
        }
        $actual_source.disabled = ($status_action -eq "disable")
        $result.changed = $true
    }

    if ($diff) {
        $after = $actual_source
        $result.diff.after = $after
    }
}

# finally remove the diff if there was no change
if (-not $result.changed -and $diff) {
    $result.diff = @{}
}

Exit-Json -obj $result
