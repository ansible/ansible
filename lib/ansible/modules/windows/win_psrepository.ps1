#!powershell

# Copyright: (c) 2020, Brian Scholer <@briantist>
# Copyright: (c) 2018, Wojciech Sciesinski <wojciech[at]sciesinski[dot]net>
# Copyright: (c) 2017, Daniele Lazzari <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

# win_psrepository (Windows PowerShell repositories Additions/Removals/Updates)

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$source_location = Get-AnsibleParam -obj $params -name "source_location" -aliases "source","module_source","module_source_location" -type "str"
$script_source_location = Get-AnsibleParam -obj $params -name "script_source_location" -aliases "script_source" -type "str"
$publish_location = Get-AnsibleParam -obj $params -name "publish_location" -aliases "module_publish_location" -type "str"
$script_publish_location = Get-AnsibleParam -obj $params -name "script_publish_location" -type "str"
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present", "absent"
$installation_policy = Get-AnsibleParam -obj $params -name "installation_policy" -type "str" -validateset "trusted", "untrusted"
$follow_redirects = Get-AnsibleParam -obj $params -name "follow_redirects" -type "bool" -default $true
$force = Get-AnsibleParam -obj $params -name "force" -type "bool" -default $false

$result = @{"changed" = $false}

# Update protocols so repos that disable weak TLS can be used
# Logic taken from Ansible.ModuleUtils.WebRequest
# ---
# Enable TLS1.1/TLS1.2 if they're available but disabled (eg. .NET 4.5)
$security_protocols = [System.Net.ServicePointManager]::SecurityProtocol -bor [System.Net.SecurityProtocolType]::SystemDefault
if ([System.Net.SecurityProtocolType].GetMember("Tls11").Count -gt 0) {
    $security_protocols = $security_protocols -bor [System.Net.SecurityProtocolType]::Tls11
}
if ([System.Net.SecurityProtocolType].GetMember("Tls12").Count -gt 0) {
    $security_protocols = $security_protocols -bor [System.Net.SecurityProtocolType]::Tls12
}
[System.Net.ServicePointManager]::SecurityProtocol = $security_protocols

Function Write-DebugLog {
    Param(
        [string]$msg
    )

    $DebugPreference = "Continue"
    $date_str = Get-Date -Format u
    $msg = "$date_str $msg"

    Write-Debug $msg
    if($log_path) {
        Add-Content -LiteralPath $log_path -Value $msg
    }
}
Function Resolve-RedirectedUrl {
    [CmdletBinding()]
    [OutputType([uri])]
    param(
        [Parameter(Mandatory=$true)]
        [uri]
        $Uri ,

        [Parameter()]
        [int]
        $RedirectCount = 0 ,

        [Parameter()]
        [int]
        $MaximumRedirectionDepth = 10 ,

        [Parameter()]
        [System.Collections.Generic.HashSet[System.Uri]]
        $History = (New-Object -TypeName 'System.Collections.Generic.HashSet[System.Uri]') ,

        [Parameter()]
        [Microsoft.PowerShell.Commands.WebRequestMethod]
        $Method = [Microsoft.PowerShell.Commands.WebRequestMethod]::Head
    )

    End {
        if ($Uri.Scheme -notmatch '^https?') {
            return $Uri
        }

        $null = $History.Add($Uri)
        try {
            # Weirdness: even with -ea SilentlyContinue, some exceptions are still thrown and can be caught
            # In the case of 3xx codes, it won't throw, which we want because there's no response info in the exception, but return value is valid.
            # In the case of 5xx, it will throw, but response is available in the exception.
            $response = Invoke-WebRequest -Uri $Uri -Method $Method -UseBasicParsing -MaximumRedirection $RedirectCount -ErrorAction SilentlyContinue
        }
        catch [System.InvalidOperationException] {
            $code = $_.Exception.Response.StatusCode
            $description = $_.Exception.Response.StatusDescription
            if ($code -eq [System.Net.HttpStatusCode]::NotImplemented -and
                [Microsoft.PowerShell.Commands.WebRequestMethod]::Head -eq $_.Exception.Response.Method) {
                # let's assume the target server doesn't support HEAD, like myget.org, and switch to GET
                Resolve-RedirectedUrl @PSBoundParameters -Method ([Microsoft.PowerShell.Commands.WebRequestMethod]::Get)
                return
            }
            else {
                # not sure what the deal is, better fail
                Fail-Json -obj $result -message "Error contacting URL '$Uri' with method '$Method'. Got HTTP status ${code}: '$description'"
            }
        }

        $code = $response.StatusCode
        $description = $response.StatusDescription
        if (-not $response -or -not $code) {
            Fail-Json -obj $result -message "Unkown error contacting URL '$Uri'."
        }

        if ((300..399) -contains $code) {
            if (++$RedirectCount -ge $MaximumRedirectionDepth) {
                Fail-Json -obj $result -message "Maximum redirection count ($MaximumRedirectionDepth) reached."
            }
            Write-DebugLog -msg "Following URL redirection: attempt $RedirectCount of $MaximumRedirectionDepth."

            $target = $response.Headers.Location -as [uri]
            if (-not $target) {
                Fail-Json -obj $result -message "URL replied with redirect but redirect target is missing or invalid."
            }

            if ($History.Contains($target)) {
                Fail-Json -obj $result -message "URL is redirecting infinitely (received identical response as a previous redirect: '$target')."
            }

            Resolve-RedirectedUrl -Uri $target -RedirectCount $RedirectCount -MaximumRedirectionDepth $MaximumRedirectionDepth -History $History -Method $Method
        }
        elseif ((200..299) -notcontains $code) {
            Fail-Json -obj $result -message "Error contacting URL '$Uri' with method '$Method'. Got HTTP status ${code}: '$description'"
        }
        else {
            if ($RedirectCount -gt 0) {
                Add-Warning -obj $result -message "Using URL '$Uri' after $RedirectCount redirects."
            }
            return $Uri
        }
    }
}

