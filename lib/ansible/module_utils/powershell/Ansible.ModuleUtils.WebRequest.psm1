# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

Function Get-AnsibleWebRequest {
    <#
    .SYNOPSIS
    Creates a System.Net.WebRequest object based on common module options for use in modules.

    .DESCRIPTION
    Will create a WebRequest for use with Invoke-WithWebRequest or even just manually in a module based on common
    module options.

    .PARAMETER Uri
    The URI to create the web request for. This must be manually passed in and is not registered as part of the module
    options.

    .PARAMETER Method
    The protocol method to use, if omitted, will use the default value for the protocol specified.

    .PARAMETER Module
    The AnsibleBasic module that is used to display any warnings to the user.

    .PARAMETER FollowRedirects
    Whether to follow redirect reponses. This is only valid when the URI specifies a HTTP address.
        all - Will follow all redirects
        none - Will follow no redirects
        safe - Will only follow redirects when GET or HEAD is used as the Method

    .PARAMETER Headers
    A hashtable or dictionary or header values to set on the request. This is only valid for HTTP addresses.

    .PARAMETER HttpAgent
    A string to set for the 'User-Agent' header. This is only valid for HTTP addresses.

    .PARAMETER MaximumRedirection
    The maximum number of redirections that will be followed. This is only valid for HTTP addresses.

    .PARAMETER Timeout
    The timeout in seconds that defines how long to wait until the request times out.

    .PARAMETER ValidateCerts
    Whether to validate SSL certificates, default to $true.

    .PARAMETER ClientCert
    The path to PFX file to use for X509 authentication. This is only valid for HTTP addresses.

    .PARAMETER ClientCertPassword
    The password for the PFX certificate if required. This is only valid for HTTP addresses.

    .PARAMETER ForceBasicAuth
    Whether to set the Basic auth header on the first request instead of when required. This is only valid for HTTP
    addresses.

    .PARAMETER UrlUsername
    The username to use for authenticating with the target.

    .PARAMETER UrlPassword
    The password to use for authenticating with the target.

    .PARAMETER UseDefaultCredential
    Whether to use the current user's credentials if available. This will only work when using Become or the WinRM
    auth was CredSSP.

    .PARAMETER UseProxy
    Whether to use the default proxy defined in IE (WinINet) for the user or set no proxy at all. This should not be
    set to $true when ProxyUrl is also defined.

    .PARAMETER ProxyUrl
    An explicit proxy server to use for the request instead of relying on the default proxy in IE. This is only valid
    for HTTP addresses.

    .PARAMETER ProxyUsername
    An optional username to use for proxy authentication.

    .PARAMETER ProxyPassword
    The password for ProxyUsername.

    .PARAMETER ProxyUseDefaultCredential
    Whether to use the current user's credentials for proxy authentication if available. This will only work when using
    become or the WinRM auth was CredSSP.

    .EXAMPLE
    $spec = @{
        options = @{}
    }
    $spec.options += $ansible_web_request_options
    $module = Ansible.Basic.AnsibleModule]::Create($args, $spec)

    Register-AnsibleWebRequestParams -Module $module
    $web_request = Get-AnsibleWebRequest -Uri "http://www.google.com"
    #>
    [CmdletBinding()]
    [OutputType([System.Net.WebRequest])]
    param (
        # Uri and Method do not have an alias as a module may need to create multiple requests with different URIs and
        # methods. These details are down to the module to define and not an input from the user.
        [Parameter(Mandatory=$true)]
        [System.Uri]$Uri,
        [System.String]$Method,
        [Ansible.Basic.AnsibleModule]$Module,

        [Alias("follow_redirects")]
        [ValidateSet("all", "none", "safe")]
        [System.String]$FollowRedirects = "safe",

        [System.Collections.IDictionary]$Headers,

        [Alias("http_agent")]
        [System.String]$HttpAgent = "ansible-httpget",

        [Alias("maximum_redirection")]
        [System.Int32]$MaximumRedirection = 50,

        [System.Int32]$Timeout = 30,

        [Alias("validate_certs")]
        [System.Boolean]$ValidateCerts = $true,

        # Credential params
        [Alias("client_cert")]
        [System.String]$ClientCert,

        [Alias("client_cert_password")]
        [System.String]$ClientCertPassword,

        [Alias("force_basic_auth")]
        [Switch]$ForceBasicAuth,

        [Alias("url_username")]
        [System.String]$UrlUsername,

        [Alias("url_password")]
        [System.String]$UrlPassword,

        [Alias("use_default_credential")]
        [Switch]$UseDefaultCredential,

        # Proxy params
        [Alias("use_proxy")]
        [System.Boolean]$UseProxy = $true,

        [Alias("proxy_url")]
        [System.String]$ProxyUrl,

        [Alias("proxy_username")]
        [System.String]$ProxyUsername,

        [Alias("proxy_password")]
        [System.String]$ProxyPassword,

        [Alias("proxy_use_default_credential")]
        [Switch]$ProxyUseDefaultCredential
    )

    # Disable certificate validation if requested
    # TODO: set this on ServerCertificateValidationCallback of the HttpWebRequest once .NET 4.5 is the minimum
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
    } elseif ($UrlUsername) {
        if ($ForceBasicAuth) {
            $auth_value = [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes(("{0}:{1}" -f $UrlUsername, $UrlPassword)))
            $web_request.Headers.Add("Authorization", "Basic $auth_value")
        } else {
            $credential = New-Object -TypeName System.Net.NetworkCredential -ArgumentList $UrlUsername, $UrlPassword
            $web_request.Credentials = $credential
        }
    } elseif ($ClientCert) {
        if (-not (Test-Path -LiteralPath $ClientCert)) {
            Write-Error -Message "Client certificate '$ClientCert' does not exist" -Category ObjectNotFound
            return
        }

        try {
            $certs = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Certificate2Collection -ArgumentList $ClientCert, $ClientCertPassword
            $web_request.ClientCertificates = $certs
        } catch [System.Security.Cryptography.CryptographicException] {
            Write-Error -Message "Failed to read client certificate '$ClientCert'" -Exception $_.Exception -Category SecurityError
            return
        }
    }

    if (-not $UseProxy) {
        $web_request.Proxy = $null
    } elseif ($ProxyUrl) {
        $proxy = New-Object -TypeName System.Net.WebProxy -ArgumentList $ProxyUrl, $true
        if ($ProxyUseDefaultCredential) {
            $proxy.UseDefaultCredentials = $true
        } elseif ($ProxyUsername) {
            $proxy_credential = New-Object -TypeName System.Net.NetworkCredential -ArgumentList $ProxyUsername, $ProxyPassword
            $proxy.Credentials = $proxy_credential
        }

        $web_request.Proxy = $proxy
    }

    # Some parameters only apply when dealing with a HttpWebRequest
    if ($web_request -is [System.Net.HttpWebRequest]) {
        if ($Headers) {
            $request_headers = New-Object -TypeName System.Net.WebHeaderCollection

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
                    User-Agent { continue }  # does nothing as this is explicitly set below
                    default { $request_headers.Add($header.Key, $header.Value) }
                }
            }
            $web_request.Headers = $request_headers
        }
        $web_request.UserAgent = $HttpAgent

        switch ($FollowRedirects) {
            none { $web_request.AllowAutoRedirect = $false }
            safe {
                if ($web_request.Method -in @("GET", "HEAD")) {
                    $web_request.AllowAutoRedirect = $false
                } else {
                    $web_request.AllowAutoRedirect = $true
                }
            }
            all { $web_request.AllowAutoRedirect = $true }
        }

        if ($MaximumRedirection -eq 0) {
            $web_request.AllowAutoRedirect = $false
        } else {
            $web_request.MaximumAutomaticRedirections = $MaximumRedirection
        }
    }

    return $web_request
}

