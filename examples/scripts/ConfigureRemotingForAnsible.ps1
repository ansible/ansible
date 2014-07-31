# Script to set a windows computer up for remoting
# The script checks the current WinRM/Remoting configuration and makes the necessary changes
# set $VerbosePreference="Continue" before running the script in order to see the output of the script
#
# Written by Trond Hindenes <trond@hindenes.com>
#
# Version 1.0 - July 6th, 2014


Param (
    [string]$SubjectName = $env:COMPUTERNAME,
    [int]$CertValidityDays = 365,
    $CreateSelfSignedCert = $true
)


#region function defs
Function New-LegacySelfSignedCert
{
    Param (
        [string]$SubjectName,
        [int]$ValidDays = 365
    )
    
    $name = new-object -com "X509Enrollment.CX500DistinguishedName.1"
    $name.Encode("CN=$SubjectName", 0)

    $key = new-object -com "X509Enrollment.CX509PrivateKey.1"
    $key.ProviderName = "Microsoft RSA SChannel Cryptographic Provider"
    $key.KeySpec = 1
    $key.Length = 1024
    $key.SecurityDescriptor = "D:PAI(A;;0xd01f01ff;;;SY)(A;;0xd01f01ff;;;BA)(A;;0x80120089;;;NS)"
    $key.MachineContext = 1
    $key.Create()

    $serverauthoid = new-object -com "X509Enrollment.CObjectId.1"
    $serverauthoid.InitializeFromValue("1.3.6.1.5.5.7.3.1")
    $ekuoids = new-object -com "X509Enrollment.CObjectIds.1"
    $ekuoids.add($serverauthoid)
    $ekuext = new-object -com "X509Enrollment.CX509ExtensionEnhancedKeyUsage.1"
    $ekuext.InitializeEncode($ekuoids)

    $cert = new-object -com "X509Enrollment.CX509CertificateRequestCertificate.1"
    $cert.InitializeFromPrivateKey(2, $key, "")
    $cert.Subject = $name
    $cert.Issuer = $cert.Subject
    $cert.NotBefore = (get-date).addDays(-1)
    $cert.NotAfter = $cert.NotBefore.AddDays($ValidDays)
    $cert.X509Extensions.Add($ekuext)
    $cert.Encode()

    $enrollment = new-object -com "X509Enrollment.CX509Enrollment.1"
    $enrollment.InitializeFromRequest($cert)
    $certdata = $enrollment.CreateRequest(0)
    $enrollment.InstallResponse(2, $certdata, 0, "")

    #return the thumprint of the last installed cert
    ls "Cert:\LocalMachine\my"| Sort-Object notbefore -Descending | select -First 1 | select -expand Thumbprint
}

#endregion

#Start script
$ErrorActionPreference = "Stop"

#Detect PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 3)
{
    Write-Error "PowerShell/Windows Management Framework needs to be updated to 3 or higher. Stopping script"
}

#Detect OS
 $Win32_OS = Get-WmiObject Win32_OperatingSystem

 switch ($Win32_OS.Version)
 {
    "6.2.9200" {$OSVersion = "Windows Server 2012"}
    "6.1.7601" {$OSVersion = "Windows Server 2008R2"}
 }


 #Set up remoting
 Write-verbose "Verifying WS-MAN"
 if (!(get-service "WinRM"))
 {
    Write-Error "I couldnt find the winRM service on this computer. Stopping"
 }
 Elseif ((get-service "WinRM").Status -ne "Running")
 {
    Write-Verbose "Starting WinRM"
    Start-Service -Name "WinRM" -ErrorAction Stop
 }

 #At this point, winrm should be running
 #Check that we have a ps session config
 if (!(Get-PSSessionConfiguration -verbose:$false) -or (!(get-childitem WSMan:\localhost\Listener)))
 {
    Write-Verbose "PS remoting is not enabled. Activating"
    try
    {
        Enable-PSRemoting -Force -ErrorAction SilentlyContinue
    }    
    catch{}
 }
 Else
 {
    Write-Verbose "PS remoting is already active and running"
 }

 #At this point, test a remoting connection to localhost, which should work
 $result = invoke-command -ComputerName localhost -ScriptBlock {$env:computername} -ErrorVariable localremotingerror -ErrorAction SilentlyContinue
 
 $options = New-PSSessionOption -SkipCACheck -SkipCNCheck -SkipRevocationCheck
 $resultssl = New-PSSession -UseSSL -ComputerName "localhost" -SessionOption $options -ErrorVariable localremotingsslerror -ErrorAction SilentlyContinue


 if (!$result -and $resultssl)
 {
    Write-Verbose "HTTP-based sessions not enabled, HTTPS based sessions enabled"
 }
 ElseIf (!$result -and !$resultssl)
 {
    Write-error "Could not establish session on either HTTP or HTTPS. Breaking"
 }


 #at this point, make sure there is a SSL-based listener
 $listeners = dir WSMan:\localhost\Listener

 if (!($listeners | where {$_.Keys -like "TRANSPORT=HTTPS"}))
 {
    #HTTPS-based endpoint does not exist.
    if (($CreateSelfSignedCert) -and ($OSVersion -notmatch "2012"))
    {
        $thumprint = New-LegacySelfSignedCert -SubjectName $env:COMPUTERNAME
    }
    if (($CreateSelfSignedCert) -and ($OSVersion -match "2012"))
    {
        $cert = New-SelfSignedCertificate -DnsName $env:COMPUTERNAME -CertStoreLocation "Cert:\LocalMachine\My"
        $thumprint = $cert.Thumbprint
    }
    
    
    
    # Create the hashtables of settings to be used.
    $valueset = @{}
    $valueset.add('Hostname',$env:COMPUTERNAME)
    $valueset.add('CertificateThumbprint',$thumprint)

    $selectorset = @{}
    $selectorset.add('Transport','HTTPS')
    $selectorset.add('Address','*')

    Write-Verbose "Enabling SSL-based remoting"
    New-WSManInstance -ResourceURI 'winrm/config/Listener' -SelectorSet $selectorset -ValueSet $valueset 
 }
 Else
 {
    Write-Verbose "SSL-based remoting already active"
 }


 #Check for basic authentication
 $basicauthsetting = Get-ChildItem WSMan:\localhost\Service\Auth | where {$_.Name -eq "Basic"}

 if (($basicauthsetting.Value) -eq $false)
 {
    Write-Verbose "Enabling basic auth"
    Set-Item -Path "WSMan:\localhost\Service\Auth\Basic" -Value $true
 }
 Else
 {
    Write-verbose "basic auth already enabled"
 }
 
#FIrewall
netsh advfirewall firewall add rule Profile=public name="Allow WinRM HTTPS" dir=in localport=5986 protocol=TCP action=allow



 Write-Verbose "PS Remoting successfully setup for Ansible"