$repository_params = @{
    Name = $name
}

$Repo = Get-PSRepository @repository_params -ErrorAction Ignore

if ($installation_policy) {
    $repository_params.InstallationPolicy = $installation_policy
}

# Validate location params are valid URIs and add them to the params
if ($source_location) {
    if ($source_location -as [uri]) {
        $repository_params.SourceLocation = if ($follow_redirects) {
            Resolve-RedirectedUrl -Uri $source_location
        }
        else {
            $source_location
        }
    }
    else {
        Fail-Json -obj $result -Message "source_location must be a valid URL."
    }
}
elseif ($force -or -not $Repo) {
    Fail-Json -obj $result -message "source_location is required when registering a new repository or using force."
}

if ($script_source_location) {
    if ($script_source_location -as [uri]) {
        $repository_params.ScriptSourceLocation = if ($follow_redirects) {
            Resolve-RedirectedUrl -Uri $script_source_location
        }
        else {
            $script_source_location
        }
    }
    else {
        Fail-Json -obj $result -Message "script_source_location must be a valid URL."
    }
}

if ($publish_location) {
    if ($publish_location -as [uri]) {
        $repository_params.PublishLocation = if ($follow_redirects) {
            Resolve-RedirectedUrl -Uri $publish_location
        }
        else {
            $publish_location
        }
    }
    else {
            Fail-Json -obj $result -Message "publish_location must be a valid URL."
    }
}

if ($script_publish_location) {
    if ($script_publish_location -as [uri]) {
        $repository_params.ScriptPublishLocation = if ($follow_redirects) {
            Resolve-RedirectedUrl -Uri $script_publish_location
        }
        else {
            $script_publish_location
        }
    }
    else {
            Fail-Json -obj $result -Message "script_publish_location must be a valid URL."
    }
}

Function Update-NuGetPackageProvider {
    $PackageProvider = Get-PackageProvider -ListAvailable | Where-Object { ($_.name -eq 'Nuget') -and ($_.version -ge "2.8.5.201") }
    if ($null -eq $PackageProvider) {
        Find-PackageProvider -Name Nuget -ForceBootstrap -IncludeDependencies -Force | Out-Null
    }
}

if ($Repo) {
    $changed_properties = @{}

    if ($force -and -not $repository_params.InstallationPolicy) {
        $repository_params.InstallationPolicy = 'trusted'
    }

    if ($repository_params.InstallationPolicy) {
        if ($Repo.InstallationPolicy -ne $repository_params.InstallationPolicy) {
            $changed_properties.InstallationPolicy = $repository_params.InstallationPolicy
        }
    }

    if ($repository_params.SourceLocation) {
        # force check not needed here because it's done earlier; source_location is required with force
        if ($repository_params.SourceLocation -ne $Repo.SourceLocation) {
            $changed_properties.SourceLocation = $repository_params.SourceLocation
        }
    }

    if ($force -or $repository_params.ScriptSourceLocation) {
        if ($repository_params.ScriptSourceLocation -ne $Repo.ScriptSourceLocation) {
            $changed_properties.ScriptSourceLocation = $repository_params.ScriptSourceLocation
        }
    }

    if ($force -or $repository_params.PublishLocation) {
        if ($repository_params.PublishLocation -ne $Repo.PublishLocation) {
            $changed_properties.PublishLocation = $repository_params.PublishLocation
        }
    }

    if ($force -or $repository_params.ScriptPublishLocation) {
        if ($repository_params.ScriptPublishLocation -ne $Repo.ScriptPublishLocation) {
            $changed_properties.ScriptPublishLocation = $repository_params.ScriptPublishLocation
        }
    }
}

if ($Repo -and ($state -eq "absent" -or ($force -and $changed_properties.Count -gt 0))) {
    if (-not $check_mode) {
        Update-NuGetPackageProvider
        Unregister-PSRepository -Name $name
    }
    $result.changed = $true
}

if ($state -eq "present") {
    if (-not $Repo -or ($force -and $changed_properties.Count -gt 0)) {
        if (-not $repository_params.InstallationPolicy) {
            $repository_params.InstallationPolicy = "trusted"
        }
        if (-not $check_mode) {
            Update-NuGetPackageProvider
            Register-PSRepository @repository_params
        }
        $result.changed = $true
    }
    else {
        if ($changed_properties.Count -gt 0) {
            if (-not $check_mode) {
                Update-NuGetPackageProvider
                Set-PSRepository -Name $name @changed_properties
            }
            $result.changed = $true
        }
    }
}

Exit-Json -obj $result
