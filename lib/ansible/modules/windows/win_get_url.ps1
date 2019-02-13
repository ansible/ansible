#!powershell

# Copyright: (c) 2015, Paul Durivage <paul.durivage@rackspace.com>
# Copyright: (c) 2015, Tal Auslander <tal@cloudshare.com>
# Copyright: (c) 2017, Dag Wieers <dag@wieers.com>
# Copyright: (c) 2019, Viktor Utkin <viktor_utkin@epam.com>
# Copyright: (c) 2019, Uladzimir Klybik <uladzimir_klybik@epam.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType
#Requires -Module Ansible.ModuleUtils.FileUtil

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
        checksum = @{ type='str' }
        checksum_algorithm = @{ type='str'; default='sha1'}
        checksum_url = @{ type='str' }
    }
    mutually_exclusive = @(
        ,@('checksum', 'checksum_url')
    )
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
$checksum_algorithm = $module.Params.checksum_algorithm
$checksum_url = $module.Params.checksum_url

$module.Diff.before = @{}
$module.Diff.after = @{}

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

Function GetWebRequest{
    param($url, $headers, $credentials, $timeout, $use_proxy, $proxy) 

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

    return $webRequest
}


Function Get-Checksum-From-Url {
    param($module, $url, $headers, $credentials, $timeout, $use_proxy, $proxy, $src_file_url)

    $webRequest = GetWebRequest -url $url -headers $headers -credentials $credentials -timeout $timeout -use_proxy $use_proxy -proxy $proxy

    if ($webRequest -is [System.Net.FtpWebRequest]) {
        $webRequest.Method = [System.Net.WebRequestMethods+Ftp]::DownloadFile
    } else {
        $webRequest.Method = [System.Net.WebRequestMethods+Http]::Get
    }

    # FIXME: Split both try-statements and single-out catched exceptions with more specific error messages
    Try {
         $webResponse = $webRequest.GetResponse()
         $responseStream = $webResponse.GetResponseStream()
         $readStream = New-Object System.IO.StreamReader $responseStream
         $web_checksum=$readStream.ReadToEnd()

         $basename = (Split-Path -Path $([System.Uri]$src_file_url).LocalPath -Leaf)
         $basename = [regex]::Escape($basename)
         $web_checksum_str = $web_checksum -split '\r?\n' | Select-String -Pattern $("\s+\.?\/?\\?" + $basename + "\s*$")
         if (-not $web_checksum_str) { 
             throw "Checksum record not found for file name '$basename' in file from url: '$url'"
         }

        $web_checksum_str_splitted = $web_checksum_str[0].ToString().split(" ", 2)
        $hash_from_file = $web_checksum_str_splitted[0].Trim()
        # Remove any non-alphanumeric characters
        $hash_from_file = $hash_from_file -replace '\W+', ''
    } Catch [System.Net.WebException] {
        $module.Result.status_code = [int] $_.Exception.Response.StatusCode
        $module.FailJson("Error requesting '$url'. $($_.Exception.Message)", $_)
    } Catch {
        $module.FailJson("Error get HASH data file from '$url'. $($_.Exception.Message)", $_)
    }
    Finally {
        if($webResponse) {
           $webResponse.Close()
        }
    }
    if ( [bool]([System.Uri]$url).isFile ) {
        $module.Result.status_code = 200
        $module.Result.msg = 'OK'
    } else {
        $module.Result.status_code = [int] $webResponse.StatusCode
        $module.Result.msg = [string] $webResponse.StatusDescription
    }
    return $hash_from_file
}

