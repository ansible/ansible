#!powershell
# This file is part of Ansible
#
# Copyright 2014, Chris Hoffman <choffman@chathamfinancial.com>
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
    win_service_status = New-Object psobject
    changed = $false
}

$name = Get-AnsibleParam $params "name" -failifempty $true -resultobj $result

Try
{
    $svc = Get-WmiObject -Class Win32_Service -Filter "Name='$($name)'"    
    
    if ([string]::IsNullOrEmpty($svc))
    {
        # service doesn't exist
        Set-Attr $result.win_service_status "exists" $false
    }
    else
    {
        # service exists
        Set-Attr $result.win_service_status "exists" $true
        Set-Attr $result.win_service_status "name" $svc.name.toString()
        Set-Attr $result.win_service_status "start_mode" $svc.StartMode.toString()
        Set-Attr $result.win_service_status "caption" $svc.Caption.toString()
        Set-Attr $result.win_service_status "state" $svc.State.toString()
        Set-Attr $result.win_service_status "path_name" $svc.PathName.toString()
        Set-Attr $result.win_service_status "start_name" $svc.StartName.toString()
    }
}
Catch
{
    Fail-Json $result "Error: $_.Exception.Message"
}

Exit-Json $result;
