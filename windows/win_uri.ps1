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

$params = Parse-Args $args;

$result = New-Object psobject @{
    win_uri = New-Object psobject
}

# Functions ###############################################

Function ConvertTo-SnakeCase($input_string) {
    $snake_case = $input_string -csplit "(?<!^)(?=[A-Z])" -join "_"
    $snake_case = $snake_case.ToLower()

    return $snake_case
}

# Build Arguments
$webrequest_opts = @{}

$url = Get-AnsibleParam -obj $params -name "url" -failifempty $true
$method = Get-AnsibleParam -obj $params "method" -default "GET"
$content_type = Get-AnsibleParam -obj $params -name "content_type"
$headers = Get-AnsibleParam -obj $params -name "headers"
$body = Get-AnsibleParam -obj $params -name "body"
$use_basic_parsing = ConvertTo-Bool (Get-AnsibleParam -obj $params -name "use_basic_parsing" -default $true)

$webrequest_opts.Uri = $url
Set-Attr $result.win_uri "url" $url

$webrequest_opts.Method = $method
Set-Attr $result.win_uri "method" $method

$webrequest_opts.ContentType = $content_type
Set-Attr $result.win_uri "content_type" $content_type

$webrequest_opts.UseBasicParsing = $use_basic_parsing
Set-Attr $result.win_uri "use_basic_parsing" $use_basic_parsing

if ($headers -ne $null) {
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
    $result_key = ConvertTo-SnakeCase $prop.Name
    $result_value = $prop.Value
    Set-Attr $result $result_key $result_value
}

Exit-Json $result
