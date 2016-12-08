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

$timezone = Get-Attr -obj $params -name timezone -failifempty $true -resultobj $result

Try {
    # Get the current timezone set
    $currentTZ = $(tzutil.exe /g)
    If ($LASTEXITCODE -ne 0) { Throw "An error occured when getting the current machine's timezone setting." }

    If ( $currentTZ -eq $timezone ) {
        Exit-Json $result "$timezone is already set on this machine"
    }
    Else {
        $tzExists = $false
        #Check that timezone can even be set (if it is listed from tzutil as an available timezone to the machine)
        $tzList = $(tzutil.exe /l)
        If ($LASTEXITCODE -ne 0) { Throw "An error occured when listing the available timezones." }
        ForEach ($tz in $tzList) {
            If ( $tz -eq $timezone ) {
                $tzExists = $true
                break
            }
        }

        If ( $tzExists ) {
            tzutil.exe /s "$timezone"
            If ($LASTEXITCODE -ne 0) { Throw "An error occured when setting the specified timezone with tzutil." }
            $newTZ = $(tzutil.exe /g)
            If ($LASTEXITCODE -ne 0) { Throw "An error occured when getting the current machine's timezone setting." }

            If ( $timezone -eq $newTZ ) {
                $result.changed = $true
            }
        }
        Else {
            Fail-Json $result "The specified timezone: $timezone isn't supported on the machine."
        }
    }
}
Catch {
    Fail-Json $result "Error setting timezone to: $timezone."
}


Exit-Json $result;