#!powershell

# Copyright: (c) 2015, Corwin Brown <corwin@corwinbrown.com>
# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.CamelConversion
#Requires -Module Ansible.ModuleUtils.FileUtil

$ErrorActionPreference = "Stop"

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$url = Get-AnsibleParam -obj $params -name "url" -type "str" -failifempty $true
$method = Get-AnsibleParam -obj $params "method" -type "str" -default "GET" -validateset "CONNECT","DELETE","GET","HEAD","MERGE","OPTIONS","PATCH","POST","PUT","REFRESH","TRACE"
$content_type = Get-AnsibleParam -obj $params -name "content_type" -type "str"
$headers = Get-AnsibleParam -obj $params -name "headers"
$body = Get-AnsibleParam -obj $params -name "body"
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path"

$user = Get-AnsibleParam -obj $params -name "user" -type "str"
$password = Get-AnsibleParam -obj $params -name "password" -type "str"
$force_basic_auth = Get-AnsibleParam -obj $params -name "force_basic_auth" -type "bool" -default $false

$creates = Get-AnsibleParam -obj $params -name "creates" -type "path"
$removes = Get-AnsibleParam -obj $params -name "removes" -type "path"

$follow_redirects = Get-AnsibleParam -obj $params -name "follow_redirects" -type "str" -default "safe" -validateset "all","none","safe"
$maximum_redirection = Get-AnsibleParam -obj $params -name "maximum_redirection" -type "int" -default 50
$return_content = Get-AnsibleParam -obj $params -name "return_content" -type "bool" -default $false
$status_code = Get-AnsibleParam -obj $params -name "status_code" -type "list" -default @(200)
$timeout = Get-AnsibleParam -obj $params -name "timeout" -type "int" -default 30
$validate_certs = Get-AnsibleParam -obj $params -name "validate_certs" -type "bool" -default $true
$client_cert = Get-AnsibleParam -obj $params -name "client_cert" -type "path"
$client_cert_password = Get-AnsibleParam -obj $params -name "client_cert_password" -type "str"

$result = @{
    changed = $false
    url = $url
}

if ($creates -and (Test-AnsiblePath -Path $creates)) {
    $result.skipped = $true
    Exit-Json -obj $result -message "The 'creates' file or directory ($creates) already exists."
}

if ($removes -and -not (Test-AnsiblePath -Path $removes)) {
    $result.skipped = $true
    Exit-Json -obj $result -message "The 'removes' file or directory ($removes) does not exist."
}

if ($status_code) {
    $status_code = foreach ($code in $status_code) {
        try {
            [int]$code
        }
        catch [System.InvalidCastException] {
            Fail-Json -obj $result -message "Failed to convert '$code' to an integer. Status codes must be provided in numeric format."
        }
    }
}

# Enable TLS1.1/TLS1.2 if they're available but disabled (eg. .NET 4.5)
$security_protocols = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::SystemDefault
if ([Net.SecurityProtocolType].GetMember("Tls11").Count -gt 0) {
    $security_protocols = $security_protocols -bor [Net.SecurityProtocolType]::Tls11
}
if ([Net.SecurityProtocolType].GetMember("Tls12").Count -gt 0) {
    $security_protocols = $security_protocols -bor [Net.SecurityProtocolType]::Tls12
}
[Net.ServicePointManager]::SecurityProtocol = $security_protocols

$client = [System.Net.WebRequest]::Create($url)
$client.Method = $method
$client.Timeout = $timeout * 1000

# Disable redirection if requested
switch($follow_redirects) {
    "none" {
        $client.AllowAutoRedirect = $false
    }
    "safe" {
        if (@("GET", "HEAD") -notcontains $method) {
            $client.AllowAutoRedirect = $false
        } else {
            $client.AllowAutoRedirect = $true
        }
    }
    default {
        $client.AllowAutoRedirect = $true
    }
}
if ($maximum_redirection -eq 0) {
    # 0 is not a valid option, need to disable redirection through AllowAutoRedirect
    $client.AllowAutoRedirect = $false
} else {
    $client.MaximumAutomaticRedirections = $maximum_redirection
}

if (-not $validate_certs) {
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
}

if ($null -ne $content_type) {
    $client.ContentType = $content_type
}

if ($headers) {
    $req_headers = New-Object -TypeName System.Net.WebHeaderCollection
    foreach ($header in $headers.GetEnumerator()) {
        # some headers need to be set on the property itself
        switch ($header.Name) {
            Accept { $client.Accept = $header.Value }
            Connection { $client.Connection = $header.Value }
            Content-Length { $client.ContentLength = $header.Value }
            Content-Type { $client.ContentType = $header.Value }
            Expect { $client.Expect = $header.Value }
            Date { $client.Date = $header.Value }
            Host { $client.Host = $header.Value }
            If-Modified-Since { $client.IfModifiedSince = $header.Value }
            Range { $client.AddRange($header.Value) }
            Referer { $client.Referer = $header.Value }
            Transfer-Encoding {
                $client.SendChunked = $true
                $client.TransferEncoding = $header.Value
            }
            User-Agent { $client.UserAgent = $header.Value }
            default { $req_headers.Add($header.Name, $header.Value) }
        }
    }
    $client.Headers.Add($req_headers)
}

