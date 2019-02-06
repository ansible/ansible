#!powershell

# Copyright: (c) 2015, Paul Durivage <paul.durivage@rackspace.com>
# Copyright: (c) 2015, Tal Auslander <tal@cloudshare.com>
# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

$spec = @{
    options = @{
        url = @{ type='str'; required=$true }
        dest = @{ type='path'; required=$true }
        timeout = @{ type='int'; default=10 }
        headers = @{ type='dict'; default=@{} }
        validate_certs = @{ type='bool'; default=$true }
        url_username = @{ type='str'; aliases=@( 'username' ) }
        url_password = @{ type='str'; aliases=@( 'password' ); no_log=$true }
        force_basic_auth = @{ type='bool'; default=$false }
        use_proxy = @{ type='bool'; default=$true }
        proxy_url = @{ type='str' }
        proxy_username = @{ type='str' }
        proxy_password = @{ type='str'; no_log=$true }
        force = @{ type='bool'; default=$true }
        checksum = @{ type='str'; default=$null }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$url = $module.Params.url
$dest = $module.Params.dest
$timeout = $module.Params.timeout
$headers = $module.Params.headers
$validate_certs = $module.Params.validate_certs
$url_username = $module.Params.url_username
$url_password = $module.Params.url_password
$force_basic_auth = $module.Params.force_basic_auth
$use_proxy = $module.Params.use_proxy
$proxy_url = $module.Params.proxy_url
$proxy_username = $module.Params.proxy_username
$proxy_password = $module.Params.proxy_password
$force = $module.Params.force
$checksum = $module.Params.checksum

Add-CSharpType -AnsibleModule $module -References @'
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
'@
Function Get-Checksum-From-Url {
    param($module, $url, $headers, $credentials, $timeout, $use_proxy, $proxy)
    if ($checksum) {
        Try {
            $is_modified_checksum = CheckModifiedChecksum-File -dest $dest -checksum $checksum

            if ($is_modified_checksum) {
                return $true
            }
        } Catch {
            $module.FailJson("Unknown checksum error for '$dest': $($_.Exception.Message)", $_)
        }
    }

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
        $webRequest.Method = [System.Net.WebRequestMethods+Ftp]::DownloadFile
    } else {
        $webRequest.Method = [System.Net.WebRequestMethods+Http]::Get
    }

    # FIXME: Split both try-statements and single-out catched exceptions with more specific error messages
    Try {
         # TBD implement case for FTP
         $webResponse = $webRequest.GetResponse()      
         $requestStream = $webResponse.GetResponseStream()
         $readStream = New-Object System.IO.StreamReader $requestStream
         $web_checksum=$readStream.ReadToEnd()
    } Catch [System.Net.WebException] {
        $module.Result.status_code = [int] $_.Exception.Response.StatusCode
        $module.FailJson("Error requesting '$url'. $($_.Exception.Message)", $_)
    } Catch {
        $module.FailJson("Error get HASH data file from '$url'. $($_.Exception.Message)", $_)
    }
    $module.Result.status_code = [int] $webResponse.StatusCode
    $module.Result.msg = [string] $webResponse.StatusDescription
    $webResponse.Close()

    return $web_checksum
}


Function CheckModified-File {
    param($module, $url, $dest, $headers, $credentials, $timeout, $use_proxy, $proxy)
    if ($checksum) {
        Try {
            $is_modified_checksum = CheckModifiedChecksum-File -dest $dest -checksum $checksum

            if ($is_modified_checksum) {
                return $true
            }
        } Catch {
            $module.FailJson("Unknown checksum error for '$dest': $($_.Exception.Message)", $_)
        }
    }

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

    # FIXME: Split both try-statements and single-out catched exceptions with more specific error messages
    Try {
        $webResponse = $webRequest.GetResponse()
        $webLastMod = $webResponse.LastModified
    } Catch [System.Net.WebException] {
        $module.Result.status_code = [int] $_.Exception.Response.StatusCode
        $module.FailJson("Error requesting '$url'. $($_.Exception.Message)", $_)
    } Catch {
        $module.FailJson("Error when requesting 'Last-Modified' date from '$url'. $($_.Exception.Message)", $_)
    }
    $module.Result.status_code = [int] $webResponse.StatusCode
    $module.Result.msg = [string] $webResponse.StatusDescription
    $webResponse.Close()

    if ($webLastMod -and ((Get-Date -Date $webLastMod).ToUniversalTime() -lt $fileLastMod)) {
        return $false
    } else {
        return $true
    }
}

Function Parse-Checksum {
    param($checksum)
    $checksum_parameter_splited = $checksum.split(":", 2)
    if ($checksum_parameter_splited.Count -ne 2) {
        throw
    }

    $checksum_algorithm = $checksum_parameter_splited[0].Trim()
    $checksum_value = $checksum_parameter_splited[1].Trim()

    return @{algorithm = $checksum_algorithm; checksum = $checksum_value}
}

Function GetNormalise-Checksum {
    param($dest, $checksum)
    if($checksum) {
        $tmpHashFromFile = Get-FileHash -Path $dest -Algorithm $(Parse-Checksum -checksum $checksum).algorithm
        return [string]$tmpHashFromFile.Hash.ToLower()
    }
    return $null
}

Function CheckModifiedChecksum-File {
    param($dest, $checksum)
    $normaliseHashDest = GetNormalise-Checksum -dest $dest -checksum $checksum

    return [bool]($normaliseHashDest -ne $(Parse-Checksum -checksum $checksum).checksum)
}

Function Download-File {
    param($module, $url, $dest, $headers, $credentials, $timeout, $use_proxy, $proxy)

    $module_start = Get-Date

    # Check $dest parent folder exists before attempting download, which avoids unhelpful generic error message.
    $dest_parent = Split-Path -LiteralPath $dest
    if (-not (Test-Path -LiteralPath $dest_parent -PathType Container)) {
        $module.FailJson("The path '$dest_parent' does not exist for destination '$dest', or is not visible to the current user.  Ensure download destination folder exists (perhaps using win_file state=directory) before win_get_url runs.")
    }

    # checksum specified, parse for algorithm and checksum
    if ($checksum) {
        Try
        {
            $checksum_parameter_splited = Parse-Checksum -checksum $checksum

            $checksum_algorithm = $checksum_parameter_splited.algorithm
            $checksum_value = $checksum_parameter_splited.checksum

            # if ($checksum_value.startswith('http://', 1) -or $checksum_value.startswith('https://', 1) -or $checksum_value.startswith('ftp://', 1)) {
            #     $checksum_url = $checksum_value
            #     # TBD
            #     $web_request = Invoke-WebRequest -Uri $checksum_url
            #     $checksum_value = $web_request.Content
            #     # $checksum_value = $checksum_value -replace '\W+', ''
            # }

            $checksum_value = $checksum_value.ToLower()
        }
        Catch {
            $module.FailJson("The 'checksum' parameter '$checksum' invalid.  Ensure format match: <algorithm>:<checksum|url>. url for checksum currently not supported.")
        }
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

    if (-not $module.CheckMode) {
        # FIXME: Single-out catched exceptions with more specific error messages
        Try {
            $extWebClient.DownloadFile($url, $dest)

            # Checksum verification for downloaded file
            if ($checksum) {
                $hashFromFile = Get-FileHash -Path $dest -Algorithm $checksum_algorithm
                $normaliseHashDest = $hashFromFile.Hash.ToLower()
                # Check both hashes are the same
                if ($normaliseHashDest -ne $checksum_value) {
                    Remove-Item -Path $dest
                    throw [string]("The checksum for {0} did not match {1}; it was {2}." -f $dest, $checksum_value, $normaliseHashDest)
                }
            }

        } Catch [System.Net.WebException] {
            $module.Result.status_code = [int] $_.Exception.Response.StatusCode
            $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            $module.FailJson("Error downloading '$url' to '$dest': $($_.Exception.Message)", $_)
        } Catch {
            $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds
            $module.Result.checksum_dest = $normaliseHashDest
            $module.FailJson("Unknown error downloading '$url' to '$dest': $($_.Exception.Message)", $_)
        }
    }

    $module.Result.status_code = 200
    $module.Result.changed = $true
    $module.Result.msg = 'OK'
    $module.Result.dest = $dest
    $module.Result.checksum_dest = $normaliseHashDest
    $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds

}

$module.Result.dest = $dest
$module.Result.elapsed = 0
$module.Result.url = $url

if (-not $use_proxy -and ($proxy_url -or $proxy_username -or $proxy_password)) {
    $module.Warn("Not using a proxy on request, however a 'proxy_url', 'proxy_username' or 'proxy_password' was defined.")
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

    # Ensure we have a string instead of a PS object to avoid serialization issues
    $dest = $dest.ToString()
} elseif (([System.IO.Path]::GetFileName($dest)) -eq '') {
    # We have a trailing path separator
    $module.FailJson("The destination path '$dest' does not exist, or is not visible to the current user.  Ensure download destination folder exists (perhaps using win_file state=directory) before win_get_url runs.")
}
$module.Result.dest = $dest

# Enable TLS1.1/TLS1.2 if they're available but disabled (eg. .NET 4.5)
$security_protocols = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::SystemDefault
if ([Net.SecurityProtocolType].GetMember("Tls11").Count -gt 0) {
    $security_protocols = $security_protocols -bor [Net.SecurityProtocolType]::Tls11
}
if ([Net.SecurityProtocolType].GetMember("Tls12").Count -gt 0) {
    $security_protocols = $security_protocols -bor [Net.SecurityProtocolType]::Tls12
}
[Net.ServicePointManager]::SecurityProtocol = $security_protocols

# Check for case $checksum variable contain url. If yes, get file data from url and replace original value in $checksum
if ($checksum) {
    $checksum_value = $(Parse-Checksum -checksum $checksum).checksum

    if ($checksum_value.startswith('http://', 1) -or $checksum_value.startswith('https://', 1) -or $checksum_value.startswith('ftp://', 1)) {
        
        $checksum = Get-Checksum-From-Url -module $module -url $checksum_value -credentials $credentials `
        -headers $headers -timeout $timeout -use_proxy $use_proxy -proxy $proxy
    }
}


if ($force -or -not (Test-Path -LiteralPath $dest)) {

    Download-File -module $module -url $url -dest $dest -credentials $credentials `
                  -headers $headers -timeout $timeout -use_proxy $use_proxy -proxy $proxy

} else {

    $is_modified = CheckModified-File -module $module -url $url -dest $dest -credentials $credentials `
                                      -headers $headers -timeout $timeout -use_proxy $use_proxy -proxy $proxy `

    if ($is_modified) {

        Download-File -module $module -url $url -dest $dest -credentials $credentials `
                      -headers $headers -timeout $timeout -use_proxy $use_proxy -proxy $proxy
    }
    else {
        Try {
            $module.Result.checksum_dest = GetNormalise-Checksum -dest $dest -checksum $checksum

        } Catch {
            $module.FailJson("Unknown checksum error for '$dest': $($_.Exception.Message)", $_)
        }
    }
}

$module.ExitJson()