Function CheckModified-File {
    param($module, $url, $dest, $headers, $credentials, $timeout, $use_proxy, $proxy, $check_length)
    if ($checksum) {
        Try {
            $is_modified_checksum = CheckModifiedChecksum-File -dest $dest -checksum $checksum
            return $is_modified_checksum
        } Catch {
            $module.FailJson("Unknown checksum error for '$dest': $($_.Exception.Message)", $_)
        }
    }

    $fileLastMod = (Get-AnsibleItem -Path $dest).LastWriteTimeUtc
    $webLastMod = $null

    $fileLength = (Get-AnsibleItem -Path $dest).Length
    $webFileLength = $null

    $srcUri = [System.Uri]$url

    if([bool]$srcUri.isFile) {
        $webLastMod = (Get-AnsibleItem -Path $srcUri.AbsolutePath).LastWriteTimeUtc
        $webFileLength = (Get-AnsibleItem -Path $srcUri.AbsolutePath).Length

        $module.Result.status_code = 200
        $module.Result.msg = 'OK'
    } else {

        $webRequest = GetWebRequest -url $url -headers $headers -credentials $credentials -timeout $timeout -use_proxy $use_proxy -proxy $proxy
        $webRequestPaired = GetWebRequest -url $url -headers $headers -credentials $credentials -timeout $timeout -use_proxy $use_proxy -proxy $proxy

        if ($webRequest -is [System.Net.FtpWebRequest]) {
            $webRequest.Method = [System.Net.WebRequestMethods+Ftp]::GetDateTimestamp
        } else {
            $webRequest.Method = [System.Net.WebRequestMethods+Http]::Head
        }

        # FIXME: Split both try-statements and single-out catched exceptions with more specific error messages
        Try {
            if ($webRequest -is [System.Net.FtpWebRequest]) {
                $webRequest.Method = [System.Net.WebRequestMethods+Ftp]::GetDateTimestamp
                $webResponse = $webRequest.GetResponse()
                $webLastMod = $webResponse.LastModified

                $webRequestPaired.Method = [System.Net.WebRequestMethods+Ftp]::GetFileSize
                $webResponsePaired = $webRequestPaired.GetResponse()
                $webFileLength = $webResponsePaired.ContentLength
            } else {
                $webRequest.Method = [System.Net.WebRequestMethods+Http]::Head
                $webResponse = $webRequest.GetResponse()
                $webLastMod = $webResponse.LastModified
                $webFileLength = $webResponse.ContentLength
            }
        } Catch [System.Net.WebException] {
            $module.Result.status_code = [int] $_.Exception.Response.StatusCode
            $module.FailJson("Error requesting '$url'. $($_.Exception.Message)", $_)
        } Catch {
            $module.FailJson("Error when requesting 'Last-Modified' date from '$url'. $($_.Exception.Message)", $_)
        }
        Finally {
            # in case GetResponse timeout, $webResponse == $null
            if($webResponse) {
               $webResponse.Close()
            }
            if($webResponsePaired) {
                $webResponsePaired.Close()
             }
        }
        $module.Result.status_code = [int] $webResponse.StatusCode
        $module.Result.msg = [string] $webResponse.StatusDescription
    }
    
    if ($check_length) {
        if ($webFileLength) {
            if($webFileLength -eq -1){
                return $false
            }
            if($webFileLength -ne $fileLength) {
                return $true
            }
        }
        return $false
    } else {
        if ($webLastMod -and ((Get-Date -Date $webLastMod).ToUniversalTime() -le $fileLastMod)) {
            return $false
        } else {
            return $true
        }
    }
}

