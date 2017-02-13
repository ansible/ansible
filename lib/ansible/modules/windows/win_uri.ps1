#!powershell
# This file is part of Ansible
#
# Copyright 2015, Corwin Brown <corwin@corwinbrown.com>
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

$ErrorActionPreference = "Stop"

# Functions ###############################################

Function ConvertTo-SnakeCase($input_string) {
    $snake_case = $input_string -csplit "(?<!^)(?=[A-Z])" -join "_"
    return $snake_case.ToLower()
}

# Build Arguments
$params = Parse-Args $args -supports_check_mode $true

$url = Get-AnsibleParam -obj $params -name "url" -type "str" -failifempty $true
$method = Get-AnsibleParam -obj $params "method" -type "str" -default "GET" -validateset "GET","POST","PUT","HEAD","DELETE","OPTIONS","PATCH","TRACE","CONNECT","REFRESH"
$content_type = Get-AnsibleParam -obj $params -name "content_type" -type "str"
# TODO: Why is this not a normal dictionary ?
$headers = Get-AnsibleParam -obj $params -name "headers" -type "str"
# TODO: Why is this not a normal dictionary ?
$body = Get-AnsibleParam -obj $params -name "body" -type "str"
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path"
$use_basic_parsing = Get-AnsibleParam -obj $params -name "use_basic_parsing" -type "bool" -default $true

$result = @{
    changed = $false
    win_uri = @{
        content_type = $content_type
        method = $method
        url = $url
        use_basic_parsing = $use_basic_parsing
    }
}

$webrequest_opts = @{
    ContentType = $content_type
    Method = $method
    Uri = $url
    UseBasicParsing = $use_basic_parsing
}

if ($headers -ne $null) {
    $req_headers = @{}
    ForEach ($header in $headers.psobject.properties) {
        $req_headers.Add($header.Name, $header.Value)
    }

    $webrequest_opts.Headers = $req_headers
}

if ($body -ne $null) {
    $webrequest_opts.Body = $body
    $result.win_uri.body = $body
}

if ($dest -ne $null) {
    $webrequest_opts.OutFile = $dest
    $result.win_uri.dest = $dest
}

# TODO: When writing to a file, this is not idempotent !
if ($check_mode -ne $true -or $dest -eq $null) {
    try {
        $response = Invoke-WebRequest @webrequest_opts
    } catch {
        Fail-Json $result $_.Exception.Message
    }
}

# Assume a change when we are writing to a file
if ($dest -ne $null) {
    $result.changed = $true
}

ForEach ($prop in $response.psobject.properties) {
    $result_key = ConvertTo-SnakeCase $prop.Name
    $result.$result_key = $prop.Value
}

Exit-Json $result
