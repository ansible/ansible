#!powershell
# This file is part of Ansible
#
# Copyright 2015, Phil Schwartz <schwartzmx@gmail.com>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$diff_support = Get-AnsibleParam -obj $params -name "_ansible_diff" -type "bool" -default $false

$timezone = Get-AnsibleParam -obj $params -name "timezone" -type "str" -failifempty $true

$result = @{
    changed = $false
    previous_timezone = $timezone
    timezone = $timezone
}

Try {
    # Get the current timezone set
    $result.previous_timezone = $(tzutil.exe /g)
    If ($LASTEXITCODE -ne 0) {
        Throw "An error occurred when getting the current machine's timezone setting."
    }

    if ( $result.previous_timezone -eq $timezone ) {
        Exit-Json $result "Timezone '$timezone' is already set on this machine"
    } Else {
        # Check that timezone is listed as an available timezone to the machine
        $tzList = $(tzutil.exe /l)
        If ($LASTEXITCODE -ne 0) {
            Throw "An error occurred when listing the available timezones."
        }

        $tzExists = $false
        ForEach ($tz in $tzList) {
            If ( $tz -eq $timezone ) {
                $tzExists = $true
                break
            }
        }
        if (-not $tzExists) {
            Fail-Json $result "The specified timezone: $timezone isn't supported on the machine."
        }

        if ($check_mode) {
            $result.changed = $true
        } else {
            tzutil.exe /s "$timezone"
            if ($LASTEXITCODE -ne 0) {
                Throw "An error occurred when setting the specified timezone with tzutil."
            }

            $new_timezone = $(tzutil.exe /g)
            if ($LASTEXITCODE -ne 0) {
                Throw "An error occurred when getting the current machine's timezone setting."
            }

            if ($timezone -eq $new_timezone) {
                $result.changed = $true
            }
        }

        if ($diff_support) {
            $result.diff = @{
                before = "$($result.previous_timezone)`n"
                after = "$timezone`n"
            }
        }
    }
} Catch {
    Fail-Json $result "Error setting timezone to: $timezone."
}

Exit-Json $result