Function Get-FileChecksum {
    param($path, $algorithm = 'sha1')
<#
    .SYNOPSIS
    Helper function to calculate a hash of a file in a way which PowerShell 3
    and above can handle
#>
    If (Test-Path -Path $path -PathType Leaf)
    {
        switch ($algorithm)
        {
            'md5' { $sp = New-Object -TypeName System.Security.Cryptography.MD5CryptoServiceProvider }
            'sha1' { $sp = New-Object -TypeName System.Security.Cryptography.SHA1CryptoServiceProvider }
            'sha256' { $sp = New-Object -TypeName System.Security.Cryptography.SHA256CryptoServiceProvider }
            'sha384' { $sp = New-Object -TypeName System.Security.Cryptography.SHA384CryptoServiceProvider }
            'sha512' { $sp = New-Object -TypeName System.Security.Cryptography.SHA512CryptoServiceProvider }
            default { 
                $module.FailJson("Unsupported hash algorithm supplied '$algorithm'")
            }
        }

        if([bool](Get-Command 'Get-FileHash' -ea 0)) {
            $raw_hash = Get-FileHash $path -Algorithm $algorithm
            $hash = $raw_hash.Hash.ToLower()
        } Else {
            $fp = [System.IO.File]::Open($path, [System.IO.Filemode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite);
            $hash = [System.BitConverter]::ToString($sp.ComputeHash($fp)).Replace("-", "").ToLower();
            $fp.Dispose();
            $module.Warn("Your host uses legacy powershell. Please update.")
        }
    }
    ElseIf (Test-Path -Path $path -PathType Container)
    {
        $hash = "3";
    }
    Else
    {
        $hash = "1";
    }
    return $hash
}

Function CheckModifiedChecksum-File {
    param($dest, $checksum)
    $normaliseHashDest = Get-FileChecksum -path $dest -algorithm $checksum_algorithm
    return [bool]($normaliseHashDest -ne $checksum)
}

Function Download-File {
    param($module, $url, $dest, $headers, $credentials, $timeout, $use_proxy, $proxy)

    $module_start = Get-Date
    $diff = ""

    # Check $dest parent folder exists before attempting download, which avoids unhelpful generic error message.
    $dest_parent = Split-Path -LiteralPath $dest
    if (-not (Test-Path -LiteralPath $dest_parent -PathType Container)) {
        $module.FailJson("The path '$dest_parent' does not exist for destination '$dest', or is not visible to the current user.  Ensure download destination folder exists (perhaps using win_file state=directory) before win_get_url runs.")
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

    Try {

        $tmpDest = [System.IO.Path]::GetTempFileName()
        $diff += "+$tmpDest`n"
        $extWebClient.DownloadFile($url, $tmpDest)

        $tmpDestHash = Get-FileChecksum -path $tmpDest -algorithm $checksum_algorithm

        #$module.Warn("tmpDest='$tmpDest' tmpDestHash='$tmpDestHash' checksum='$checksum'")

        # Checksum verification for downloaded file
        if ($checksum) {
            # Check both hashes are the same
            if ($tmpDestHash -ne $checksum) {
                throw [string]("The checksum for {0} did not match '{1}', it was '{2}'" -f $dest, $checksum, $tmpDestHash)
            } else {
                if(Test-Path -LiteralPath $dest) {
                    $destHash = Get-FileChecksum -path $dest -algorithm $checksum_algorithm
                    if ($destHash -eq $checksum) {
                        $module.Result.status_code = 200
                        $module.Result.msg = 'file already exists'
                        $module.Result.checksum_src = $tmpDestHash
                        # $module.Result.checksum_dest = $destHash
                        $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds
                        return
                    }
                } else {
                    Copy-Item -Path $tmpDest -Destination $dest -Force -WhatIf:$module.CheckMode | Out-Null
                    $diff += "+$dest`n"
                }
            }
        } else {
            $is_modified = CheckModified-File -module $module -url $url -dest $tmpDest -credentials $credentials -headers $headers `
                                                -timeout $timeout -use_proxy $use_proxy -proxy $proxy -check_length $true
            if ($is_modified) {
                throw "Source and recieved files size mismatch."
            }
            Copy-Item -Path $tmpDest -Destination $dest -Force -WhatIf:$module.CheckMode | Out-Null
            $diff += "+$dest`n"
        }

    } Catch [System.Net.WebException] {
        $module.Result.status_code = [int] $_.Exception.Response.StatusCode
        $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds
        $module.FailJson("Error downloading '$url' to '$dest': $($_.Exception.Message)", $_)
    } Catch {
        $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds
        $module.Result.checksum_dest = $destHash
        $module.FailJson("Unknown error downloading '$url' to '$dest': $($_.Exception.Message)", $_)
    }
    Finally {
        if (Test-Path -LiteralPath $tmpDest) {
            Remove-Item -Path $tmpDest | Out-Null
            $diff += "-$tmpDest`n"

            $module.Diff.after.files = $diff
        }
    }

    $module.Result.status_code = 200
    $module.Result.changed = $true
    $module.Result.msg = 'OK'
    $module.Result.dest = $dest
    $module.Result.checksum_src = $tmpDestHash
    # $module.Result.checksum_dest = $destHash
    $module.Result.elapsed = ((Get-Date) - $module_start).TotalSeconds
}

$module.Result.dest = $dest
$module.Result.elapsed = 0
$module.Result.url = $url

# normalise values
if ($checksum) {
    $checksum = $checksum.Trim().toLower()
}
if ($checksum_algorithm) {
    $checksum_algorithm = $checksum_algorithm.Trim().toLower()
}
if ($checksum_url) {
    $checksum_url = $checksum_url.Trim().toLower()
}

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
if ($checksum_url) {

    if ($checksum_url.startswith('http://', 1) -or $checksum_url.startswith('https://', 1) -or `
        $checksum_url.startswith('ftp://', 1) -or [bool]([System.Uri]$checksum_url).isFile) {
        
        $checksum = Get-Checksum-From-Url -module $module -url $checksum_url -credentials $credentials `
                                                -headers $headers -timeout $timeout -use_proxy $use_proxy `
                                                -proxy $proxy -src_file_url $url
    } else {
        $module.FailJson("Unsupported `checksum_url` value for '$dest': '$checksum_url'")
    }
}


if ($force -or -not (Test-Path -LiteralPath $dest)) {

    Download-File -module $module -url $url -dest $dest -credentials $credentials `
                  -headers $headers -timeout $timeout -use_proxy $use_proxy -proxy $proxy

} else {

    $is_modified = CheckModified-File -module $module -url $url -dest $dest -credentials $credentials -headers $headers `
                                      -timeout $timeout -use_proxy $use_proxy -proxy $proxy -check_length $false

    if ($is_modified) {

       Download-File -module $module -url $url -dest $dest -credentials $credentials `
                     -headers $headers -timeout $timeout -use_proxy $use_proxy -proxy $proxy
   } else {
       $module.Result.msg = 'file already exists'
   }
}

if(Test-Path -LiteralPath $dest) {
    $module.Result.size = (Get-AnsibleItem -Path $dest).Length
    Try {
        if(-not $module.Result.checksum_dest) {
            $module.Result.checksum_dest = Get-FileChecksum -path $dest -algorithm $checksum_algorithm
        }
    } Catch {
        $module.FailJson("Unknown checksum error for '$dest': $($_.Exception.Message)", $_)
    }
}
$module.ExitJson()
