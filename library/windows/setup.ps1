#!powershell
# This file is part of Ansible
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

$fact_path = "C:\ansible\facts.d"
If ($params.fact_path.GetType)
{
   $fact_path = $params.fact_path;
}

$filter = "*"
If ($params.filter.GetType)
{
    $filter = $params.filter;
}

$result = New-Object psobject @{
    ansible_facts = New-Object psobject
    changed = $false
};

If (Test-Path $fact_path)
{
    Get-ChildItem $fact_path -Filter *.fact | Foreach-Object
    {
        $facts = Get-Content $_ | ConvertFrom-Json
        # TODO: Need to concatentate this with $result
    }
}

$osversion = [Environment]::OSVersion

Set-Attr $result.ansible_facts "ansible_hostname" $env:COMPUTERNAME;
Set-Attr $result.ansible_facts "ansible_fqdn" "$([System.Net.Dns]::GetHostByName((hostname)).HostName)"
Set-Attr $result.ansible_facts "ansible_system" $osversion.Platform.ToString()
Set-Attr $result.ansible_facts "ansible_os_family" "Windows"
Set-Attr $result.ansible_facts "ansible_distribution" $osversion.VersionString
Set-Attr $result.ansible_facts "ansible_distribution_version" $osversion.Version.ToString()

# Need to figure out how to filter the code. Below is a start but not implemented
#If ($filter != "*")
#{
#    $filtered = New-Object psobject;
#    $result.psobject.properties | Where
#    {
#        $_.Name -like $filter | 
#    }
#}
#Else
#{
#    $filtered = $result;
#}

echo $result | ConvertTo-Json;
