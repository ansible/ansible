#!powershell
# This file is part of Ansible

# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil
#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

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
$source = Get-AnsibleParam -obj $params -name "source" -type "str" -failifempty ($state -ne "absent")
$source_username = Get-AnsibleParam -obj $params -name "source_username" -type "str"
$source_password = Get-AnsibleParam -obj $params -name "source_password" -type "str" -failifempty ($null -ne $source_username)
$update_password = Get-AnsibleParam -obj $params -name "update_password" -type "str" -default "always" -validateset "always", "on_create"

$result = @{
    changed = $false
}
if ($diff) {
    $result.diff = @{
        before = $null
        after = $null
    }
}

Function Get-PrettyXml {
    param([xml]$xml)

    $string_writer = New-Object -TypeName System.IO.StringWriter
    $xml_writer = New-Object -TypeName System.Xml.XmlTextWriter $string_writer
    $xml_writer.Formatting = "indented"
    $xml_writer.Indentation = 2
    $xml.WriteContentTo($xml_writer)
    $xml_writer.Flush()
    $string_writer.Flush()

    return $string_writer.ToString()
}

Function Get-ChocolateySources {
    param($choco_app)

    $choco_config_path = "$(Split-Path -Path (Split-Path -Path $choco_app.Path))\config\chocolatey.config"
    if (-not (Test-Path -Path $choco_config_path)) {
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
        $source_password = $xml_source.Attributes.GetNamedItem("password")
        if ($null -ne $source_password) {
            $source_password = $source_password.Value
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
        $certificate_password = $xml_source.Attributes.GetNamedItem("certificatePassword")
        if ($null -ne $certificate_password) {
            $certificate_password = $certificate_password.Value
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

            source_password = $source_password
            certificate_password = $certificate_password
        }
        $sources.Add($source_info) > $null
    }
    return ,$sources
}

Function Set-RawChocolateySourceAttribute {
    param(
        $choco_app,
        $name,
        $attribute,
        $value
    )
    # for private attributes like password/certificatePassword, the only way
    # for us to preserve the existing value when changing another attirbute is
    # to store it manually by editing the XML
    $choco_config_path = "$(Split-Path -Path (Split-Path -Path $choco_app.Path))\config\chocolatey.config"
    if (-not (Test-Path -Path $choco_config_path)) {
        Fail-Json -obj $result -message "Expecting Chocolatey config file to exist at '$choco_config_path'"
    }

    try {
        [xml]$choco_config = Get-Content -Path $choco_config_path
    } catch {
        Fail-Json -obj $result -message "Failed to parse Chocolatey config file at '$choco_config_path': $($_.Exception.Message)"
    }
    $source = $choco_config.chocolatey.sources.GetEnumerator() | Where-Object { $_.id -eq $name }
    $source.$attribute = $value
    $new_xml = Get-PrettyXml -xml $choco_config
    if (-not $check_mode) {
        [System.IO.File]::WriteAllText($choco_config_path, $new_xml)
    }
}

Function New-ChocolateySource {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingUserNameAndPassWordParams", "", Justification="We need to use the plaintext pass in the cmdline, also using a SecureString here doesn't make sense considering the source is not secure")]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidUsingPlainTextForPassword", "", Justification="See above")]
    param(
        $choco_app,
        $name,
        $source,
        $source_username,
        $source_password,
        [switch]$encrypted_source_password,
        $certificate,
        $certificate_password,
        [switch]$encrypted_certificate_password,
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
        if ($encrypted_source_password) {
            # use a placeholder for now
            $arguments.Add("pass") > $null
        } else {
            $arguments.Add($source_password) > $null
        }
    }
    if ($null -ne $certificate) {
        $arguments.Add("--cert") > $null
        $arguments.Add($certificate) > $null
    }
    if ($null -ne $certificate_password) {
        $arguments.Add("--certpassword") > $null
        if ($encrypted_certificate_password) {
            # use a placeholder for now
            $arguments.Add("pass") > $null
        } else {
            $arguments.Add($certificate_password) > $null
        }
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
        Fail-Json -obj $result -message "Failed to add Chocolatey source '$name': $($_.stderr)"
    }
    if ($encrypted_source_password -and $null -ne $source_password) {
        Set-RawChocolateySourceAttribute -choco_app $choco_app -name $name -attribute password -value $source_password
    }
    if ($encrypted_certificate_password -and $null -ne $certificate_password) {
        Set-RawChocolateySourceAttribute -choco_app $choco_app -name $name -attribute certificatePassword -value $certificate_password
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
    $before = $actual_source.Clone()
    # remove the secret info for the diff output (while these are encrypted) we
    # are best not to return them
    $before.Remove("source_password")
    $before.Remove("certificate_password")
    $result.diff.before = $before
}

if ($state -eq "absent" -and $null -ne $actual_source) {
    Remove-ChocolateySource -choco_app $choco_app -name $name
    $result.changed = $true
} elseif ($state -in ("disabled", "present")) {
    if ($null -eq $actual_source) {
        $actual_source = New-ChocolateySource -choco_app $choco_app -name $name -source $source `
            -source_username $source_username -source_password $source_password `
            -encrypted_source_password:$false -certificate $certificate `
            -certificate_password $certificate_password -encrypted_certificate_password:$false `
            -priority $priority -bypass_proxy $bypass_proxy -allow_self_service $allow_self_service `
            -admin_only $admin_only
        $result.changed = $true
    } else {
        $change = $false

        # start with baseline that copies the existing source definition
        $new_args = $actual_source.Clone()
        $new_args.choco_app = $choco_app
        $new_args.encrypted_source_password = $true
        $new_args.encrypted_certificate_password = $true

        if ($source -ne $new_args.source) {
            $change = $true
            $new_args.source = $source
        }
        if ($null -ne $source_username -and $source_username -ne $new_args.source_username) {
            $change = $true
            $new_args.source_username = $source_username
        }
        if ($null -ne $source_password) {
            $new_args.source_password = $source_password
            $new_args.encrypted_source_password = $false
            if ($update_password -eq "always") {
                $change = $true
            }
        }
        if ($null -ne $certificate -and $certificate -ne $new_args.certificate) {
            $change = $true
            $new_args.certificate = $certificate
        }
        if ($null -ne $certificate_password) {
            $new_args.certificate_password = $certificate_password
            $new_args.encrypted_certificate_password = $false
            if ($update_password -eq "always") {
                $change = $true
            }
        }
        if ($null -ne $priority -and $priority -ne $new_args.priority) {
            $change = $true
            $new_args.priority = $priority
        }
        if ($null -ne $bypass_proxy -and $bypass_proxy -ne $new_args.bypass_proxy) {
            $change = $true
            $new_args.bypass_proxy = $bypass_proxy
        }
        if ($null -ne $allow_self_service -and $allow_self_service -ne $new_args.allow_self_service) {
            $change = $true
            $new_args.allow_self_service = $allow_self_service
        }
        if ($null -ne $admin_only -and $admin_only -ne $new_args.admin_only) {
            $change = $true
            $new_args.admin_only = $admin_only
        }

        if ($change) {
            Remove-ChocolateySource -choco_app $choco_app -name $name
            $actual_source = New-ChocolateySource @new_args
            $result.changed = $true
        }
    }

    # enable/disable the source if necessary
    if ($state -ne "disabled" -and $actual_source.disabled) {
        $arguments = [System.Collections.ArrayList]@($choco_app.Path, "source", "enable", "--name", $name)
        if ($check_mode) {
            $arguments.Add("--what-if") > $null
        }
        $command = Argv-ToString -arguments $arguments
        $res = Run-Command -command $command
        if ($res.rc -ne 0) {
            Fail-Json -obj $result -message "Failed to enable Chocolatey source '$name': $($_.res.stderr)"
        }
        $actual_source.disabled = $false
        $result.changed = $true
    } elseif ($state -eq "disabled" -and (-not $actual_source.disabled)) {
        $arguments = [System.Collections.ArrayList]@($choco_app.Path, "source", "disable", "--name", $name)
        if ($check_mode) {
            $arguments.Add("--what-if") > $null
        }
        $command = Argv-ToString -arguments $arguments
        $res = Run-Command -command $command
        if ($res.rc -ne 0) {
            Fail-Json -obj $result -message "Failed to disable Chocolatey source '$name': $($_.res.stderr)"
        }
        $actual_source.disabled = $true
        $result.changed = $true
    }

    if ($diff) {
        $after = $actual_source
        $after.Remove("source_password")
        $after.Remove("certificate_password")
        $result.diff.after = $after
    }
}

# finally remove the diff if there was no change
if (-not $result.changed -and $diff) {
    $result.diff = $null
}

Exit-Json -obj $result
