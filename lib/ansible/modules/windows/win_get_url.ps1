#!powershell

# Copyright: (c) 2015, Paul Durivage <paul.durivage@rackspace.com>
# Copyright: (c) 2015, Tal Auslander <tal@cloudshare.com>
# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = 'Stop'

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false
$_remote_tmp = Get-AnsibleParam $params "_ansible_remote_tmp" -type "path" -default $env:TMP

$webclient_util = @"
    using System.Net;
    public class ExtendedWebClient : WebClient {
        public int Timeout;

        public ExtendedWebClient() {
            Timeout = 600000; // Default timeout value
        }

        protected override WebRequest GetWebRequest(System.Uri address) {
            WebRequest request = base.GetWebRequest(address);
            request.Timeout = Timeout;
            return request;
        }
    }
"@
$original_tmp = $env:TMP
$env:TMP = $_remote_tmp
Add-Type -TypeDefinition $webclient_util
$env:TMP = $original_tmp


Function CheckModified-File($url, $dest, $headers, $credentials, $timeout, $use_proxy, $proxy) {

    $fileLastMod = ([System.IO.FileInfo]$dest).LastWriteTimeUtc
    $webLastMod = $null

    $webRequest = [System.Net.WebRequest]::Create($url)
    
    foreach ($header in $headers.GetEnumerator()) {
        $webRequest.Headers.Add($header.Name, $header.Value)
    }

    if ($timeout) {
        $webRequest.Timeout = $timeout * 1000
    }

    if (-not $use_proxy) {
        # Ignore the system proxy settings
        $webRequest.Proxy = $null
    } elseif ($proxy) {
        $webRequest.Proxy = $proxy
    }

    if ($credentials) {
        if ($force_basic_auth) {
            $webRequest.Headers.Add("Authorization", "Basic $credentials")
        } else {
            $webRequest.Credentials = $credentials
        }
    }

    if ($webRequest -is [System.Net.FtpWebRequest]) {
        $webRequest.Method = [System.Net.WebRequestMethods+Ftp]::GetDateTimestamp
    } else {
        $webRequest.Method = [System.Net.WebRequestMethods+Http]::Head
    }
    
    Try {
        $webResponse = $webRequest.GetResponse()

        $webLastMod = $webResponse.LastModified
    } Catch [System.Net.WebException] {
        $result.status_code = $_.Exception.Response.StatusCode
        Fail-Json -obj $result -message "Error requesting '$url'. $($_.Exception.Message)"
    } Catch {
        Fail-Json -obj $result -message "Error when requesting 'Last-Modified' date from '$url'. $($_.Exception.Message)"
    }
    $result.status_code = [int] $webResponse.StatusCode
    $result.msg = $webResponse.StatusDescription
    $webResponse.Close()

    if ($webLastMod -and ((Get-Date -Date $webLastMod).ToUniversalTime() -lt $fileLastMod)) {
        return $false
    } else {
        return $true
    }
}


Function Download-File($result, $url, $dest, $headers, $credentials, $timeout, $use_proxy, $proxy, $whatif) {

    # Check $dest parent folder exists before attempting download, which avoids unhelpful generic error message.
    $dest_parent = Split-Path -LiteralPath $dest
    if (-not (Test-Path -LiteralPath $dest_parent -PathType Container)) {
        Fail-Json -obj $result -message "The path '$dest_parent' does not exist for destination '$dest', or is not visible to the current user.  Ensure download destination folder exists (perhaps using win_file state=directory) before win_get_url runs."
    }

    # TODO: Replace this with WebRequest
    $extWebClient = New-Object ExtendedWebClient

    foreach ($header in $headers.GetEnumerator()) {
        $extWebClient.Headers.Add($header.Name, $header.Value)
    }

    if ($timeout) {
        $extWebClient.Timeout = $timeout * 1000
    }

    if (-not $use_proxy) {
        # Ignore the system proxy settings
        $extWebClient.Proxy = $null
    } elseif ($proxy) {
        $extWebClient.Proxy = $proxy
    }

    if ($credentials) {
        if ($force_basic_auth) {
            $extWebClient.Headers.Add("Authorization","Basic $credentials")
        } else {
            $extWebClient.Credentials = $credentials
        }
    }

    if (-not $whatif) {
        Try {
            $extWebClient.DownloadFile($url, $dest)
        } Catch [System.Net.WebException] {
            $result.status_code = [int] $_.Exception.Response.StatusCode
            Fail-Json -obj $result -message "Error downloading '$url' to '$dest': $($_.Exception.Message)"
        } Catch {
            Fail-Json -obj $result -message "Unknown error downloading '$url' to '$dest': $($_.Exception.Message)"
        }
    }

    $result.status_code = 200
    $result.changed = $true
    $result.msg = 'OK'
    $result.dest = $dest
}

