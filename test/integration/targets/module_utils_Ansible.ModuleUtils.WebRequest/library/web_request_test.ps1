#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.WebRequest

$spec = @{
    options = @{
        httpbin_host = @{ type = 'str'; required = $true }
    }
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$httpbin_host = $module.Params.httpbin_host

Function Assert-Equal {
    param(
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)][AllowNull()]$Actual,
        [Parameter(Mandatory = $true, Position = 0)][AllowNull()]$Expected
    )

    process {
        $matched = $false
        if ($Actual -is [System.Collections.ArrayList] -or $Actual -is [Array] -or $Actual -is [System.Collections.IList]) {
            $Actual.Count | Assert-Equal -Expected $Expected.Count
            for ($i = 0; $i -lt $Actual.Count; $i++) {
                $actualValue = $Actual[$i]
                $expectedValue = $Expected[$i]
                Assert-Equal -Actual $actualValue -Expected $expectedValue
            }
            $matched = $true
        }
        else {
            $matched = $Actual -ceq $Expected
        }

        if (-not $matched) {
            if ($Actual -is [PSObject]) {
                $Actual = $Actual.ToString()
            }

            $call_stack = (Get-PSCallStack)[1]
            $module.Result.test = $test
            $module.Result.actual = $Actual
            $module.Result.expected = $Expected
            $module.Result.line = $call_stack.ScriptLineNumber
            $module.Result.method = $call_stack.Position.Text

            $module.FailJson("AssertionError: actual != expected")
        }
    }
}

Function Convert-StreamToString {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [System.IO.Stream]
        $Stream
    )

    $ms = New-Object -TypeName System.IO.MemoryStream
    try {
        $Stream.CopyTo($ms)
        [System.Text.Encoding]::UTF8.GetString($ms.ToArray())
    }
    finally {
        $ms.Dispose()
    }
}

