#Requires -Version 3.0
################################################################################
# Configure a Windows host for remote management with Ansible ##################
################################################################################
# To run this script in Powershell:
#
# [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
# $url  = "https://raw.githubusercontent.com/oneclick-ag/ansible/oc_dev/examples/scripts/ConfigureRemotingForAnsible.ps1"
# $file = "$env:temp\ConfigureRemotingForAnsible.ps1"
# (New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
# powershell.exe -ExecutionPolicy ByPass -File $file
#
################################################################################

[CmdletBinding()]
Param (
    [string]$SubjectName = $env:COMPUTERNAME,
    [int]$CertValidityDays = 3650,
    [switch]$ForceNewSSLCert = $true
)

################################################################################

Function Write-ProgressLog {
    $Message = $args[0]
    Write-EventLog -LogName Application -Source $EventSource -EntryType Information -EventId 1 -Message $Message
}

Function Write-VerboseLog {
    $Message = $args[0]
    Write-Verbose $Message
    Write-ProgressLog $Message
}

Function Write-HostLog {
    $Message = $args[0]
    Write-Output $Message
    Write-ProgressLog $Message
}

Function New-LegacySelfSignedCert {
    Param (
        [string]$SubjectName,
        [int]$ValidDays = 3650
    )

    $hostnonFQDN = $env:computerName
    $hostFQDN = [System.Net.Dns]::GetHostByName(($env:computerName)).Hostname
    $SignatureAlgorithm = "SHA256"

    $name = New-Object -COM "X509Enrollment.CX500DistinguishedName.1"
    $name.Encode("CN=$SubjectName", 0)

    $key = New-Object -COM "X509Enrollment.CX509PrivateKey.1"
    $key.ProviderName = "Microsoft Enhanced RSA and AES Cryptographic Provider"
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

    $SigOID = New-Object -ComObject X509Enrollment.CObjectId
    $SigOID.InitializeFromValue(([Security.Cryptography.Oid]$SignatureAlgorithm).Value)

    [string[]] $AlternativeName += $hostnonFQDN
    $AlternativeName += $hostFQDN
    $IAlternativeNames = New-Object -ComObject X509Enrollment.CAlternativeNames

    foreach ($AN in $AlternativeName) {
        $AltName = New-Object -ComObject X509Enrollment.CAlternativeName
        $AltName.InitializeFromString(0x3, $AN)
        $IAlternativeNames.Add($AltName)
    }

    $SubjectAlternativeName = New-Object -ComObject X509Enrollment.CX509ExtensionAlternativeNames
    $SubjectAlternativeName.InitializeEncode($IAlternativeNames)

    [String[]]$KeyUsage = ("DigitalSignature", "KeyEncipherment")
    $KeyUsageObj = New-Object -ComObject X509Enrollment.CX509ExtensionKeyUsage
    $KeyUsageObj.InitializeEncode([int][Security.Cryptography.X509Certificates.X509KeyUsageFlags]($KeyUsage))
    $KeyUsageObj.Critical = $true

    $cert.X509Extensions.Add($KeyUsageObj)
    $cert.X509Extensions.Add($ekuext)
    $cert.SignatureInformation.HashAlgorithm = $SigOID
    $CERT.X509Extensions.Add($SubjectAlternativeName)
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

################################################################################

# Setup error handling
Trap {
    $_
    Exit 1
}
$ErrorActionPreference = "Stop"

# Get the ID and security principal of the current user account
$myWindowsID = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$myWindowsPrincipal = new-object System.Security.Principal.WindowsPrincipal($myWindowsID)

# Get the security principal for the Administrator role
$adminRole = [System.Security.Principal.WindowsBuiltInRole]::Administrator

# Check to see if we are currently running "as Administrator"
if (-Not $myWindowsPrincipal.IsInRole($adminRole)) {
    Write-Output "ERROR: You need elevated Administrator privileges in order to run this script."
    Write-Output "       Start Windows PowerShell by using the Run as Administrator option."
    Exit 2
}

$EventSource = $MyInvocation.MyCommand.Name
If (-Not $EventSource) {
    $EventSource = "Powershell CLI"
}

If ([System.Diagnostics.EventLog]::Exists('Application') -eq $False -or [System.Diagnostics.EventLog]::SourceExists($EventSource) -eq $False) {
    New-EventLog -LogName Application -Source $EventSource
}

# Detect PowerShell version.
If ($PSVersionTable.PSVersion.Major -lt 3) {
    Write-ProgressLog "PowerShell version 3 or higher is required."
    Throw "PowerShell version 3 or higher is required."
}

# Find and start the WinRM service.
Write-Verbose "Verifying WinRM service."
If (!(Get-Service "WinRM")) {
    Write-ProgressLog "Unable to find the WinRM service."
    Throw "Unable to find the WinRM service."
}
ElseIf ((Get-Service "WinRM").Status -ne "Running") {
    Write-Verbose "Setting WinRM service to start automatically on boot."
    Set-Service -Name "WinRM" -StartupType Automatic
    Write-ProgressLog "Set WinRM service to start automatically on boot."
    Write-Verbose "Starting WinRM service."
    Start-Service -Name "WinRM" -ErrorAction Stop
    Write-ProgressLog "Started WinRM service."

}

# WinRM should be running; check that we have a PS session config.
If (!(Get-PSSessionConfiguration -Verbose:$false) -or (!(Get-ChildItem WSMan:\localhost\Listener))) {
    Write-Verbose "Enabling PS Remoting without checking Network profile."
    Enable-PSRemoting -SkipNetworkProfileCheck -Force -ErrorAction Stop
    Write-ProgressLog "Enabled PS Remoting without checking Network profile."
Else {
    Write-Verbose "PS Remoting is already enabled."
}

# Ensure LocalAccountTokenFilterPolicy is set to 1
# https://github.com/ansible/ansible/issues/42978
$token_path = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
$token_prop_name = "LocalAccountTokenFilterPolicy"
$token_key = Get-Item -Path $token_path
$token_value = $token_key.GetValue($token_prop_name, $null)
if ($token_value -ne 1) {
    Write-Verbose "Setting LocalAccountTOkenFilterPolicy to 1"
    if ($null -ne $token_value) {
        Remove-ItemProperty -Path $token_path -Name $token_prop_name
    }
    New-ItemProperty -Path $token_path -Name $token_prop_name -Value 1 -PropertyType DWORD > $null
}

# Make sure there is a SSL listener
$listeners = Get-ChildItem WSMan:\localhost\Listener
If (!($listeners | Where-Object { $_.Keys -like "TRANSPORT=HTTPS" })) {
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
    Write-ProgressLog "Enabled SSL listener."
}
Else {
    Write-Verbose "SSL listener is already active."

    # Force a new SSL cert on Listener if the $ForceNewSSLCert
    If ($ForceNewSSLCert) {

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

# Remove listeners that run over HTTP
Get-ChildItem -Path WSMan:\localhost\Listener | Where-Object { $_.Keys -contains "Transport=HTTP" } | Remove-Item -Recurse -Force

# Disable basic auth
$basicAuthSetting = Get-ChildItem WSMan:\localhost\Service\Auth | Where-Object { $_.Name -eq "Basic" }
If (($basicAuthSetting.Value) -eq $true) {
    Write-Verbose "Disabling basic auth support."
    Set-Item -Path "WSMan:\localhost\Service\Auth\Basic" -Value $false
    Write-ProgressLog "Disabled basic auth support."
}
Else {
    Write-Verbose "Basic auth is already disabled."
}

# Disable Kerberos auth
$kerberosAuthSetting = Get-ChildItem WSMan:\localhost\Service\Auth | Where-Object { $_.Name -eq "Kerberos" }
If (($kerberosAuthSetting.Value) -eq $true) {
    Write-Verbose "Disabling Kerberos auth support."
    Set-Item -Path "WSMan:\localhost\Service\Auth\Kerberos" -Value $false
    Write-ProgressLog "Disabled Kerberos auth support."
}
Else {
    Write-Verbose "Kerberos auth is already disabled."
}

# Disable Negotiate auth
$negotiateAuthSetting = Get-ChildItem WSMan:\localhost\Service\Auth | Where-Object { $_.Name -eq "Negotiate" }
If (($negotiateAuthSetting.Value) -eq $true) {
    Write-Verbose "Disabling Negotiate auth support."
    Set-Item -Path "WSMan:\localhost\Service\Auth\Negotiate" -Value $false
    Write-ProgressLog "Disabled Negotiate auth support."
}
Else {
    Write-Verbose "Negotiate auth is already disabled."
}

# Disable Certificate auth
$certificateAuthSetting = Get-ChildItem WSMan:\localhost\Service\Auth | Where-Object { $_.Name -eq "Certificate" }
If (($certificateAuthSetting.Value) -eq $true) {
    Write-Verbose "Disabling Certificate auth support."
    Set-Item -Path "WSMan:\localhost\Service\Auth\Certificate" -Value $false
    Write-ProgressLog "Disabled Certificate auth support."
}
Else {
    Write-Verbose "Certificate auth is already disabled."
}

# Disable AllowUnencrypted
$allowUnencryptedSetting = Get-ChildItem WSMan:\localhost\Service | Where-Object { $_.Name -eq "AllowUnencrypted" }
If (($allowUnencryptedSetting.Value) -eq $true) {
    Write-Verbose "Disabling AllowUnencrypted support."
    Set-Item -Path "WSMan:\localhost\Service\AllowUnencrypted" -Value $false
    Write-ProgressLog "Disabled AllowUnencrypted support."
}
Else {
    Write-Verbose "AllowUnencrypted is already disabled."
}

# Disable EnableCompatibilityHttpListener
$enableCompatibilityHttpListenerSetting = Get-ChildItem WSMan:\localhost\Service | Where-Object { $_.Name -eq "EnableCompatibilityHttpListener" }
If (($enableCompatibilityHttpListenerSetting.Value) -eq $true) {
    Write-Verbose "Disabling EnableCompatibilityHttpListener support."
    Set-Item -Path "WSMan:\localhost\Service\EnableCompatibilityHttpListener" -Value $false
    Write-ProgressLog "Disabled EnableCompatibilityHttpListener support."
}
Else {
    Write-Verbose "EnableCompatibilityHttpListener is already disabled."
}

# Disable EnableCompatibilityHttpsListener
$enableCompatibilityHttpsListenerSetting = Get-ChildItem WSMan:\localhost\Service | Where-Object { $_.Name -eq "EnableCompatibilityHttpsListener" }
If (($enableCompatibilityHttpsListenerSetting.Value) -eq $true) {
    Write-Verbose "Disabling EnableCompatibilityHttpsListener support."
    Set-Item -Path "WSMan:\localhost\Service\EnableCompatibilityHttpsListener" -Value $false
    Write-ProgressLog "Disabled EnableCompatibilityHttpsListener support."
}
Else {
    Write-Verbose "EnableCompatibilityHttpsListener is already disabled."
}

# Enable CredSSP auth
$credsspAuthSetting = Get-ChildItem WSMan:\localhost\Service\Auth | Where-Object { $_.Name -eq "CredSSP" }
If (($credsspAuthSetting.Value) -eq $false) {
    Write-Verbose "Enabling CredSSP auth support."
    Enable-WSManCredSSP -role server -Force
    Write-ProgressLog "Enabled CredSSP auth support."
}

# Configure firewall to allow WinRM HTTPS connections.
$fwtest1 = netsh advfirewall firewall show rule name="Allow WinRM HTTPS"
$fwtest2 = netsh advfirewall firewall show rule name="Allow WinRM HTTPS" profile=any
If ($fwtest1.count -lt 5) {
    Write-Verbose "Adding firewall rule to allow WinRM HTTPS."
    netsh advfirewall firewall add rule profile=any name="Allow WinRM HTTPS" dir=in localport=5986 protocol=TCP action=allow
    Write-ProgressLog "Added firewall rule to allow WinRM HTTPS."
}
ElseIf (($fwtest1.count -ge 5) -and ($fwtest2.count -lt 5)) {
    Write-Verbose "Updating firewall rule to allow WinRM HTTPS for any profile."
    netsh advfirewall firewall set rule name="Allow WinRM HTTPS" new profile=any
    Write-ProgressLog "Updated firewall rule to allow WinRM HTTPS for any profile."
}
Else {
    Write-Verbose "Firewall rule already exists to allow WinRM HTTPS."
}

################################################################################
# Test a remoting connection to localhost, which should work
################################################################################

$httpResult = Invoke-Command -ComputerName "localhost" -ScriptBlock { $using:env:COMPUTERNAME } -ErrorVariable httpError -ErrorAction SilentlyContinue
$httpsOptions = New-PSSessionOption -SkipCACheck -SkipCNCheck -SkipRevocationCheck

$httpsResult = New-PSSession -UseSSL -ComputerName "localhost" -SessionOption $httpsOptions -ErrorVariable httpsError -ErrorAction SilentlyContinue

If ($httpResult -and $httpsResult) {
    Write-Verbose "HTTP: Enabled | HTTPS: Enabled"
}
ElseIf ($httpsResult -and !$httpResult) {
    Write-Verbose "HTTP: Disabled | HTTPS: Enabled"
}
ElseIf ($httpResult -and !$httpsResult) {
    Write-Verbose "HTTP: Enabled | HTTPS: Disabled"
}
Else {
    Write-ProgressLog "Unable to establish an HTTP or HTTPS remoting session."
    Throw "Unable to establish an HTTP or HTTPS remoting session."
}
Write-VerboseLog "PS Remoting has been successfully configured for Ansible."