$url = Get-AnsibleParam -obj $params -name "url" -type "str" -failifempty $true
$dest = Get-AnsibleParam -obj $params -name "dest" -type "path" -failifempty $true
$timeout = Get-AnsibleParam -obj $params -name "timeout" -type "int" -default 10
$headers = Get-AnsibleParam -obj $params -name "headers" -type "dict" -default @{}
$skip_certificate_validation = Get-AnsibleParam -obj $params -name "skip_certificate_validation" -type "bool"
$validate_certs = Get-AnsibleParam -obj $params -name "validate_certs" -type "bool" -default $true
$url_username = Get-AnsibleParam -obj $params -name "url_username" -type "str" -aliases "username"
$url_password = Get-AnsibleParam -obj $params -name "url_password" -type "str" -aliases "password"
$force_basic_auth = Get-AnsibleParam -obj $params -name "force_basic_auth" -type "bool" -default $false
$use_proxy = Get-AnsibleParam -obj $params -name "use_proxy" -type "bool" -default $true
$proxy_url = Get-AnsibleParam -obj $params -name "proxy_url" -type "str"
$proxy_username = Get-AnsibleParam -obj $params -name "proxy_username" -type "str"
$proxy_password = Get-AnsibleParam -obj $params -name "proxy_password" -type "str"
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $true

$result = @{
    changed = $false
    dest = $dest
    url = $url
    # This is deprecated as of v2.4, remove in v2.8
    win_get_url = @{
        dest = $dest
        url = $url
    }
}

if (-not $use_proxy -and ($proxy_url -or $proxy_username -or $proxy_password)) {
    Add-Warning -obj $result -msg "Not using a proxy on request, however a 'proxy_url', 'proxy_username' or 'proxy_password' was defined."
}

$proxy = $null
if ($proxy_url) {
    $proxy = New-Object System.Net.WebProxy($proxy_url, $true)
    if ($proxy_username -and $proxy_password) {
        $proxy_credential = New-Object System.Net.NetworkCredential($proxy_username, $proxy_password)
        $proxy.Credentials = $proxy_credential
    }
}

$credentials = $null
if ($url_username) {
    if ($force_basic_auth) {
        $credentials = [convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes($url_username+":"+$url_password))
    } else {
        $credentials = New-Object System.Net.NetworkCredential($url_username, $url_password) 
    }
    
}

# If skip_certificate_validation was specified, use validate_certs
if ($skip_certificate_validation -ne $null) {
    Add-DeprecationWarning -obj $result -message "The parameter 'skip_certificate_validation' is being replaced with 'validate_certs'" -version 2.8
    $validate_certs = -not $skip_certificate_validation
}

if (-not $validate_certs) {
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
}

# Use last part of url for dest file name if a directory is supplied for $dest
if (Test-Path -LiteralPath $dest -PathType Container) {
    $uri = [System.Uri]$url
    $basename = Split-Path -Path $uri.LocalPath -Leaf
    if ($uri.LocalPath -and $uri.LocalPath -ne '/' -and $basename) {
        $url_basename = Split-Path -Path $uri.LocalPath -Leaf
        $dest = Join-Path -Path $dest -ChildPath $url_basename
    } else {
        $dest = Join-Path -Path $dest -ChildPath $uri.Host
    }
} elseif (([System.IO.Path]::GetFileName($dest)) -eq '') {
    # We have a trailing path separator
    Fail-Json -obj $result -message "The destination path '$dest' does not exist, or is not visible to the current user.  Ensure download destination folder exists (perhaps using win_file state=directory) before win_get_url runs."
}
$result.dest = $dest
$result.win_get_url.dest = $dest

# Enable TLS1.1/TLS1.2 if they're available but disabled (eg. .NET 4.5)
$security_protcols = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::SystemDefault
if ([Net.SecurityProtocolType].GetMember("Tls11").Count -gt 0) {
    $security_protcols = $security_protcols -bor [Net.SecurityProtocolType]::Tls11
}
if ([Net.SecurityProtocolType].GetMember("Tls12").Count -gt 0) {
    $security_protcols = $security_protcols -bor [Net.SecurityProtocolType]::Tls12
}
[Net.ServicePointManager]::SecurityProtocol = $security_protcols

if ($force -or -not (Test-Path -LiteralPath $dest)) {

    Download-File -result $result -url $url -dest $dest -credentials $credentials `
                  -headers $headers -timeout $timeout -use_proxy $use_proxy -proxy $proxy `
                  -whatif $check_mode

} else {

    $is_modified = CheckModified-File -result $result -url $url -dest $dest -credentials $credentials `
                                      -headers $headers -timeout $timeout -use_proxy $use_proxy -proxy $proxy

    if ($is_modified) {

        Download-File -result $result -url $url -dest $dest -credentials $credentials `
                      -headers $headers -timeout $timeout -use_proxy $use_proxy -proxy $proxy `
                      -whatif $check_mode

    }
}

Exit-Json -obj $result

