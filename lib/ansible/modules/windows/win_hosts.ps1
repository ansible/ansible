#!powershell

# Copyright: (c) 2018, Micah Hunsberger (@mhunsber)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

$spec = @{
    options = @{
        state = @{ type = "str"; choices = "absent", "present"; default = "present" }
        aliases = @{ type = "list"; elements = "str" }
        canonical_name = @{ type = "str" }
        ip_address = @{ type = "str" }
        action = @{ type = "str"; choices = "add", "remove", "set"; default = "set" }
    }
    required_if = @(,@( "state", "present", @("canonical_name", "ip_address")))
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$state = $module.Params.state
$aliases = $module.Params.aliases
$canonical_name = $module.Params.canonical_name
$ip_address = $module.Params.ip_address
$action = $module.Params.action

$tmp = [ipaddress]::None
if($ip_address -and -not [ipaddress]::TryParse($ip_address, [ref]$tmp)){
    $module.FailJson("win_hosts: Argument ip_address needs to be a valid ip address, but was $ip_address")
}
$ip_address_type = $tmp.AddressFamily

$hosts_file = Get-Item -LiteralPath "$env:SystemRoot\System32\drivers\etc\hosts"

Function Get-CommentIndex($line) {
    $c_index = $line.IndexOf('#')
    if($c_index -lt 0) {
        $c_index = $line.Length
    }
    return $c_index
}

Function Get-HostEntryParts($line) {
    $success = $true
    $c_index = Get-CommentIndex -line $line
    $pure_line = $line.Substring(0,$c_index).Trim()
    $bits = $pure_line -split "\s+"
    if($bits.Length -lt 2){
        return @{
            success = $false
            ip_address = ""
            ip_type = ""
            canonical_name = ""
            aliases = @()
        }
    }
    $ip_obj = [ipaddress]::None
    if(-not [ipaddress]::TryParse($bits[0], [ref]$ip_obj) ){
        $success = $false
    }
    $cname = $bits[1]
    $als = New-Object string[] ($bits.Length - 2)
    [array]::Copy($bits, 2, $als, 0, $als.Length)
    return @{
        success = $success
        ip_address = $ip_obj.IPAddressToString
        ip_type = $ip_obj.AddressFamily
        canonical_name = $cname
        aliases = $als
    }
}

Function Find-HostName($line, $name) {
    $c_idx = Get-CommentIndex -line $line
    $re = New-Object regex ("\s+$($name.Replace('.',"\."))(\s|$)", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $match = $re.Match($line, 0, $c_idx)
    return $match
}

Function Remove-HostEntry($list, $idx) {
    $module.Result.changed = $true
    $list.RemoveAt($idx)
}

Function Add-HostEntry($list, $cname, $aliases, $ip) {
    $module.Result.changed = $true
    $line = "$ip $cname $($aliases -join ' ')"
    $list.Add($line) | Out-Null
}

Function Remove-HostnamesFromEntry($list, $idx, $aliases) {
    $line = $list[$idx]
    $line_removed = $false

    foreach($name in $aliases){
        $match = Find-HostName -line $line -name $name
        if($match.Success){
            $line = $line.Remove($match.Index + 1, $match.Length -1)
            # was this the last alias? (check for space characters after trimming)
            if($line.Substring(0,(Get-CommentIndex -line $line)).Trim() -inotmatch "\s") {
                $list.RemoveAt($idx)
                $line_removed = $true
                # we're done
                return @{
                    line_removed = $line_removed
                }
            }
        }
    }
    if($line -ne $list[$idx]){
        $module.Result.changed = $true
        $list[$idx] = $line
    }
    return @{
        line_removed = $line_removed
    }
}

Function Add-AliasesToEntry($list, $idx, $aliases) {
    $line = $list[$idx]
    foreach($name in $aliases){
        $match = Find-HostName -line $line -name $name
        if(-not $match.Success) {
            # just add the alias before the comment
            $line = $line.Insert((Get-CommentIndex -line $line), " $name ")
        }
    }
    if($line -ne $list[$idx]){
        $module.Result.changed = $true
        $list[$idx] = $line
    }
}

$hosts_lines = New-Object System.Collections.ArrayList

Get-Content -LiteralPath $hosts_file.FullName | ForEach-Object { $hosts_lines.Add($_) } | Out-Null
$module.Diff.before = ($hosts_lines -join "`n") + "`n"

if ($state -eq 'absent') {
    # go through and remove canonical_name and ip
    for($idx = 0; $idx -lt $hosts_lines.Count; $idx++) {
        $entry = $hosts_lines[$idx]
         # skip comment lines
         if(-not $entry.Trim().StartsWith('#')) {
            $entry_parts = Get-HostEntryParts -line $entry
            if($entry_parts.success) {
                if(-not $ip_address -or $entry_parts.ip_address -eq $ip_address) {
                    if(-not $canonical_name -or $entry_parts.canonical_name -eq $canonical_name) {
                        if(Remove-HostEntry -list $hosts_lines -idx $idx){
                            # keep index correct if we removed the line
                            $idx = $idx - 1
                        }
                    }
                }
            }
        }
    }
}
if($state -eq 'present') {
    $entry_idx = -1
    $aliases_to_keep = @()
    # go through lines, find the entry and determine what to remove based on action
    for($idx = 0; $idx -lt $hosts_lines.Count; $idx++) {
        $entry = $hosts_lines[$idx]
         # skip comment lines
         if(-not $entry.Trim().StartsWith('#')) {
            $entry_parts = Get-HostEntryParts -line $entry
            if($entry_parts.success) {
                $aliases_to_remove = @()
                if($entry_parts.ip_address -eq $ip_address) {
                    if($entry_parts.canonical_name -eq $canonical_name) {
                        $entry_idx = $idx

                        if($action -eq 'set') {
                            $aliases_to_remove = $entry_parts.aliases | Where-Object { $aliases -notcontains $_ }
                        } elseif($action -eq 'remove') {
                            $aliases_to_remove = $aliases
                        }
                    } else {
                        # this is the right ip_address, but not the cname we were looking for.
                        # we need to make sure none of aliases or canonical_name exist for this entry
                        # since the given canonical_name should be an A/AAAA record,
                        # and aliases should be cname records for the canonical_name.
                        $aliases_to_remove = $aliases + $canonical_name
                    }
                } else {
                    # this is not the ip_address we are looking for
                    if ($ip_address_type -eq $entry_parts.ip_type) {
                        if ($entry_parts.canonical_name -eq $canonical_name) {
                            Remove-HostEntry -list $hosts_lines -idx $idx
                            $idx = $idx - 1
                            if ($action -ne "set") {
                                # keep old aliases intact
                                $aliases_to_keep += $entry_parts.aliases | Where-Object { ($aliases + $aliases_to_keep + $canonical_name) -notcontains $_ }
                            }
                        } elseif ($action -eq "remove") {
                            $aliases_to_remove = $canonical_name
                        } elseif ($aliases -contains $entry_parts.canonical_name) {
                            Remove-HostEntry -list $hosts_lines -idx $idx
                            $idx = $idx - 1
                            if ($action -eq "add") {
                                # keep old aliases intact
                                $aliases_to_keep += $entry_parts.aliases | Where-Object { ($aliases + $aliases_to_keep + $canonical_name) -notcontains $_ }
                            }
                        } else {
                            $aliases_to_remove = $aliases + $canonical_name
                        }
                    } else {
                        # TODO: Better ipv6 support. There is odd behavior for when an alias can be used for both ipv6 and ipv4
                    }
                }

                if($aliases_to_remove) {
                    if((Remove-HostnamesFromEntry -list $hosts_lines -idx $idx -aliases $aliases_to_remove).line_removed) {
                        $idx = $idx - 1
                    }
                }
            }
        }
    }

    if($entry_idx -ge 0) {
        $aliases_to_add = @()
        $entry_parts = Get-HostEntryParts -line $hosts_lines[$entry_idx]
        if($action -eq 'remove') {
            $aliases_to_add = $aliases_to_keep | Where-Object { $entry_parts.aliases -notcontains $_ }
        } else {
            $aliases_to_add = ($aliases + $aliases_to_keep) | Where-Object { $entry_parts.aliases -notcontains $_ }
        }

        if($aliases_to_add) {
            Add-AliasesToEntry -list $hosts_lines -idx $entry_idx -aliases $aliases_to_add
        }
    } else {
        # add the entry at the end
        if($action -eq 'remove') {
            if($aliases_to_keep) {
                Add-HostEntry -list $hosts_lines -ip $ip_address -cname $canonical_name -aliases $aliases_to_keep
            } else {
                Add-HostEntry -list $hosts_lines -ip $ip_address -cname $canonical_name
            }
        } else {
            Add-HostEntry -list $hosts_lines -ip $ip_address -cname $canonical_name -aliases ($aliases + $aliases_to_keep)
        }
    }
}

$module.Diff.after = ($hosts_lines -join "`n") + "`n"
if( $module.Result.changed -and -not $module.CheckMode ) {
    Set-Content -LiteralPath $hosts_file.FullName -Value $hosts_lines
}

$module.ExitJson()
