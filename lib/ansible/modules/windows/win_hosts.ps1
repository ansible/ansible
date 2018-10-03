#!powershell

#Requires -Module Ansible.ModuleUtils.Legacy
Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_mode = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$host_name = Get-AnsibleParam -obj $params -name "host_name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "absent","present"
$ip_address = Get-AnsibleParam -obj $params -name "ip_address" -type "str" -failifempty ($state -eq 'present')

# TODO: validate ip address?

$hosts_file = Get-Item -Path "$env:SystemRoot\System32\drivers\etc\hosts"

$result = @{
    changed = $false
}

Function Get-IndexOfHostEntry($list, [string]$value){
    $idx = 0
    
    # replace regex wildcard with literal
    $value = $value.Replace('.', "\.")

    ForEach($el in $list) {
        # skip comment lines
        if(!$el.Trim().StartsWith('#')) {
            
            # hostname may not match ip
            if($el -imatch "\s*(?<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(?<h>$value)"){
                return $idx
            }

        }

        $idx++
    }

    return -1
}

$host_name = $host_name.Trim()
$ip_address = $ip_address.Trim()

$hosts_lines = New-Object System.Collections.ArrayList

Get-Content -Path $hosts_file.FullName | ForEach-Object { $hosts_lines.Add($_) } | Out-Null

if($state -eq 'present'){

    $idx = Get-IndexOfHostEntry -list $hosts_lines -value $host_name

    if($idx -eq -1) {
        $result.changed = $true

        if(-not $check_mode){
            $hosts_lines.Add("$ip_address $host_name") | Out-Null
            Set-Content -Path $hosts_file -Value $hosts_lines
        }

        if($diff_mode) {
            $result.diff = @{
                prepared = "`n+[$ip_address $host_name]`n"
            }
        }

    } else {
        # determine if ip matches
        if($hosts_lines[$idx] -inotmatch "\s*$($ip_address.Replace('.',"\."))\s+$($host_name.Replace('.', "\."))"){
            $result.changed = $true
            
            if(-not $check_mode){
                $removed_line = $hosts_lines[$idx]
                $hosts_lines.RemoveAt($idx)
                $hosts_lines.Insert($idx, "$ip_address $host_name")
                Set-Content -Path $hosts_file -Value $hosts_lines
            }

            if($diff_mode) {
                $result.diff = @{
                    prepared = "`n-[$removed_line]`n+[$ip_address $host_name]`n"
                }
            }
        }

    }

} elseif ($state -eq 'absent') {

    if ($ip_address){
        Add-Warning -obj $result -message "When removing host entry '$host_name' it does not need an ip address '$ip_address' set"
    }

    $idx = Get-IndexOfHostEntry -list $hosts_lines -value $host_name

    if($idx -ne -1){

        $result.changed = $true
        $removed_line = $hosts_lines[$idx]

        if(-not $check_mode){
            $hosts_lines.RemoveAt($idx)
            Set-Content -Path $hosts_file -Value $hosts_lines
        }

        if($diff_mode) {
            $result.diff = @{
                prepared = "`n-[$removed_line]`n"
            }
        }
    }
}

Exit-Json $result
