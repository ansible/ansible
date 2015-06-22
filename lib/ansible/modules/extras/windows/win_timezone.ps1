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

$params = Parse-Args $args;

$result = New-Object psobject @{
    win_timezone = New-Object psobject
    changed = $false
}

If ($params.timezone) {
    Try {
        # Get the current timezone set
        $currentTZ = $(C:\Windows\System32\tzutil /g)

        If ( $currentTZ -eq $params.timezone ) {
            Exit-Json $result "$params.timezone is already set on this machine"
        }
        Else {
            $tzExists = $false
            #Check that timezone can even be set (if it is listed from tzutil as an available timezone to the machine)
            $tzList = $(C:\Windows\System32\tzutil /l)
            ForEach ($tz in $tzList) {
                If ( $tz -eq $params.timezone ) {
                    $tzExists = $true
                    break
                }
            }

            If ( $tzExists ) {
                C:\Windows\System32\tzutil /s "$params.timezone"
                $newTZ = $(C:\Windows\System32\tzutil /g)

                If ( $params.timezone -eq $newTZ ) {
                    $result.changed = $true
                }
            }
            Else {
                Fail-Json $result "The specified timezone: $params.timezone isn't supported on the machine."
            }
        }
    }
    Catch {
        Fail-Json $result "Error setting timezone to: $params.timezone."
    }
}
Else {
    Fail-Json $result "Parameter: timezone is required."
}


Exit-Json $result;