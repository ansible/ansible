#!powershell

# Copyright: (c) 2015, Corwin Brown <corwin@corwinbrown.com>
# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.CamelConversion
#Requires -Module Ansible.ModuleUtils.FileUtil
#Requires -Module Ansible.ModuleUtils.Legacy

$spec = @{
    options = @{
        url = @{ type = "str"; required = $true }
        method = @{
            type = "str"
            default = "GET"
       }
       content_type = @{ type = "str" }
       headers = @{ type = "dict" }
       body = @{ type = "raw" }
       dest = @{ type = "path" }
       user = @{ type = "str" }
       password = @{ type = "str"; no_log = $true }
       force_basic_auth = @{ type = "bool"; default = $false }
       creates = @{ type = "path" }
       removes = @{ type = "path" }
       follow_redirects = @{
           type = "str"
           default = "safe"
           choices = "all", "none", "safe"
       }
       maximum_redirection = @{ type = "int"; default = 50 }
       return_content = @{ type = "bool"; default = $false }
       status_code = @{ type = "list"; elements = "int"; default = @(200) }
       timeout = @{ type = "int"; default = 30 }
       validate_certs = @{ type = "bool"; default = $true }
       client_cert = @{ type = "path" }
       client_cert_password = @{ type = "str"; no_log = $true }
    }
    supports_check_mode = $true
}
$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$url = $module.Params.url
$method = $module.Params.method.ToUpper()
$content_type = $module.Params.content_type
$headers = $module.Params.headers
$body = $module.Params.body
$dest = $module.Params.dest
$user = $module.Params.user
$password = $module.Params.password
$force_basic_auth = $module.Params.force_basic_auth
$creates = $module.Params.creates
$removes = $module.Params.removes
$follow_redirects = $module.Params.follow_redirects
$maximum_redirection = $module.Params.maximum_redirection
$return_content = $module.Params.return_content
$status_code = $module.Params.status_code
$timeout = $module.Params.timeout
$validate_certs = $module.Params.validate_certs
$client_cert = $module.Params.client_cert
$client_cert_password = $module.Params.client_cert_password

$JSON_CANDIDATES = @('text', 'json', 'javascript')

$module.Result.elapsed = 0
$module.Result.url = $url

if (-not ($method -cmatch '^[A-Z]+$')) {
    $module.FailJson("Parameter 'method' needs to be a single word in uppercase, like GET or POST.")
}

if ($creates -and (Test-AnsiblePath -Path $creates)) {
    $module.Result.skipped = $true
    $module.Result.msg = "The 'creates' file or directory ($creates) already exists."
    $module.ExitJson()
}

if ($removes -and -not (Test-AnsiblePath -Path $removes)) {
    $module.Result.skipped = $true
    $module.Result.msg = "The 'removes' file or directory ($removes) does not exist."
    $module.ExitJson()
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
        switch ($header.Key) {
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
            default { $req_headers.Add($header.Key, $header.Value) }
        }
    }
    $client.Headers.Add($req_headers)
}

if ($client_cert) {
    if (-not (Test-AnsiblePath -Path $client_cert)) {
        $module.FailJson("Client certificate '$client_cert' does not exit")
    }
    try {
        $certs = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Certificate2Collection -ArgumentList $client_cert, $client_cert_password
        $client.ClientCertificates = $certs
    } catch [System.Security.Cryptography.CryptographicException] {
        $module.FailJson("Failed to read client certificate '$client_cert': $($_.Exception.Message)", $_)
    } catch {
        $module.FailJson("Unhandled exception when reading client certificate at '$client_cert': $($_.Exception.Message)", $_)
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
    $module.Warn("Both 'user' and 'password' parameters are required together, skipping authentication")
}

if ($null -ne $body) {
    if ($body -is [System.Collections.IDictionary] -or $body -is [System.Collections.IList]) {
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

$module_start = Get-Date

try {
    $response = $client.GetResponse()
} catch [System.Net.WebException] {
    $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds
    $response = $null
    if ($_.Exception.PSObject.Properties.Name -match "Response") {
        # was a non-successful response but we at least have a response and
        # should parse it below according to module input
        $response = $_.Exception.Response
    }

    # in the case a response (or empty response) was on the exception like in
    # a timeout scenario, we should still fail
    if ($null -eq $response) {
        $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds
        $module.FailJson("WebException occurred when sending web request: $($_.Exception.Message)", $_)
    }
} catch [System.Net.ProtocolViolationException] {
    $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds
    $module.FailJson("ProtocolViolationException when sending web request: $($_.Exception.Message)", $_)
} catch {
    $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds
    $module.FailJson("Unhandled exception occured when sending web request. Exception: $($_.Exception.Message)", $_)
}
$module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds

ForEach ($prop in $response.psobject.properties) {
    $result_key = Convert-StringToSnakeCase -string $prop.Name
    $prop_value = $prop.Value
    # convert and DateTime values to ISO 8601 standard
    if ($prop_value -is [System.DateTime]) {
        $prop_value = $prop_value.ToString("o", [System.Globalization.CultureInfo]::InvariantCulture)
    }
    $module.Result.$result_key = $prop_value
}

# manually get the headers as not all of them are in the response properties
foreach ($header_key in $response.Headers.GetEnumerator()) {
    $header_value = $response.Headers[$header_key]
    $header_key = $header_key.Replace("-", "") # replace - with _ for snake conversion
    $header_key = Convert-StringToSnakeCase -string $header_key
    $module.Result.$header_key = $header_value
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
            $memory_st.Seek(0, [System.IO.SeekOrigin]::Begin) > $null
            $content_bytes = $memory_st.ToArray()
            $module.Result.content = [System.Text.Encoding]::UTF8.GetString($content_bytes)
            if ($module.Result.ContainsKey("content_type") -and $module.Result.content_type -Match ($JSON_CANDIDATES -join '|')) {
                try {
                    $module.Result.json = ([Ansible.Basic.AnsibleModule]::FromJson($module.Result.content))
                } catch [System.ArgumentException] {
                    # Simply continue, since 'text' might be anything
                }
            }
        }

        if ($dest) {
            $memory_st.Seek(0, [System.IO.SeekOrigin]::Begin) > $null
            $changed = $true

            if (Test-AnsiblePath -Path $dest) {
                $actual_checksum = Get-FileChecksum -path $dest -algorithm "sha1"

                $sp = New-Object -TypeName System.Security.Cryptography.SHA1CryptoServiceProvider
                $content_checksum = [System.BitConverter]::ToString($sp.ComputeHash($memory_st)).Replace("-", "").ToLower()

                if ($actual_checksum -eq $content_checksum) {
                    $changed = $false
                }
            }

            $module.Result.changed = $changed
            if ($changed -and (-not $module.CheckMode)) {
                $memory_st.Seek(0, [System.IO.SeekOrigin]::Begin) > $null
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
    $module.FailJson("Status code of request '$([int]$response.StatusCode)' is not in list of valid status codes $status_code : $($response.StatusCode)'.")
}

$module.ExitJson()
