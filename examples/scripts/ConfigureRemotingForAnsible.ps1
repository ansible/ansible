#Requires -Version 3.0

# Configure a Windows host for remote management with Ansible
# -----------------------------------------------------------
#
# This script checks the current WinRM (PS Remoting) configuration and makes
# the necessary changes to allow Ansible to connect, authenticate and
# execute PowerShell commands.
#
# All events are logged to the Windows EventLog, useful for unattended runs.
#
# Use option -Verbose in order to see the verbose output messages.
#
# Use option -CertValidityDays to specify how long this certificate is valid
# starting from today. So you would specify -CertValidityDays 3650 to get
# a 10-year valid certificate.
#
# Use option -ForceNewSSLCert if the system has been SysPreped and a new
# SSL Certifcate must be forced on the WinRM Listener when re-running this
# script. This is necessary when a new SID and CN name is created.
#
# Use option -SkipNetworkProfileCheck to skip the network profile check.
# Without specifying this the script will only run if the device's interfaces
# are in DOMAIN or PRIVATE zones.  Provide this switch if you want to enable
# WinRM on a device with an interface in PUBLIC zone.
#
# Use option -SubjectName to specify the CN name of the certificate. This
# defaults to the system's hostname and generally should not be specified.
#
# Option EnableCredSSP is deprecated, you can use AuthTypes with 'CredSSP' to
# enable CredSSP optionally.
#
# Use option -AuthTypes to specify a list of authentication types to enable. By
# default, Basic is enabled. Acceptable values are 'Basic' and 'CredSSP'. If
# the legacy option EnableCredSSP is enabled, CredSSP will be added to the AuthTypes
# array.
#
# Use option -EnsureSslOnly switch to ensure that only the HTTPS listener is
# enabled. This will disable any HTTP listeners and remove any firewall rules
# that allow WinRM HTTP traffic through.

# Written by Trond Hindenes <trond@hindenes.com>
# Updated by Chris Church <cchurch@ansible.com>
# Updated by Michael Crilly <mike@autologic.cm>
# Updated by Anton Ouzounov <Anton.Ouzounov@careerbuilder.com>
# Updated by Nicolas Simond <contact@nicolas-simond.com>
# Updated by Dag Wieërs <dag@wieers.com>
# Updated by Jordan Borean <jborean93@gmail.com>
# Updated by Kamran Ayub <kamran.ayub@gmail.com>
#
# Version 1.0 - 2014-07-06
# Version 1.1 - 2014-11-11
# Version 1.2 - 2015-05-15
# Version 1.3 - 2016-04-04
# Version 1.4 - 2017-01-05
# Version 1.5 - 2017-02-09
# Version 1.6 - 2017-04-18

# Support -Verbose option
[CmdletBinding()]

Param (
    [string]$SubjectName = $env:COMPUTERNAME,
    [int]$CertValidityDays = 1095,
    [switch]$SkipNetworkProfileCheck,
    $CreateSelfSignedCert = $true,
    [switch]$ForceNewSSLCert,
    [switch]$EnableCredSSP,
    [ValidateSet('Basic', 'CredSSP')]
    [string[]]$AuthTypes = @('Basic'),
    [switch]$EnsureSslOnly
)

Set-Variable WinRmHttpPort -Option Constant -Value 5985
Set-Variable WinRmHttpsPort -Option Constant -Value 5986

Function Write-Log
{
    $Message = $args[0]
    Write-EventLog -LogName Application -Source $EventSource -EntryType Information -EventId 1 -Message $Message
}

Function Write-VerboseLog
{
    $Message = $args[0]
    Write-Verbose $Message
    Write-Log $Message
}

Function Write-HostLog
{
    $Message = $args[0]
    Write-Host $Message
    Write-Log $Message
}

Function New-LegacySelfSignedCert
{
    Param (
        [string]$SubjectName,
        [int]$ValidDays = 1095
    )

    $name = New-Object -COM "X509Enrollment.CX500DistinguishedName.1"
    $name.Encode("CN=$SubjectName", 0)

    $key = New-Object -COM "X509Enrollment.CX509PrivateKey.1"
    $key.ProviderName = "Microsoft RSA SChannel Cryptographic Provider"
    $key.KeySpec = 1
    $key.Length = 4096
    $key.SecurityDescriptor = "D:PAI(A;;0xd01f01ff;;;SY)(A;;0xd01f01ff;;;BA)(A;;0x80120089;;;NS)"
    $key.MachineContext = 1
    $key.Create()

    $serverauthoid = New-Object -COM "X509Enrollment.CObjectId.1"
    $serverauthoid.InitializeFromValue("1.3.6.1.5.5.7.3.1")
    $ekuoids = New-Object -COM "X509Enrollment.CObjectIds.1"
    $ekuoids.Add($serverauthoid)
    $ekuext = New-Object -COM "X509Enrollment.CX509ExtensionEnhancedKeyUsage.1"
    $ekuext.InitializeEncode($ekuoids)

    $cert = New-Object -COM "X509Enrollment.CX509CertificateRequestCertificate.1"
    $cert.InitializeFromPrivateKey(2, $key, "")
    $cert.Subject = $name
    $cert.Issuer = $cert.Subject
    $cert.NotBefore = (Get-Date).AddDays(-1)
    $cert.NotAfter = $cert.NotBefore.AddDays($ValidDays)
    $cert.X509Extensions.Add($ekuext)
    $cert.Encode()

    $enrollment = New-Object -COM "X509Enrollment.CX509Enrollment.1"
    $enrollment.InitializeFromRequest($cert)
    $certdata = $enrollment.CreateRequest(0)
    $enrollment.InstallResponse(2, $certdata, 0, "")

    # extract/return the thumbprint from the generated cert
    $parsed_cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
    $parsed_cert.Import([System.Text.Encoding]::UTF8.GetBytes($certdata))

    return $parsed_cert.Thumbprint
}