if ($client_cert) {
    if (-not (Test-AnsiblePath -Path $client_cert)) {
        Fail-Json -obj $result -message "Client certificate '$client_cert' does not exist"
    }
    try {
        $certs = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Certificate2Collection -ArgumentList $client_cert, $client_cert_password
        $client.ClientCertificates = $certs
    } catch [System.Security.Cryptography.CryptographicException] {
        Fail-Json -obj $result -message "Failed to read client certificate '$client_cert': $($_.Exception.Message)"
    } catch {
        Fail-Json -obj $result -message "Unhandled exception when reading client certificate at '$client_cert': $($_.Exception.Message)"
    }
}

if ($user -and $password) {
    if ($force_basic_auth) {
        $basic_value = [Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes("$($user):$($password)"))
        $client.Headers.Add("Authorization", "Basic $basic_value")
    } else {
        $sec_password = ConvertTo-SecureString -String $password -AsPlainText -Force
        $credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $sec_password
        $client.Credentials = $credential
    }
} elseif ($user -or $password) {
    Add-Warning -obj $result -message "Both 'user' and 'password' parameters are required together, skipping authentication"
}

if ($null -ne $body) {
    if ($body -is [Hashtable]) {
        $body_string = ConvertTo-Json -InputObject $body -Compress
    } elseif ($body -isnot [String]) {
        $body_string = $body.ToString()
    } else {
        $body_string = $body
    }
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($body_string)

    $req_st = $client.GetRequestStream()
    try {
        $req_st.Write($buffer, 0, $buffer.Length)
    } finally {
        $req_st.Flush()
        $req_st.Close()
    }
}

try {
    $response = $client.GetResponse()
} catch [System.Net.WebException] {
    $response = $null
    if ($_.Exception.PSObject.Properties.Name -match "Response") {
        # was a non-successful response but we at least have a response and
        # should parse it below according to module input
        $response = $_.Exception.Response
    }

    # in the case a response (or empty response) was on the exception like in
    # a timeout scenario, we should still fail
    if ($null -eq $response) {
        Fail-Json -obj $result -message "WebException occurred when sending web request: $($_.Exception.Message)"
    }
} catch [System.Net.ProtocolViolationException] {
    Fail-Json -obj $result -message "ProtocolViolationException when sending web request: $($_.Exception.Message)"
} catch {
    Fail-Json -obj $result -message "Unhandled exception occured when sending web request. Exception: $($_.Exception.Message)"
}

ForEach ($prop in $response.psobject.properties) {
    $result_key = Convert-StringToSnakeCase -string $prop.Name
    $prop_value = $prop.Value
    # convert and DateTime values to ISO 8601 standard
    if ($prop_value -is [System.DateTime]) {
        $prop_value = $prop_value.ToString("o", [System.Globalization.CultureInfo]::InvariantCulture)
    }
    $result.$result_key = $prop_value
}

# manually get the headers as not all of them are in the response properties
foreach ($header_key in $response.Headers.GetEnumerator()) {
    $header_value = $response.Headers[$header_key]
    $header_key = $header_key.Replace("-", "") # replace - with _ for snake conversion
    $header_key = Convert-StringToSnakeCase -string $header_key
    $result.$header_key = $header_value
}

# we only care about the return body if we need to return the content or create a file
if ($return_content -or $dest) {
    $resp_st = $response.GetResponseStream()

    # copy to a MemoryStream so we can read it multiple times
    $memory_st = New-Object -TypeName System.IO.MemoryStream
    try {
        $resp_st.CopyTo($memory_st)
        $resp_st.Close()

        if ($return_content) {
            $memory_st.Seek(0, [System.IO.SeekOrigin]::Begin)
            $content_bytes = $memory_st.ToArray()
            $result.content = [System.Text.Encoding]::UTF8.GetString($content_bytes)
            if ($result.ContainsKey("content_type") -and $result.content_type -in @("application/json", "application/javascript")) {
                $result.json = ConvertFrom-Json -InputObject $result.content
            }
        }

        if ($dest) {
            $memory_st.Seek(0, [System.IO.SeekOrigin]::Begin)
            $changed = $true

            if (Test-AnsiblePath -Path $dest) {
                $actual_checksum = Get-FileChecksum -path $dest -algorithm "sha1"

                $sp = New-Object -TypeName System.Security.Cryptography.SHA1CryptoServiceProvider
                $content_checksum = [System.BitConverter]::ToString($sp.ComputeHash($memory_st)).Replace("-", "").ToLower()
    
                if ($actual_checksum -eq $content_checksum) {
                    $changed = $false
                }
            }

            $result.changed = $changed
            if ($changed -and (-not $check_mode)) {
                $memory_st.Seek(0, [System.IO.SeekOrigin]::Begin)
                $file_stream = [System.IO.File]::Create($dest)
                try {
                    $memory_st.CopyTo($file_stream)
                } finally {
                    $file_stream.Flush()
                    $file_stream.Close()
                }
            }
        }
    } finally {
        $memory_st.Close()
    }
}

if ($status_code -notcontains $response.StatusCode) {
    Fail-Json -obj $result -message "Status code of request '$([int]$response.StatusCode)' is not in list of valid status codes $status_code : '$($response.StatusCode)'."
}

Exit-Json -obj $result
