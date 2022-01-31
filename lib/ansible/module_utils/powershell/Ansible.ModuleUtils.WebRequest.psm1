# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

Function Get-AnsibleWebRequest {
    <#
    .SYNOPSIS
    Creates a System.Net.WebRequest object based on common URL module options in Ansible.

    .DESCRIPTION
    Will create a WebRequest based on common input options within Ansible. This can be used manually or with
    Invoke-WithWebRequest.

    .PARAMETER Uri
    The URI to create the web request for.

    .PARAMETER Method
    The protocol method to use, if omitted, will use the default value for the URI protocol specified.

    .PARAMETER FollowRedirects
    Whether to follow redirect reponses. This is only valid when using a HTTP URI.
        all - Will follow all redirects
        none - Will follow no redirects
        safe - Will only follow redirects when GET or HEAD is used as the Method

    .PARAMETER Headers
    A hashtable or dictionary of header values to set on the request. This is only valid for a HTTP URI.

    .PARAMETER HttpAgent
    A string to set for the 'User-Agent' header. This is only valid for a HTTP URI.

    .PARAMETER MaximumRedirection
    The maximum number of redirections that will be followed. This is only valid for a HTTP URI.

    .PARAMETER Timeout
    The timeout in seconds that defines how long to wait until the request times out.

    .PARAMETER ValidateCerts
    Whether to validate SSL certificates, default to True.

    .PARAMETER ClientCert
    The path to PFX file to use for X509 authentication. This is only valid for a HTTP URI. This path can either
    be a filesystem path (C:\folder\cert.pfx) or a PSPath to a credential (Cert:\CurrentUser\My\<thumbprint>).

    .PARAMETER ClientCertPassword
    The password for the PFX certificate if required. This is only valid for a HTTP URI.

    .PARAMETER ForceBasicAuth
    Whether to set the Basic auth header on the first request instead of when required. This is only valid for a
    HTTP URI.

    .PARAMETER UrlUsername
    The username to use for authenticating with the target.

    .PARAMETER UrlPassword
    The password to use for authenticating with the target.

    .PARAMETER UseDefaultCredential
    Whether to use the current user's credentials if available. This will only work when using Become, using SSH with
    password auth, or WinRM with CredSSP or Kerberos with credential delegation.

    .PARAMETER UseProxy
    Whether to use the default proxy defined in IE (WinINet) for the user or set no proxy at all. This should not
    be set to True when ProxyUrl is also defined.

    .PARAMETER ProxyUrl
    An explicit proxy server to use for the request instead of relying on the default proxy in IE. This is only
    valid for a HTTP URI.

    .PARAMETER ProxyUsername
    An optional username to use for proxy authentication.

    .PARAMETER ProxyPassword
    The password for ProxyUsername.

    .PARAMETER ProxyUseDefaultCredential
    Whether to use the current user's credentials for proxy authentication if available. This will only work when
    using Become, using SSH with password auth, or WinRM with CredSSP or Kerberos with credential delegation.

    .PARAMETER Module
    The AnsibleBasic module that can be used as a backup parameter source or a way to return warnings back to the
    Ansible controller.

    .EXAMPLE
    $spec = @{
        options = @{}
    }
    $module = Ansible.Basic.AnsibleModule]::Create($args, $spec, @(Get-AnsibleWebRequestSpec))

    $web_request = Get-AnsibleWebRequest -Module $module
    #>
    [CmdletBinding()]
    [OutputType([System.Net.WebRequest])]
    Param (
        [Alias("url")]
        [System.Uri]
        $Uri,

        [System.String]
        $Method,

        [Alias("follow_redirects")]
        [ValidateSet("all", "none", "safe")]
        [System.String]
        $FollowRedirects = "safe",

        [System.Collections.IDictionary]
        $Headers,

        [Alias("http_agent")]
        [System.String]
        $HttpAgent = "ansible-httpget",

        [Alias("maximum_redirection")]
        [System.Int32]
        $MaximumRedirection = 50,

        [System.Int32]
        $Timeout = 30,

        [Alias("validate_certs")]
        [System.Boolean]
        $ValidateCerts = $true,

        # Credential params
        [Alias("client_cert")]
        [System.String]
        $ClientCert,

        [Alias("client_cert_password")]
        [System.String]
        $ClientCertPassword,

        [Alias("force_basic_auth")]
        [Switch]
        $ForceBasicAuth,

        [Alias("url_username")]
        [System.String]
        $UrlUsername,

        [Alias("url_password")]
        [System.String]
        $UrlPassword,

        [Alias("use_default_credential")]
        [Switch]
        $UseDefaultCredential,

        # Proxy params
        [Alias("use_proxy")]
        [System.Boolean]
        $UseProxy = $true,

        [Alias("proxy_url")]
        [System.String]
        $ProxyUrl,

        [Alias("proxy_username")]
        [System.String]
        $ProxyUsername,

        [Alias("proxy_password")]
        [System.String]
        $ProxyPassword,

        [Alias("proxy_use_default_credential")]
        [Switch]
        $ProxyUseDefaultCredential,

        [ValidateScript({ $_.GetType().FullName -eq 'Ansible.Basic.AnsibleModule' })]
        [System.Object]
        $Module
    )

    # Set module options for parameters unless they were explicitly passed in.
    if ($Module) {
        foreach ($param in $PSCmdlet.MyInvocation.MyCommand.Parameters.GetEnumerator()) {
            if ($PSBoundParameters.ContainsKey($param.Key)) {
                # Was set explicitly we want to use that value
                continue
            }

            foreach ($alias in @($Param.Key) + $param.Value.Aliases) {
                if ($Module.Params.ContainsKey($alias)) {
                    $var_value = $Module.Params.$alias -as $param.Value.ParameterType
                    Set-Variable -Name $param.Key -Value $var_value
                    break
                }
            }
        }
    }

    # Disable certificate validation if requested
    # FUTURE: set this on ServerCertificateValidationCallback of the HttpWebRequest once .NET 4.5 is the minimum
    if (-not $ValidateCerts) {
        [System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }
    }

    # Enable TLS1.1/TLS1.2 if they're available but disabled (eg. .NET 4.5)
    $security_protocols = [System.Net.ServicePointManager]::SecurityProtocol -bor [System.Net.SecurityProtocolType]::SystemDefault
    if ([System.Net.SecurityProtocolType].GetMember("Tls11").Count -gt 0) {
        $security_protocols = $security_protocols -bor [System.Net.SecurityProtocolType]::Tls11
    }
    if ([System.Net.SecurityProtocolType].GetMember("Tls12").Count -gt 0) {
        $security_protocols = $security_protocols -bor [System.Net.SecurityProtocolType]::Tls12
    }
    [System.Net.ServicePointManager]::SecurityProtocol = $security_protocols

    $web_request = [System.Net.WebRequest]::Create($Uri)
    if ($Method) {
        $web_request.Method = $Method
    }
    $web_request.Timeout = $Timeout * 1000

    if ($UseDefaultCredential -and $web_request -is [System.Net.HttpWebRequest]) {
        $web_request.UseDefaultCredentials = $true
    }
    elseif ($UrlUsername) {
        if ($ForceBasicAuth) {
            $auth_value = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes(("{0}:{1}" -f $UrlUsername, $UrlPassword)))
            $web_request.Headers.Add("Authorization", "Basic $auth_value")
        }
        else {
            $credential = New-Object -TypeName System.Net.NetworkCredential -ArgumentList $UrlUsername, $UrlPassword
            $web_request.Credentials = $credential
        }
    }

    if ($ClientCert) {
        # Expecting either a filepath or PSPath (Cert:\CurrentUser\My\<thumbprint>)
        $cert = Get-Item -LiteralPath $ClientCert -ErrorAction SilentlyContinue
        if ($null -eq $cert) {
            Write-Error -Message "Client certificate '$ClientCert' does not exist" -Category ObjectNotFound
            return
        }

        $crypto_ns = 'System.Security.Cryptography.X509Certificates'
        if ($cert.PSProvider.Name -ne 'Certificate') {
            try {
                $cert = New-Object -TypeName "$crypto_ns.X509Certificate2" -ArgumentList @(
                    $ClientCert, $ClientCertPassword
                )
            }
            catch [System.Security.Cryptography.CryptographicException] {
                Write-Error -Message "Failed to read client certificate at '$ClientCert'" -Exception $_.Exception -Category SecurityError
                return
            }
        }
        $web_request.ClientCertificates = New-Object -TypeName "$crypto_ns.X509Certificate2Collection" -ArgumentList @(
            $cert
        )
    }

    if (-not $UseProxy) {
        $proxy = $null
    }
    elseif ($ProxyUrl) {
        $proxy = New-Object -TypeName System.Net.WebProxy -ArgumentList $ProxyUrl, $true
    }
    else {
        $proxy = $web_request.Proxy
    }

    # $web_request.Proxy may return $null for a FTP web request. We only set the credentials if we have an actual
    # proxy to work with, otherwise just ignore the credentials property.
    if ($null -ne $proxy) {
        if ($ProxyUseDefaultCredential) {
            # Weird hack, $web_request.Proxy returns an IWebProxy object which only guarantees the Credentials
            # property. We cannot set UseDefaultCredentials so we just set the Credentials to the
            # DefaultCredentials in the CredentialCache which does the same thing.
            $proxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials
        }
        elseif ($ProxyUsername) {
            $proxy.Credentials = New-Object -TypeName System.Net.NetworkCredential -ArgumentList @(
                $ProxyUsername, $ProxyPassword
            )
        }
        else {
            $proxy.Credentials = $null
        }
    }

    $web_request.Proxy = $proxy

    # Some parameters only apply when dealing with a HttpWebRequest
    if ($web_request -is [System.Net.HttpWebRequest]) {
        if ($Headers) {
            foreach ($header in $Headers.GetEnumerator()) {
                switch ($header.Key) {
                    Accept { $web_request.Accept = $header.Value }
                    Connection { $web_request.Connection = $header.Value }
                    Content-Length { $web_request.ContentLength = $header.Value }
                    Content-Type { $web_request.ContentType = $header.Value }
                    Expect { $web_request.Expect = $header.Value }
                    Date { $web_request.Date = $header.Value }
                    Host { $web_request.Host = $header.Value }
                    If-Modified-Since { $web_request.IfModifiedSince = $header.Value }
                    Range { $web_request.AddRange($header.Value) }
                    Referer { $web_request.Referer = $header.Value }
                    Transfer-Encoding {
                        $web_request.SendChunked = $true
                        $web_request.TransferEncoding = $header.Value
                    }
                    User-Agent { continue }
                    default { $web_request.Headers.Add($header.Key, $header.Value) }
                }
            }
        }

        # For backwards compatibility we need to support setting the User-Agent if the header was set in the task.
        # We just need to make sure that if an explicit http_agent module was set then that takes priority.
        if ($Headers -and $Headers.ContainsKey("User-Agent")) {
            if ($HttpAgent -eq $ansible_web_request_options.http_agent.default) {
                $HttpAgent = $Headers['User-Agent']
            }
            elseif ($null -ne $Module) {
                $Module.Warn("The 'User-Agent' header and the 'http_agent' was set, using the 'http_agent' for web request")
            }
        }
        $web_request.UserAgent = $HttpAgent

        switch ($FollowRedirects) {
            none { $web_request.AllowAutoRedirect = $false }
            safe {
                if ($web_request.Method -in @("GET", "HEAD")) {
                    $web_request.AllowAutoRedirect = $true
                }
                else {
                    $web_request.AllowAutoRedirect = $false
                }
            }
            all { $web_request.AllowAutoRedirect = $true }
        }

        if ($MaximumRedirection -eq 0) {
            $web_request.AllowAutoRedirect = $false
        }
        else {
            $web_request.MaximumAutomaticRedirections = $MaximumRedirection
        }
    }

    return $web_request
}