# Setup error handling.
Trap
{
    $_
    Exit 1
}
$ErrorActionPreference = "Stop"

# Get the ID and security principal of the current user account
$myWindowsID=[System.Security.Principal.WindowsIdentity]::GetCurrent()
$myWindowsPrincipal=new-object System.Security.Principal.WindowsPrincipal($myWindowsID)

# Get the security principal for the Administrator role
$adminRole=[System.Security.Principal.WindowsBuiltInRole]::Administrator

# Check to see if we are currently running "as Administrator"
if (-Not $myWindowsPrincipal.IsInRole($adminRole))
{
    Write-Host "ERROR: You need elevated Administrator privileges in order to run this script."
    Write-Host "       Start Windows PowerShell by using the Run as Administrator option."
    Exit 2
}

$EventSource = $MyInvocation.MyCommand.Name
If (-Not $EventSource)
{
    $EventSource = "Powershell CLI"
}

If ([System.Diagnostics.EventLog]::Exists('Application') -eq $False -or [System.Diagnostics.EventLog]::SourceExists($EventSource) -eq $False)
{
    New-EventLog -LogName Application -Source $EventSource
}

# Detect PowerShell version.
If ($PSVersionTable.PSVersion.Major -lt 3)
{
    Write-Log "PowerShell version 3 or higher is required."
    Throw "PowerShell version 3 or higher is required."
}

# Find and start the WinRM service.
Write-Verbose "Verifying WinRM service."
If (!(Get-Service "WinRM"))
{
    Write-Log "Unable to find the WinRM service."
    Throw "Unable to find the WinRM service."
}
ElseIf ((Get-Service "WinRM").Status -ne "Running")
{
    Write-Verbose "Starting WinRM service."
    Start-Service -Name "WinRM" -ErrorAction Stop
    Write-Log "Started WinRM service."
    Write-Verbose "Setting WinRM service to start automatically on boot."
    Set-Service -Name "WinRM" -StartupType Automatic
    Write-Log "Set WinRM service to start automatically on boot."

}

# WinRM should be running; check that we have a PS session config.
If (!(Get-PSSessionConfiguration -Verbose:$false) -or (!(Get-ChildItem WSMan:\localhost\Listener)))
{
  If ($SkipNetworkProfileCheck) {
    Write-Verbose "Enabling PS Remoting without checking Network profile."
    Enable-PSRemoting -SkipNetworkProfileCheck -Force -ErrorAction Stop
    Write-Log "Enabled PS Remoting without checking Network profile."
  }
  Else {
    Write-Verbose "Enabling PS Remoting."
    Enable-PSRemoting -Force -ErrorAction Stop
    Write-Log "Enabled PS Remoting."
  }
}
Else
{
    Write-Verbose "PS Remoting is already enabled."
}

# Make sure there is a SSL listener.
$listeners = Get-ChildItem WSMan:\localhost\Listener
If (!($listeners | Where {$_.Keys -like "TRANSPORT=HTTPS"}))
{
    # We cannot use New-SelfSignedCertificate on 2012R2 and earlier
    $thumbprint = New-LegacySelfSignedCert -SubjectName $SubjectName -ValidDays $CertValidityDays
    Write-HostLog "Self-signed SSL certificate generated; thumbprint: $thumbprint"

    # Create the hashtables of settings to be used.
    $valueset = @{
        Hostname = $SubjectName
        CertificateThumbprint = $thumbprint
    }

    $selectorset = @{
        Transport = "HTTPS"
        Address = "*"
    }

    Write-Verbose "Enabling SSL listener."
    New-WSManInstance -ResourceURI 'winrm/config/Listener' -SelectorSet $selectorset -ValueSet $valueset
    Write-Log "Enabled SSL listener."
}
Else
{
    Write-Verbose "SSL listener is already active."

    # Force a new SSL cert on Listener if the $ForceNewSSLCert
    If ($ForceNewSSLCert)
    {

        # We cannot use New-SelfSignedCertificate on 2012R2 and earlier
        $thumbprint = New-LegacySelfSignedCert -SubjectName $SubjectName -ValidDays $CertValidityDays
        Write-HostLog "Self-signed SSL certificate generated; thumbprint: $thumbprint"

        $valueset = @{
            CertificateThumbprint = $thumbprint
            Hostname = $SubjectName
        }

        # Delete the listener for SSL
        $selectorset = @{
            Address = "*"
            Transport = "HTTPS"
        }
        Remove-WSManInstance -ResourceURI 'winrm/config/Listener' -SelectorSet $selectorset

        # Add new Listener with new SSL cert
        New-WSManInstance -ResourceURI 'winrm/config/Listener' -SelectorSet $selectorset -ValueSet $valueset
    }
}

