#!powershell

# Copyright: (c) 2019, Hitachi ID Systems, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        name = @{ type = "str"; required = $true }
        state = @{ type = "str"; choices = "absent", "present"; default = "present" }
        ttl = @{ type = "int"; default = "3600" }
        type = @{ type = "str"; choices = "A","AAAA","CNAME","PTR"; required = $true }
        value = @{ type = "list"; elements = "str"; default = @() ; aliases=@( 'values' )}
        zone = @{ type = "str"; required = $true }
        computer_name = @{ type = "str" }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$name = $module.Params.name
$state = $module.Params.state
$ttl = $module.Params.ttl
$type = $module.Params.type
$values = $module.Params.value
$zone = $module.Params.zone
$dns_computer_name = $module.Params.computer_name


$extra_args = @{}
if ($null -ne $dns_computer_name) {
    $extra_args.ComputerName = $dns_computer_name
}

if ($state -eq 'present') {
    if ($values.Count -eq 0) {
        $module.FailJson("Parameter 'values' must be non-empty when state='present'")
    }
} else {
    if ($values.Count -ne 0) {
        $module.FailJson("Parameter 'values' must be undefined or empty when state='absent'")
    }
}


# TODO: add warning for forest minTTL override -- see https://docs.microsoft.com/en-us/windows/desktop/ad/configuration-of-ttl-limits
if ($ttl -lt 1 -or $ttl -gt 31557600) {
    $module.FailJson("Parameter 'ttl' must be between 1 and 31557600")
}
$ttl = New-TimeSpan -Seconds $ttl


if (($type -eq 'CNAME' -or $type -eq 'PTR') -and $null -ne $values -and $values.Count -gt 0 -and $zone[-1] -ne '.') {
    # CNAMEs and PTRs should be '.'-terminated, or record matching will fail
    $values = $values | ForEach-Object {
        if ($_ -Like "*.") { $_ } else { "$_." }
    }
}


$record_argument_name = @{
    A = "IPv4Address";
    AAAA = "IPv6Address";
    CNAME = "HostNameAlias";
    # MX = "MailExchange";
    # NS = "NameServer";
    PTR = "PtrDomainName";
    # TXT = "DescriptiveText"
}[$type]


$changes = @{
    before = "";
    after = ""
}


$records = Get-DnsServerResourceRecord -ZoneName $zone -Name $name -RRType $type -Node -ErrorAction:Ignore @extra_args | Sort-Object
if ($null -ne $records) {
    # We use [Hashtable]$required_values below as a set rather than a map.
    # It provides quick lookup to test existing DNS record against. By removing
    # items as each is processed, whatever remains at the end is missing
    # content (that needs to be added).
    $required_values = @{}
    foreach ($value in $values) {
        $required_values[$value.ToString()] = $null
    }

    foreach ($record in $records) {
        $record_value = $record.RecordData.$record_argument_name.ToString()

        if ($required_values.ContainsKey($record_value)) {
            # This record matches one of the values; but does it match the TTL?
            if ($record.TimeToLive -ne $ttl) {
                $new_record = $record.Clone()
                $new_record.TimeToLive = $ttl
                Set-DnsServerResourceRecord -ZoneName $zone -OldInputObject $record -NewInputObject $new_record -WhatIf:$module.CheckMode @extra_args

                $changes.before += "[$zone] $($record.HostName) $($record.TimeToLive.TotalSeconds) IN $type $record_value`n"
                $changes.after += "[$zone] $($record.HostName) $($ttl.TotalSeconds) IN $type $record_value`n"
                $module.Result.changed = $true
            }

            # Cross this one off the list, so we don't try adding it later
            $required_values.Remove($record_value)
        } else {
            # This record doesn't match any of the values, and must be removed
            $record | Remove-DnsServerResourceRecord -ZoneName $zone -Force -WhatIf:$module.CheckMode @extra_args

            $changes.before += "[$zone] $($record.HostName) $($record.TimeToLive.TotalSeconds) IN $type $record_value`n"
            $module.Result.changed = $true
        }
    }

    # Whatever is left in $required_values needs to be added
    $values = $required_values.Keys
}


if ($null -ne $values -and $values.Count -gt 0) {
    foreach ($value in $values) {
        $splat_args = @{ $type = $true; $record_argument_name = $value }
        $module.Result.debug_splat_args = $splat_args
        try {
            Add-DnsServerResourceRecord -ZoneName $zone -Name $name -AllowUpdateAny -TimeToLive $ttl @splat_args -WhatIf:$module.CheckMode @extra_args
        } catch {
            $module.FailJson("Error adding DNS $type resource $name in zone $zone with value $value", $_)
        }
        $changes.after += "[$zone] $name $($ttl.TotalSeconds) IN $type $value`n"
    }

    $module.Result.changed = $true
}

if ($module.CheckMode) {
    # Simulated changes
    $module.Diff.before = $changes.before
    $module.Diff.after = $changes.after
} else {
    # Real changes
    $records_end = Get-DnsServerResourceRecord -ZoneName $zone -Name $name -RRType $type -Node -ErrorAction:Ignore @extra_args | Sort-Object

    $module.Diff.before = @($records | ForEach-Object { "[$zone] $($_.HostName) $($_.TimeToLive.TotalSeconds) IN $type $($_.RecordData.$record_argument_name.ToString())`n" }) -join ''
    $module.Diff.after = @($records_end | ForEach-Object { "[$zone] $($_.HostName) $($_.TimeToLive.TotalSeconds) IN $type $($_.RecordData.$record_argument_name.ToString())`n" }) -join ''
}

$module.ExitJson()
