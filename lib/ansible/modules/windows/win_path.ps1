#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

$system_path = "System\CurrentControlSet\Control\Session Manager\Environment"
$user_path = "Environment"

# list/arraylist methods don't allow IEqualityComparer override for case/backslash/quote-insensitivity, roll our own search
Function Get-IndexOfPathElement ($list, [string]$value) {
    $idx = 0
    $value = $value.Trim('"').Trim('\')
    ForEach($el in $list) {
        If ([string]$el.Trim('"').Trim('\') -ieq $value) {
            return $idx
        }

        $idx++
    }

    return -1
}

# alters list in place, returns true if at least one element was added
Function Add-Elements ($existing_elements, $elements_to_add) {
    $last_idx = -1
    $changed = $false

    ForEach($el in $elements_to_add) {
        $idx = Get-IndexOfPathElement $existing_elements $el

        # add missing elements at the end
        If ($idx -eq -1) {
            $last_idx = $existing_elements.Add($el)
            $changed = $true
        }
        ElseIf ($idx -lt $last_idx) {
            $existing_elements.RemoveAt($idx) | Out-Null
            $existing_elements.Add($el) | Out-Null
            $last_idx = $existing_elements.Count - 1
            $changed = $true
        }
        Else {
            $last_idx = $idx
        }
    }

    return $changed
}

# alters list in place, returns true if at least one element was removed
Function Remove-Elements ($existing_elements, $elements_to_remove) {
    $count = $existing_elements.Count

    ForEach($el in $elements_to_remove) {
        $idx = Get-IndexOfPathElement $existing_elements $el
        $result.removed_idx = $idx
        If ($idx -gt -1) {
            $existing_elements.RemoveAt($idx)
        }
    }

    return $count -ne $existing_elements.Count
}

# PS registry provider doesn't allow access to unexpanded REG_EXPAND_SZ; fall back to .NET
Function Get-RawPathVar ($scope) {
    If ($scope -eq "user") {
        $env_key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey($user_path)
    }
    ElseIf ($scope -eq "machine") {
        $env_key = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey($system_path)
    }

    return $env_key.GetValue($var_name, "", [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
}

Function Set-RawPathVar($path_value, $scope) {
    If ($scope -eq "user") {
        $var_path = "HKCU:\" + $user_path
    }
    ElseIf ($scope -eq "machine") {
        $var_path = "HKLM:\" + $system_path
    }

    Set-ItemProperty $var_path -Name $var_name -Value $path_value -Type ExpandString | Out-Null

    return $path_value
}

$parsed_args = Parse-Args $args -supports_check_mode $true

$result = @{changed=$false}

$var_name = Get-AnsibleParam $parsed_args "name" -Default "PATH"
$elements = Get-AnsibleParam $parsed_args "elements" -FailIfEmpty $result
$state = Get-AnsibleParam $parsed_args "state" -Default "present" -ValidateSet "present","absent"
$scope = Get-AnsibleParam $parsed_args "scope" -Default "machine" -ValidateSet "machine","user"

$check_mode = Get-AnsibleParam $parsed_args "_ansible_check_mode" -Default $false

If ($elements -is [string]) {
    $elements = @($elements)
}

If ($elements -isnot [Array]) {
    Fail-Json $result "elements must be a string or list of path strings"
}

$current_value = Get-RawPathVar $scope
$result.path_value = $current_value

# TODO: test case-canonicalization on wacky unicode values (eg turkish i)
# TODO: detect and warn/fail on unparseable path? (eg, unbalanced quotes, invalid path chars)
# TODO: detect and warn/fail if system path and Powershell isn't on it?

$existing_elements = New-Object System.Collections.ArrayList

# split on semicolons, accounting for quoted values with embedded semicolons (which may or may not be wrapped in whitespace)
$pathsplit_re = [regex] '((?<q>\s*"[^"]+"\s*)|(?<q>[^;]+))(;$|$|;)'

ForEach ($m in $pathsplit_re.Matches($current_value)) {
    $existing_elements.Add($m.Groups['q'].Value) | Out-Null
}

If ($state -eq "absent") {
    $result.changed = Remove-Elements $existing_elements $elements
}
ElseIf ($state -eq "present") {
    $result.changed = Add-Elements $existing_elements $elements
}

# calculate the new path value from the existing elements
$path_value = [String]::Join(";", $existing_elements.ToArray())
$result.path_value = $path_value

If ($result.changed -and -not $check_mode) {
    Set-RawPathVar $path_value $scope | Out-Null
}

Exit-Json $result