Function Invoke-WithWebRequest {
    <#
    .SYNOPSIS
    Invokes a predefined ScriptBlock with the WebRequest.

    .DESCRIPTION
    Invokes the ScriptBlock and handle extra information like accessing the response stream, closing those streams
    safely as well as setting common module return values.

    .PARAMETER Module
    The Ansible.Basic module to set the return values for. This will set the following return values;
        elapsed - The total time, in seconds, that it took to send the web request and process the response
        msg - The human readable description of the response status code
        status_code - An int that is the response status code

    .PARAMETER Request
    The System.Net.WebRequest to call. This can either be manually crafted or created with 'Get-AnsibleWebRequest'.

    .PARAMETER Script
    The ScriptBlock to invoke during the web request. This ScriptBlock should take in the params
        param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

    The work to process the response based on the module requires are done in this block but it does not need to
    dispose of any response streams, only what is defined in the ScriptBlock itself.

    .PARAMETER Body
    An optional Stream to send to the target during the request.

    .PARAMETER IgnoreBadResponse
    By default a WebException will be raised for a non 2xx status code and the Script will not be invoked. This
    parameter can be set to process all responses regardless of the status code.

    .EXAMPLE
    # A very basic module to download a file to a path

    $spec = @{
        options = @{
            url = @{ type = "str"; required = $true }
            path = @{ type = "path"; required = $true }
        }
    }
    $spec.options += $ansible_web_request_options
    $module = Ansible.Basic.AnsibleModule]::Create($args, $spec)

    Register-AnsibleWebRequestParams -Module $module
    $web_request = Get-AnsibleWebRequest -Uri $module.Params.url

    $script = {
        param([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

        $fs = [System.IO.File]::Create($module.Params.path)
        try {
            $Stream.CopyTo($fs)
            $fs.Flush()
        } finally {
            $fs.Dispose()
        }
    }
    Invoke-WithWebRequest -Module $module -Request $web_request -Script $script
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [Ansible.Basic.AnsibleModule]$Module,

        [Parameter(Mandatory=$true)]
        [System.Net.WebRequest]$Request,

        [Parameter(Mandatory=$true)]
        [ScriptBlock]$Script,

        [AllowNull()]
        [System.IO.Stream]$Body,

        [Switch]$IgnoreBadResponse
    )

    $start = Get-Date
    if ($null -ne $Body) {
        $request_st = $Request.GetRequestStream()
        try {
            $Body.CopyTo($request_st)
        } finally {
            $request_st.Flush()
            $request_st.Close()
        }
    }

    try {
        try {
            $web_response = $Request.GetResponse()
        } catch [System.Net.WebException] {
            # A WebResponse with a status code not in the 200 range will raise a WebException. We check if the
            # exception raised contains the actual response and continue on if IgnoreBadResponse is set. We also make
            # sure we set the status_code return value on the Module object if possible

            if ($_.Exception.PSObject.Properties.Name -match "Response") {
                $web_response = $_.Exception.Response

                if (-not $IgnoreBadResponse -or $null -eq $web_response) {
                    $Module.Result.msg = $_.Exception.StatusDescription
                    $Module.Result.status_code = $_.Exception.Response.StatusCode
                    throw $_
                }
            } else {
                throw $_
            }
        }

        if ($Request.RequestUri.IsFile) {
            # A FileWebResponse won't have these properties set
            $Module.Result.msg = "OK"
            $Module.Result.status_code = 200
        } else {
            $Module.Result.msg = $web_response.StatusDescription
            $Module.Result.status_code = $web_response.StatusCode
        }

        $response_stream = $web_response.GetResponseStream()
        try {
            # Invoke the ScriptBlock and pass in WebResponse and ResponseStream
            &$Script -Response $web_response -Stream $response_stream
        } finally {
            $response_stream.Dispose()
        }
    } finally {
        if ($web_response) {
            $web_response.Close()
        }
        $Module.Result.elapsed = ((Get-date) - $start).TotalSeconds
    }
}