Function Invoke-WithWebRequest {
    <#
    .SYNOPSIS
    Invokes a ScriptBlock with the WebRequest.

    .DESCRIPTION
    Invokes the ScriptBlock and handle extra information like accessing the response stream, closing those streams
    safely as well as setting common module return values.

    .PARAMETER Module
    The Ansible.Basic module to set the return values for. This will set the following return values;
        elapsed - The total time, in seconds, that it took to send the web request and process the response
        msg - The human readable description of the response status code
        status_code - An int that is the response status code

    .PARAMETER Request
    The System.Net.WebRequest to call. This can either be manually crafted or created with Get-AnsibleWebRequest.

    .PARAMETER Script
    The ScriptBlock to invoke during the web request. This ScriptBlock should take in the params
        Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

    This scriptblock should manage the response based on what it need to do.

    .PARAMETER Body
    An optional Stream to send to the target during the request.

    .PARAMETER IgnoreBadResponse
    By default a WebException will be raised for a non 2xx status code and the Script will not be invoked. This
    parameter can be set to process all responses regardless of the status code.

    .EXAMPLE Basic module that downloads a file
    $spec = @{
        options = @{
            path = @{ type = "path"; required = $true }
        }
    }
    $module = Ansible.Basic.AnsibleModule]::Create($args, $spec, @(Get-AnsibleWebRequestSpec))

    $web_request = Get-AnsibleWebRequest -Module $module

    Invoke-WithWebRequest -Module $module -Request $web_request -Script {
        Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

        $fs = [System.IO.File]::Create($module.Params.path)
        try {
            $Stream.CopyTo($fs)
            $fs.Flush()
        } finally {
            $fs.Dispose()
        }
    }
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [System.Object]
        [ValidateScript({ $_.GetType().FullName -eq 'Ansible.Basic.AnsibleModule' })]
        $Module,

        [Parameter(Mandatory = $true)]
        [System.Net.WebRequest]
        $Request,

        [Parameter(Mandatory = $true)]
        [ScriptBlock]
        $Script,

        [AllowNull()]
        [System.IO.Stream]
        $Body,

        [Switch]
        $IgnoreBadResponse
    )

    $start = Get-Date
    if ($null -ne $Body) {
        $request_st = $Request.GetRequestStream()
        try {
            $Body.CopyTo($request_st)
            $request_st.Flush()
        }
        finally {
            $request_st.Close()
        }
    }

    try {
        try {
            $web_response = $Request.GetResponse()
        }
        catch [System.Net.WebException] {
            # A WebResponse with a status code not in the 200 range will raise a WebException. We check if the
            # exception raised contains the actual response and continue on if IgnoreBadResponse is set. We also
            # make sure we set the status_code return value on the Module object if possible

            if ($_.Exception.PSObject.Properties.Name -match "Response") {
                $web_response = $_.Exception.Response

                if (-not $IgnoreBadResponse -or $null -eq $web_response) {
                    $Module.Result.msg = $_.Exception.StatusDescription
                    $Module.Result.status_code = $_.Exception.Response.StatusCode
                    throw $_
                }
            }
            else {
                throw $_
            }
        }

        if ($Request.RequestUri.IsFile) {
            # A FileWebResponse won't have these properties set
            $Module.Result.msg = "OK"
            $Module.Result.status_code = 200
        }
        else {
            $Module.Result.msg = $web_response.StatusDescription
            $Module.Result.status_code = $web_response.StatusCode
        }

        $response_stream = $web_response.GetResponseStream()
        try {
            # Invoke the ScriptBlock and pass in WebResponse and ResponseStream
            &$Script -Response $web_response -Stream $response_stream
        }
        finally {
            $response_stream.Dispose()
        }
    }
    finally {
        if ($web_response) {
            $web_response.Close()
        }
        $Module.Result.elapsed = ((Get-date) - $start).TotalSeconds
    }
}

