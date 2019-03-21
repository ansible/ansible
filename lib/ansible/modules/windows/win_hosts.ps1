#!powershell

# Copyright: (c) 2018, Micah Hunsberger (@mhunsber)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"
$aliases = Get-AnsibleParam -obj $params -name "aliases" -type "list" -failifempty $false
$canonical_name = Get-AnsibleParam -obj $params -name "canonical_name" -type "str" -failifempty ($state -eq 'present')
$ip_address = Get-AnsibleParam -obj $params -name "ip_address" -type "str" -default "" -failifempty ($state -eq 'present')
$action = Get-AnsibleParam -obj $params -name "action" -type "str" -default "set" -validateset "add","remove","set"

$tmp = [ipaddress]::None
if($ip_address -and -not [ipaddress]::TryParse($ip_address, [ref]$tmp)){
    Fail-Json -obj @{} -message "win_hosts: Argument ip_address needs to be a valid ip address, but was $ip_address"
}
$ip_address_type = $tmp.AddressFamily

$hosts_file = Get-Item -LiteralPath "$env:SystemRoot\System32\drivers\etc\hosts"

$result = @{
    changed = $false
    diff = @{
        prepared = ""
    }
}

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
    $result.changed = $true
    $removed = $false

    if($diff_mode) {
        $result.diff.prepared += "`n-[$($list[$idx])]`n"
    }

    if(-not $check_mode) {
        $list.RemoveAt($idx)
        $removed = $true
    }

    return $removed
}

Function Add-HostEntry($list, $cname, $aliases, $ip) {
    $result.changed = $true
    $line = "$ip $cname $($aliases -join ' ')"
    if($diff_mode) {
        $result.diff.prepared += "`n+[$line]`n"
    }
    if(-not $check_mode) {
        $list.Add($line) | Out-Null
    }
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
                if($diff_mode){
                    $result.diff.prepared += "`n-[$($list[$idx])]`n"
                }
                if(-not $check_mode) {
                    $list.RemoveAt($idx)
                    $line_removed = $true
                }
                # we're done
                return @{
                    line_removed = $line_removed
                }
            }
        }
    }
    if($line -ne $list[$idx]){
        $result.changed = $true
        if($diff_mode) {
            $result.diff.prepared += "`n-[$($list[$idx])]`n+[$line]`n"
        }
        if(-not $check_mode) {
            $list[$idx] = $line
        }
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
        $result.changed = $true
        if($diff_mode) {
            $result.diff.prepared += "`n-[$($list[$idx])]`n+[$line]`n"
        }
        if(-not $check_mode) {
            $list[$idx] = $line
        }
    }
}

$hosts_lines = New-Object System.Collections.ArrayList

Get-Content -LiteralPath $hosts_file.FullName | ForEach-Object { $hosts_lines.Add($_) } | Out-Null

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
                        # don't need to worry about line being removed since canonical_name is present
                        $entry_idx = $idx

                        if($action -eq 'set') {
                            # remove the entry's aliases that are not in $aliases
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
                            # remove the entry
                            if (Remove-HostEntry -list $hosts_lines -idx $idx){
                                # keep index correct if we removed the line
                                $idx = $idx - 1
                            }
                            if ($action -ne "set") {
                                # keep old aliases intact
                                $aliases_to_keep += $entry_parts.aliases | Where-Object { ($aliases + $aliases_to_keep + $canonical_name) -notcontains $_ }
                            }
                        } elseif ($action -eq "remove") {
                            # just remove canonical_name. user may want alias(es) mapped to this canonical name
                            $aliases_to_remove = $canonical_name
                        } elseif ($aliases -contains $entry_parts.canonical_name) {
                            # remove the entry
                            if (Remove-HostEntry -list $hosts_lines -idx $idx) {
                                # keep index correct if we removed the line
                                $idx = $idx - 1
                            }
                            if ($action -eq "add") {
                                # keep old aliases intact
                                $aliases_to_keep += $entry_parts.aliases | Where-Object { ($aliases + $aliases_to_keep + $canonical_name) -notcontains $_ }
                            }
                        } else {
                            # ensure canonical_name and aliases removed from this entry
                            $aliases_to_remove = $aliases + $canonical_name
                        }
                    } else {
                        # Just ignore if the types don't match.
                        # TODO: Better ipv6 support. There is odd behavior for when an alias can be used for both ipv6 and ipv4
                    }
                }

                if($aliases_to_remove) {
                    if((Remove-HostnamesFromEntry -list $hosts_lines -idx $idx -aliases $aliases_to_remove).line_removed) {
                        # keep index correct if we removed the line
                        $idx = $idx - 1
                    }
                }
            }
        }
    }

    if($entry_idx -ge 0) {
        # we found the entry
        $aliases_to_add = @()
        $entry_parts = Get-HostEntryParts -line $hosts_lines[$entry_idx]
        if($action -eq 'remove') {
            # just preserve any previously removed aliases
            $aliases_to_add = $aliases_to_keep | Where-Object { $entry_parts.aliases -notcontains $_ }
        } else {
            # we want to add provided aliases and previously removed aliases that are not already in the list
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

if( $result.changed -and -not $check_mode ) {
    Set-Content -LiteralPath $hosts_file.FullName -Value $hosts_lines
}

Exit-Json $result