$tests = [Ordered]@{
    'GET request over http' = {
        $r = Get-AnsibleWebRequest -Uri "http://$httpbin_host/get"

        $r.Method | Assert-Equal -Expected 'GET'
        $r.Timeout | Assert-Equal -Expected 30000
        $r.UseDefaultCredentials | Assert-Equal -Expected $false
        $r.Credentials | Assert-Equal -Expected $null
        $r.ClientCertificates.Count | Assert-Equal -Expected 0
        $r.Proxy.Credentials | Assert-Equal -Expected $null
        $r.UserAgent | Assert-Equal -Expected 'ansible-httpget'

        $actual = Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.StatusCode | Assert-Equal -Expected 200
            Convert-StreamToString -Stream $Stream
        } | ConvertFrom-Json

        $actual.headers.'User-Agent' | Assert-Equal -Expected 'ansible-httpget'
        $actual.headers.'Host' | Assert-Equal -Expected $httpbin_host

        $module.Result.msg | Assert-Equal -Expected 'OK'
        $module.Result.status_code | Assert-Equal -Expected 200
        $module.Result.ContainsKey('elapsed') | Assert-Equal -Expected $true
    }

    'GET request over https' = {
        # url is an alias for the -Uri parameter.
        $r = Get-AnsibleWebRequest -url "https://$httpbin_host/get"

        $r.Method | Assert-Equal -Expected 'GET'
        $r.Timeout | Assert-Equal -Expected 30000
        $r.UseDefaultCredentials | Assert-Equal -Expected $false
        $r.Credentials | Assert-Equal -Expected $null
        $r.ClientCertificates.Count | Assert-Equal -Expected 0
        $r.Proxy.Credentials | Assert-Equal -Expected $null
        $r.UserAgent | Assert-Equal -Expected 'ansible-httpget'

        $actual = Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.StatusCode | Assert-Equal -Expected 200
            Convert-StreamToString -Stream $Stream
        } | ConvertFrom-Json

        $actual.headers.'User-Agent' | Assert-Equal -Expected 'ansible-httpget'
        $actual.headers.'Host' | Assert-Equal -Expected $httpbin_host
    }

    'POST request' = {
        $getParams = @{
            Headers = @{
                'Content-Type' = 'application/json'
            }
            Method = 'POST'
            Uri = "https://$httpbin_host/post"
        }
        $r = Get-AnsibleWebRequest @getParams

        $r.Method | Assert-Equal -Expected 'POST'
        $r.Timeout | Assert-Equal -Expected 30000
        $r.UseDefaultCredentials | Assert-Equal -Expected $false
        $r.Credentials | Assert-Equal -Expected $null
        $r.ClientCertificates.Count | Assert-Equal -Expected 0
        $r.Proxy.Credentials | Assert-Equal -Expected $null
        $r.ContentType | Assert-Equal -Expected 'application/json'
        $r.UserAgent | Assert-Equal -Expected 'ansible-httpget'

        $body = New-Object -TypeName System.IO.MemoryStream -ArgumentList @(,
            ([System.Text.Encoding]::UTF8.GetBytes('{"foo":"bar"}'))
        )
        $actual = Invoke-WithWebRequest -Module $module -Request $r -Body $body -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.StatusCode | Assert-Equal -Expected 200
            Convert-StreamToString -Stream $Stream
        } | ConvertFrom-Json

        $actual.headers.'User-Agent' | Assert-Equal -Expected 'ansible-httpget'
        $actual.headers.'Host' | Assert-Equal -Expected $httpbin_host
        $actual.data | Assert-Equal -Expected '{"foo":"bar"}'
    }

    'Safe redirection of GET' = {
        $r = Get-AnsibleWebRequest -Uri "http://$httpbin_host/redirect/2"

        Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.ResponseUri | Assert-Equal -Expected "http://$httpbin_host/get"
            $Response.StatusCode | Assert-Equal -Expected 200
        }
    }

    'Safe redirection of HEAD' = {
        $r = Get-AnsibleWebRequest -Uri "http://$httpbin_host/redirect/2" -Method HEAD

        Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.ResponseUri | Assert-Equal -Expected "http://$httpbin_host/get"
            $Response.StatusCode | Assert-Equal -Expected 200
        }
    }

    'Safe redirection of PUT' = {
        $params = @{
            Method = 'PUT'
            Uri = "http://$httpbin_host/redirect-to?url=https://$httpbin_host/put"
        }
        $r = Get-AnsibleWebRequest @params

        Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.ResponseUri | Assert-Equal -Expected $r.RequestUri
            $Response.StatusCode | Assert-Equal -Expected 302
        }
    }

    'None redirection of GET' = {
        $params = @{
            FollowRedirects = 'None'
            Uri = "http://$httpbin_host/redirect/2"
        }
        $r = Get-AnsibleWebRequest @params

        Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.ResponseUri | Assert-Equal -Expected $r.RequestUri
            $Response.StatusCode | Assert-Equal -Expected 302
        }
    }

    'None redirection of HEAD' = {
        $params = @{
            follow_redirects = 'None'
            method = 'HEAD'
            Uri = "http://$httpbin_host/redirect/2"
        }
        $r = Get-AnsibleWebRequest @params

        Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.ResponseUri | Assert-Equal -Expected $r.RequestUri
            $Response.StatusCode | Assert-Equal -Expected 302
        }
    }

    'None redirection of PUT' = {
        $params = @{
            FollowRedirects = 'None'
            Method = 'PUT'
            Uri = "http://$httpbin_host/redirect-to?url=https://$httpbin_host/put"
        }
        $r = Get-AnsibleWebRequest @params

        Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.ResponseUri | Assert-Equal -Expected $r.RequestUri
            $Response.StatusCode | Assert-Equal -Expected 302
        }
    }

    'All redirection of GET' = {
        $params = @{
            FollowRedirects = 'All'
            Uri = "http://$httpbin_host/redirect/2"
        }
        $r = Get-AnsibleWebRequest @params

        Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.ResponseUri | Assert-Equal -Expected "http://$httpbin_host/get"
            $Response.StatusCode | Assert-Equal -Expected 200
        }
    }

    'All redirection of HEAD' = {
        $params = @{
            follow_redirects = 'All'
            method = 'HEAD'
            Uri = "http://$httpbin_host/redirect/2"
        }
        $r = Get-AnsibleWebRequest @params

        Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.ResponseUri | Assert-Equal -Expected "http://$httpbin_host/get"
            $Response.StatusCode | Assert-Equal -Expected 200
        }
    }

    'All redirection of PUT' = {
        $params = @{
            FollowRedirects = 'All'
            Method = 'PUT'
            Uri = "http://$httpbin_host/redirect-to?url=https://$httpbin_host/put"
        }
        $r = Get-AnsibleWebRequest @params

        Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.ResponseUri | Assert-Equal -Expected "https://$httpbin_host/put"
            $Response.StatusCode | Assert-Equal -Expected 200
        }
    }

    'Exceeds maximum redirection - ignored' = {
        $params = @{
            MaximumRedirection = 4
            Uri = "https://$httpbin_host/redirect/5"
        }
        $r = Get-AnsibleWebRequest @params

        Invoke-WithWebRequest -Module $module -Request $r -IgnoreBadResponse -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.ResponseUri | Assert-Equal -Expected "https://$httpbin_host/relative-redirect/1"
            $Response.StatusCode | Assert-Equal -Expected 302
        }
    }

    'Exceeds maximum redirection - exception' = {
        $params = @{
            MaximumRedirection = 1
            Uri = "https://$httpbin_host/redirect/2"
        }
        $r = Get-AnsibleWebRequest @params

        $failed = $false
        try {
            $null = Invoke-WithWebRequest -Module $module -Request $r -Script {}
        }
        catch {
            $_.Exception.GetType().Name | Assert-Equal -Expected 'WebException'
            $_.Exception.Message | Assert-Equal -Expected 'Too many automatic redirections were attempted.'
            $failed = $true
        }
        $failed | Assert-Equal -Expected $true
    }

    'Basic auth as Credential' = {
        $params = @{
            Url = "http://$httpbin_host/basic-auth/username/password"
            UrlUsername = 'username'
            UrlPassword = 'password'
        }
        $r = Get-AnsibleWebRequest @params

        Invoke-WithWebRequest -Module $module -Request $r -IgnoreBadResponse -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.StatusCode | Assert-Equal -Expected 200
        }
    }

    'Basic auth as Header' = {
        $params = @{
            Url = "http://$httpbin_host/basic-auth/username/password"
            url_username = 'username'
            url_password = 'password'
            ForceBasicAuth = $true
        }
        $r = Get-AnsibleWebRequest @params

        Invoke-WithWebRequest -Module $module -Request $r -IgnoreBadResponse -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.StatusCode | Assert-Equal -Expected 200
        }
    }

    'Send request with headers' = {
        $params = @{
            Headers = @{
                'Content-Length' = 0
                testingheader = 'testing_header'
                TestHeader = 'test-header'
                'User-Agent' = 'test-agent'
            }
            Url = "https://$httpbin_host/get"
        }
        $r = Get-AnsibleWebRequest @params

        $actual = Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.StatusCode | Assert-Equal -Expected 200
            Convert-StreamToString -Stream $Stream
        } | ConvertFrom-Json

        $actual.headers.'Testheader' | Assert-Equal -Expected 'test-header'
        $actual.headers.'testingheader' | Assert-Equal -Expected 'testing_header'
        $actual.Headers.'User-Agent' | Assert-Equal -Expected 'test-agent'
    }

    'Request with timeout' = {
        $params = @{
            Uri = "https://$httpbin_host/delay/5"
            Timeout = 1
        }
        $r = Get-AnsibleWebRequest @params

        $failed = $false
        try {
            $null = Invoke-WithWebRequest -Module $module -Request $r -Script {}
        }
        catch {
            $failed = $true
            $_.Exception.GetType().Name | Assert-Equal -Expected WebException
            $_.Exception.Message | Assert-Equal -Expected 'The operation has timed out'
        }
        $failed | Assert-Equal -Expected $true
    }

    'Request with file URI' = {
        $filePath = Join-Path $module.Tmpdir -ChildPath 'test.txt'
        Set-Content -LiteralPath $filePath -Value 'test'

        $r = Get-AnsibleWebRequest -Uri $filePath

        $actual = Invoke-WithWebRequest -Module $module -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.ContentLength | Assert-Equal -Expected 6
            Convert-StreamToString -Stream $Stream
        }
        $actual | Assert-Equal -Expected "test`r`n"
        $module.Result.msg | Assert-Equal -Expected "OK"
        $module.Result.status_code | Assert-Equal -Expected 200
    }

    'Web request based on module options' = {
        Set-Variable complex_args -Scope Global -Value @{
            url = "https://$httpbin_host/redirect/2"
            method = 'GET'
            follow_redirects = 'safe'
            headers = @{
                'User-Agent' = 'other-agent'
            }
            http_agent = 'actual-agent'
            maximum_redirection = 2
            timeout = 10
            validate_certs = $false
        }
        $spec = @{
            options = @{
                url = @{ type = 'str'; required = $true }
                test = @{ type = 'str'; choices = 'abc', 'def' }
            }
            mutually_exclusive = @(, @('url', 'test'))
        }

        $testModule = [Ansible.Basic.AnsibleModule]::Create(@(), $spec, @(Get-AnsibleWebRequestSpec))
        $r = Get-AnsibleWebRequest -Url $testModule.Params.url -Module $testModule

        $actual = Invoke-WithWebRequest -Module $testModule -Request $r -Script {
            Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

            $Response.ResponseUri | Assert-Equal -Expected "https://$httpbin_host/get"
            Convert-StreamToString -Stream $Stream
        } | ConvertFrom-Json
        $actual.headers.'User-Agent' | Assert-Equal -Expected 'actual-agent'
    }

    'Web request with default proxy' = {
        $params = @{
            Uri = "https://$httpbin_host/get"
        }
        $r = Get-AnsibleWebRequest @params

        $null -ne $r.Proxy | Assert-Equal -Expected $true
    }

    'Web request with no proxy' = {
        $params = @{
            Uri = "https://$httpbin_host/get"
            UseProxy = $false
        }
        $r = Get-AnsibleWebRequest @params

        $null -eq $r.Proxy | Assert-Equal -Expected $true
    }
}

# setup and teardown should favour native tools to create and delete the service and not the util we are testing.
foreach ($testImpl in $tests.GetEnumerator()) {
    Set-Variable -Name complex_args -Scope Global -Value @{}
    $test = $testImpl.Key
    &$testImpl.Value
}

$module.Result.data = "success"
$module.ExitJson()