# If SSL only, remove existing HTTP listener
if ($EnsureSslOnly -and ($listeners | Where {$_.Keys -like "TRANSPORT=HTTP"})) {
    
    # Delete the listener for HTTP
    $selectorset = @{
        Address = "*"
        Transport = "HTTP"
    }
    Remove-WSManInstance -ResourceURI 'winrm/config/Listener' -SelectorSet $selectorset
    Write-HostLog "Removed WinRM HTTP listener"

    # Remove firewall rule if it exists
    $httpfirewallrule = Get-NetFirewallPortFilter `
        | Where { $_.LocalPort -eq $WinRmHttpPort } `
        | Get-NetFirewallRule

    if ($httpfirewallrule) {
        # Remove firewall rule
        $httpfirewallrule | Remove-NetFirewallRule
        Write-HostLog "Removed WinRM HTTP firewall rule"
    }
}

# Check for basic authentication.
$basicAuthSetting = Get-ChildItem WSMan:\localhost\Service\Auth | Where {$_.Name -eq "Basic"}
If (($basicAuthSetting.Value) -eq $false -and $AuthTypes -contains 'Basic')
{
    Write-Verbose "Enabling basic auth support."
    Set-Item -Path "WSMan:\localhost\Service\Auth\Basic" -Value $true
    Write-Log "Enabled basic auth support."
}
Else
{
    Write-Verbose "Basic auth is already enabled."
}

# Support backwards-compatible switch
If ($EnableCredSSP -and $AuthTypes -notcontains 'CredSSP') {
    $AuthTypes = @($AuthTypes) + 'CredSSP'
}
# Check for CredSSP authentication.
$credsspAuthSetting = Get-ChildItem WSMan:\localhost\Service\Auth | Where {$_.Name -eq "CredSSP"}
If (($credsspAuthSetting.Value) -eq $false -and $AuthTypes -contains 'CredSSP')
{
    Write-Verbose "Enabling CredSSP auth support."
    Enable-WSManCredSSP -Role Server -Force
    Write-Log "Enabled CredSSP auth support."
} Else {
    Write-Verbose "CredSSP auth is already enabled."
}

# Configure firewall to allow WinRM HTTPS connections.
$httpsfirewallrule = Get-NetFirewallPortFilter `
    | Where { $_.LocalPort -eq $WinRmHttpsPort } `
    | Get-NetFirewallRule

If (!$httpsfirewallrule)
{
    Write-Verbose "Adding firewall rule to allow WinRM HTTPS."
    New-NetFirewallRule -DisplayName 'Allow WinRM HTTPS' -LocalPort $WinRmHttpsPort -Protocol TCP -Profile Any    
    Write-Log "Added firewall rule to allow WinRM HTTPS."
}
ElseIf ($httpsfirewallrule.Profile -notcontains 'Any')
{
    Write-Verbose "Updating firewall rule(s) to allow WinRM HTTPS for any profile."
    $httpsfirewallrule | Set-NetFirewallRule -Profile 'Any'
    Write-Log "Updated firewall rule(s) to allow WinRM HTTPS for any profile."
}
Else
{
    Write-Verbose "Firewall rule already exists to allow WinRM HTTPS."
}

# Test a remoting connection to localhost, which should work.
if (!$EnsureSslOnly) {
    $httpResult = Invoke-Command -ComputerName "localhost" -ScriptBlock {$env:COMPUTERNAME} -ErrorVariable httpError -ErrorAction SilentlyContinue
}
$httpsOptions = New-PSSessionOption -SkipCACheck -SkipCNCheck -SkipRevocationCheck

$httpsResult = New-PSSession -UseSSL -ComputerName "localhost" -SessionOption $httpsOptions -ErrorVariable httpsError -ErrorAction SilentlyContinue

If ($httpResult -and $httpsResult)
{
    Write-Verbose "HTTP: Enabled | HTTPS: Enabled"
}
ElseIf ($httpsResult -and !$httpResult)
{
    Write-Verbose "HTTP: Disabled | HTTPS: Enabled"
}
ElseIf ($httpResult -and !$httpsResult)
{
    Write-Verbose "HTTP: Enabled | HTTPS: Disabled"
}
Else
{
    Write-Log "Unable to establish an HTTP or HTTPS remoting session."
    Throw "Unable to establish an HTTP or HTTPS remoting session."
}
Write-VerboseLog "PS Remoting has been successfully configured for Ansible."
