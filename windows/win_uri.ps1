#!powershell
# This file is part of Ansible
#
# Copyright 2015, Corwin Brown <blakfeld@gmail.com>
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
    win_uri = New-Object psobject
}

# Build Arguments
$webrequest_opts = @{}
if (Get-Member -InputObject $params -Name url) {
    $url = $params.url.ToString()
    $webrequest_opts.Uri = $url
} else {
    Fail-Json $result "Missing required argument: url"
}

if (Get-Member -InputObject $params -Name method) {
    $method = $params.method.ToString()
    $webrequest_opts.Method = $method
}

if (Get-Member -InputObject $params -Name content_type) {
    $content_type = $params.method.content_type.ToString()
    $webrequest_opts.ContentType = $content_type
}

if (Get-Member -InputObject $params -Name body) {
    $body = $params.method.body.ToString()
    $webrequest_opts.Body = $body
}

if (Get-Member -InputObject $params -Name headers) {
    $headers = $params.headers
    Set-Attr $result.win_uri "headers" $headers

    $req_headers = @{}
    ForEach ($header in $headers.psobject.properties) {
        $req_headers.Add($header.Name, $header.Value)
    }

    $webrequest_opts.Headers = $req_headers
}

try {
    $response = Invoke-WebRequest @webrequest_opts
} catch {
    $ErrorMessage = $_.Exception.Message
    Fail-Json $result $ErrorMessage
}

ForEach ($prop in $response.psobject.properties) {
    Set-Attr $result $prop.Name $prop.Value
}

Exit-Json $result

