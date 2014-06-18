#!powershell
# This file is part of Ansible.
#
# Copyright 2014, Paul Durivage <paul.durivage@rackspace.com>
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
    win_get_url = New-Object psobject
    changed = $false
}

If ($params.url) {
    $url = $params.url
}
Else {
    Fail-Json $result "mising required argument: url"
}

If ($params.dest) {
    $dest = $params.dest
}
Else {
    Fail-Json $result "missing required argument: dest"
}

$client = New-Object System.Net.WebClient

Try {
    $client.DownloadFile($url, $dest)
    $result.changed = $true
}
Catch {
    Fail-Json $result "Error downloading $url to $dest"
}

Set-Attr $result.win_get_url "url" $url
Set-Attr $result.win_get_url "dest" $dest

Exit-Json $result;