Function Register-AnsibleWebRequestParams {
    <#
    .SYNOPSIS
    Scans through the module options passed in from Ansible and set's them as the default parameter value for the
    Get-AnsibleWebRequest cmdlet. This allows a user to register common module options for this cmdlet without
    repeating the arguments.

    .PARAMETER Module
    [Ansible.Basic.AnsibleModule] The instance of an AnsibleModule that contains the parameters to set.

    .EXAMPLE
    Register-AnsibleWebRequestParams -Module $module
    #>
    param (
        [Parameter(Mandatory=$true)]
        [Ansible.Basic.AnsibleModule]$Module
    )

    foreach ($option in $ansible_web_request_options.Keys) {
        if ($Module.Params.ContainsKey($option) -and $null -ne $Module.Params.$option) {
            # Need to set in the global scope so it applies to the parent calls. Because modules are run in their own
            # Runspace, this does not persist after the module has completed it's run.
            $global:PSDefaultParameterValues["Get-AnsibleWebRequest:$option"] = $Module.Params.$option
        }
    }
    $global:PSDefaultParameterValues["Get-AnsibleWebRequest:Module"] = $Module
}

$ansible_web_request_options = @{
    follow_redirects = @{ type="str"; choices=@("all","none","safe"); default="safe" }
    headers = @{ type="dict" }
    http_agent = @{ type="str"; default="ansible-httpget" }
    maximum_redirection = @{ type="int"; default=50 }
    timeout = @{ type="int"; default=30 }  # Defaulted to 10 in win_get_url but 30 in win_uri
    validate_certs = @{ type="bool"; default=$true }

    # Credential options
    client_cert = @{ type="path" }
    client_cert_password = @{ type="str"; no_log=$true }
    force_basic_auth = @{ type="bool"; default=$false }
    url_username = @{ type="str"; aliases=@("user", "username") }  # user was used in win_uri
    url_password = @{ type="str"; aliases=@("password"); no_log=$true }
    use_default_credential = @{ type="bool"; default=$false }

    # Proxy options
    use_proxy = @{ type="bool"; default=$true }
    proxy_url = @{ type="str" }
    proxy_username = @{ type="str" }
    proxy_password = @{ type="str"; no_log=$true }
    proxy_use_default_credential = @{ type="bool"; default=$false }
}

Export-ModuleMember -Function Get-AnsibleWebRequest, Invoke-WithWebRequest, Register-AnsibleWebRequestParams `
    -Variable ansible_web_request_options

