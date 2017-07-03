#!powershell
# This file is part of Ansible
#
# Copyright 2015, Corwin Brown <corwin@corwinbrown.com>
# Copyright 2017, Dag Wieers <dag@wieers.com>
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
$safe_methods = @("GET", "HEAD")
$content_keys = @("Content", "Images", "InputFields", "Links", "RawContent")

Function ConvertTo-SnakeCase($input_string) {
    $snake_case = $input_string -csplit "(?<!^)(?=[A-Z])" -join "_"
    return $snake_case.ToLower()
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$url = Get-AnsibleParam -obj $params -name "url" -type "str" -failifempty $true
$method = Get-AnsibleParam -obj $params "method" -type "str" -default "GET" -validateset "CONNECT","DELETE","GET","HEAD","OPTIONS","PATCH","POST","PUT","REFRESH","TRACE"
$content_type = Get-AnsibleParam -obj $params -name "content_type" -type "str"
$headers = Get-AnsibleParam -obj $params -name "headers" -type="dict"
$body = Get-AnsibleParam -obj $params -name "body" -type "dict"
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path"

$user = Get-AnsibleParam -obj $params -name "user" -type "str"
$password = Get-AnsibleParam -obj $params -name "password" -type "str"

$creates = Get-AnsibleParam -obj $params -name "creates" -type "path"
$removes = Get-AnsibleParam -obj $params -name "removes" -type "path"

$follow_redirects = Get-AnsibleParam -obj $params -name "follow_redirects" -type "str" -default "safe" -validateset "all","none","safe"
$maximum_redirection = Get-AnsibleParam -obj $params -name "maximum_redirection" -type "int" -default 5
$return_content = Get-AnsibleParam -obj $params -name "return_content" -type "bool" -default $false
$status_code = Get-AnsibleParam -obj $params -name "status_code" -type "list" -default @(200)
$timeout = Get-AnsibleParam -obj $params -name "timeout" -type "int" -default 30
$use_basic_parsing = Get-AnsibleParam -obj $params -name "use_basic_parsing" -type "bool" -default $true
$validate_certs = Get-AnsibleParam -obj $params -name "validate_certs" -type "bool" -default $true
$client_cert = Get-AnsibleParam -obj $params -name "client_cert" -type "path"

if ($creates -and (Test-Path -Path $creates)) {
    $result.skipped = $true
    Exit-Json $result "The 'creates' file or directory ($creates) already exists."
}

if ($removes -and -not (Test-Path -Path $removes)) {
    $result.skipped = $true
    Exit-Json $result "The 'removes' file or directory ($removes) does not exist."
}

$result = @{
    changed = $false
    content_type = $content_type
    method = $method
    url = $url
    use_basic_parsing = $use_basic_parsing
}

# Disable redirection if requested
switch($follow_redirects) {
    "none" {
        $maximum_redirection = 0
    }
    "safe" {
        if ($safe_methods -notcontains $method) {
            $maximum_redirection = 0
        }
    }
}

$webrequest_opts = @{
    ContentType = $content_type
    ErrorAction = "SilentlyContinue"
    MaximumRedirection = $maximum_redirection
    Method = $method
    TimeoutSec = $timeout
    Uri = $url
    UseBasicParsing = $use_basic_parsing
}

if (-not $validate_certs) {
    $PSDefaultParameterValues.Add("Invoke-WebRequest:SkipCertificateCheck", $true)
}

if ($headers) {
    $req_headers = @{}
    ForEach ($header in $headers.psobject.properties) {
        $req_headers.Add($header.Name, $header.Value)
    }
    $webrequest_opts.Headers = $req_headers
}

if ($client_cert) {
    Try {
        $webrequest_opts.Certificate = Get-PfxCertificate -FilePath $client_cert
    } Catch {
        Fail-Json $result "Failed to read client certificate '$client_cert'"
    }
}

if ($body) {
    $webrequest_opts.Body = $body
    $result.body = $body
}

if ($dest -and -not $check_mode) {
    $webrequest_opts.OutFile = $dest
    $webrequest_opts.PassThru = $true
    $result.dest = $dest
}

if ($user -and $password) {
    $webrequest_opts.Credential = New-Object System.Management.Automation.PSCredential($user, $($password | ConvertTo-SecureString -AsPlainText -Force))
}

try {
    $response = Invoke-WebRequest @webrequest_opts
} catch {
    Fail-Json $result $_.Exception.Message
}

# TODO: When writing to a file, this is not idempotent !
# FIXME: Assume a change when we are writing to a file
# FIXME: Implement diff-mode
if ($dest) {
    $result.changed = $true
}

ForEach ($prop in $response.psobject.properties) {
    if ($content_keys -contains $prop.Name -and -not $return_content) {
        continue
    }
    $result_key = ConvertTo-SnakeCase $prop.Name
    $result.$result_key = $prop.Value
}

if ($status_code -notcontains $response.StatusCode) {
    Fail-Json $result "Status code of request '$($response.StatusCode)' is not in list of valid status codes $status_code."
}

Exit-Json $result
