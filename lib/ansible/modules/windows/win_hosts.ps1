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
$host_name = Get-AnsibleParam -obj $params -name "host_name" -type "str" -failifempty ($state -eq 'present')
$ip_address = Get-AnsibleParam -obj $params -name "ip_address" -type "str" -default "" -failifempty ($state -eq 'present')
$ip_action = Get-AnsibleParam -obj $params -name "ip_action" -type "str" -default "replace" -validateset "replace","add"

# TODO: validate ip address?

$hosts_file = Get-Item -Path "$env:SystemRoot\System32\drivers\etc\hosts"

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

Function Get-IpIndex($line, $ip) {
    $c_index = Get-CommentIndex -line $line
    $re = New-Object regex "\s*$($ip.Replace('.',"\."))\s"
    $match = $re.Match($line, 0, $c_index)
    if($match.Success) {
        return $match.Index
    } else {
        return -1
    }
}

Function Find-Hostname($line, $name) {
    $c_idx = Get-CommentIndex -line $line
    $re = New-Object regex ("\s+$($name.Replace('.',"\."))(\s|$)", [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $match = $re.Match($line, 0, $c_idx)
    return $match
}

Function Remove-HostEntry($list, [ref]$idx) {
    $result.changed = $true

    if($diff_mode) {
        $result.diff.prepared += "`n-[$($list[$idx.value])]`n"
    }

    if(-not $check_mode) {
        # don't skip any lines
        $list.RemoveAt($idx.value)
        $idx.value--
    }

}

Function Add-HostEntry($list, $name, $ip) {
    $result.changed = $true

    $line = "$ip $name"

    if($diff_mode) {
        $result.diff.prepared += "`n+[$line]`n"
    }

    if(-not $check_mode) {
        $list.Add($line) | Out-Null
    }
}

Function Remove-AliasFromEntry($list, [ref]$idx, $name) {
    $line = $list[$idx.value]

    $match = Find-Hostname -line $line -name $name

    if($match.Success){
        $result.changed = $true
    
        $line = $line.Remove($match.Index + 1, $match.Length -1)

        # was this the only alias? (check for space characters after trimming)
        if($line.Substring(0,(Get-CommentIndex -line $line)).Trim() -inotmatch "\s") {

            Remove-HostEntry -list $list -idx $idx

        } else {

            if($diff_mode) {
                $result.diff.prepared += "`n-[$($list[$idx.value])]`n+[$line]`n"
            }
    
            if(-not $check_mode) {
                $list[$idx.value] = $line
            }

        }
    }

}

Function Add-AliasToEntry($list, $idx, $name) {
    $line = $list[$idx]

    $match = Find-Hostname -line $line -name $name

    if(-not $match.Success) {
        $result.changed = $true

        # just add the alias before the comment
        $line = $line.Insert((Get-CommentIndex -line $line), " $name ")

        if($diff_mode) {
            $result.diff.prepared += "`n-[$($list[$idx])]`n+[$line]`n"
        }

        if(-not $check_mode) {
            $list[$idx] = $line
        }
    }
}

$hosts_lines = New-Object System.Collections.ArrayList

Get-Content -Path $hosts_file.FullName | ForEach-Object { $hosts_lines.Add($_) } | Out-Null

# go through and remove based on host and ips
if ($state -eq 'absent') {
    for($idx = 0; $idx -lt $hosts_lines.Count; $idx++) {
    
        $entry = $hosts_lines[$idx]
        # skip comment lines
        if(-not $entry.Trim().StartsWith('#')) {
        
            $ip_idx = Get-IpIndex -line $entry -ip $ip_address
            if($ip_idx -ge 0) {
                if ($host_name) {
                    Remove-AliasFromEntry -list $hosts_lines -idx ([ref]$idx) -name $host_name
                } else {
                    # only ips provided
                    Remove-HostEntry -list $hosts_lines -idx ([ref]$idx)
                }
            }
        }
    }
}
# go through lines, determine whether to add or remove based on ip_action
if($state -eq 'present') {
    # for adding later
    $entry_exists = $false
    $found_idx = -1

    for($idx = 0; $idx -lt $hosts_lines.Count; $idx++) {
    
        $entry = $hosts_lines[$idx]
        # skip comment lines
        if(-not $entry.Trim().StartsWith('#')) {

            if((Get-IpIndex -line $entry -ip $ip_address) -ge 0) {
                $found_idx = $idx
                if(-not $entry_exists) {
                    # find out if this is the one
                    if((Find-Hostname -line $entry -name $host_name).Success) {
                        $entry_exists = $true
                        if($ip_action -eq 'add') {
                            # we're done!
                            break
                        }
                    }
                }
            } elseif($ip_action -eq 'replace') {
                # this is not the ip we are looking for
                # remove the alias if it exists
                Remove-AliasFromEntry -list $hosts_lines -idx ([ref]$idx) -name $host_name
            }
        }
    }
    
    if(-not $entry_exists){
        if($found_idx -ge 0) {
            Add-AliasToEntry -list $hosts_lines -idx $found_idx -name $host_name
        } else {
            Add-HostEntry -list $hosts_lines -name $host_name -ip $ip_address
        }
    }
}

if( $result.changed ) {
    Set-Content -Path $hosts_file -Value $hosts_lines
}

Exit-Json $result