Function Get-AnsibleWebRequestSpec {
    <#
    .SYNOPSIS
    Used by modules to get the argument spec fragment for AnsibleModule.

    .EXAMPLES
    $spec = @{
        options = @{}
    }
    $module = [Ansible.Basic.AnsibleModule]::Create($args, $spec, @(Get-AnsibleWebRequestSpec))
    #>
    @{ options = $ansible_web_request_options }
}

# See lib/ansible/plugins/doc_fragments/url_windows.py
# Kept here for backwards compat as this variable was added in Ansible 2.9. Ultimately this util should be removed
# once the deprecation period has been added.
$ansible_web_request_options = @{
    method = @{ type = "str" }
    follow_redirects = @{ type = "str"; choices = @("all", "none", "safe"); default = "safe" }
    headers = @{ type = "dict" }
    http_agent = @{ type = "str"; default = "ansible-httpget" }
    maximum_redirection = @{ type = "int"; default = 50 }
    timeout = @{ type = "int"; default = 30 }  # Was defaulted to 10 in win_get_url but 30 in win_uri so we use 30
    validate_certs = @{ type = "bool"; default = $true }

    # Credential options
    client_cert = @{ type = "str" }
    client_cert_password = @{ type = "str"; no_log = $true }
    force_basic_auth = @{ type = "bool"; default = $false }
    url_username = @{ type = "str" }
    url_password = @{ type = "str"; no_log = $true }
    use_default_credential = @{ type = "bool"; default = $false }

    # Proxy options
    use_proxy = @{ type = "bool"; default = $true }
    proxy_url = @{ type = "str" }
    proxy_username = @{ type = "str" }
    proxy_password = @{ type = "str"; no_log = $true }
    proxy_use_default_credential = @{ type = "bool"; default = $false }
}

$export_members = @{
    Function = "Get-AnsibleWebRequest", "Get-AnsibleWebRequestSpec", "Invoke-WithWebRequest"
    Variable = "ansible_web_request_options"
}
Export-ModuleMember @export_members
