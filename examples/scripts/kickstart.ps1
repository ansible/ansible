# Powershell script to:
# - upgrade to .NET framework 4.5
# - upgrade a PowerShell 2.0 system to PowerShell 3.0
# - configure WinRM
# - set your firewall rules
# - create an ansible user
# - ask for a reboot once everything has completed
# - runs idempotent
#
# credit to: Matt Martz and Trond Hindenes
#
#   PS > kickstart.ps1
#   it will ask for the ansible password
#   it will ask for a reboot
#   
#   Run as kickstart.ps1 -Verbose to see the output when running.
#
#   Written by Timothy Vandenbrande <timothy.vandenbrande@gmail.com>
#

[CmdletBinding()]

Param (
    [string]$SubjectName = $env:COMPUTERNAME,
    [int]$CertValidityDays = 365,
    $CreateSelfSignedCert = $true,
    [string]$user = "ansible"
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

function download-file
{
	param ([string]$path, [string]$local)
	$client = new-object system.net.WebClient
	$client.Headers.Add("user-agent", "PowerShell")
	$client.downloadfile($path, $local)
}


function create-account ($user, $password, $computer="localhost") {
    if(!$user -or !$password)
    {
        $(Throw 'A value for $user and $password is required.')
    }
	if (LocalUserExist $user) {
		write-verbose "$user already exists"
	} else {
		$objOu = [ADSI]"WinNT://$computer"
		$objUser = $objOU.Create("User", $user)
		$objUser.setpassword($password)
		$objUser.SetInfo()
		$objUser.description = $user
		$objUser.SetInfo()
	}
}

# Powershell function to check for the Local user account...
function LocalUserExist($userName)
{
  $Computer = [ADSI]"WinNT://$Env:COMPUTERNAME,Computer"
  # Local user account creation: 
  $colUsers = ($Computer.psbase.children | Where-Object {$_.psBase.schemaClassName -eq "User"} | Select-Object -expand Name)
  $userFound = $colUsers -contains $userName
  return $userFound
} 

# Powershell to check for the existence of Local group...
function LocalGroupExist($groupName)
{ 
    return [ADSI]::Exists("WinNT://$Env:COMPUTERNAME/$groupName,group")
}

# PS function to create the local group
function CreateLocalGroup($groupName)
{
    $groupExist = LocalGroupExist($groupName)
    if($groupExist -eq $false)
    {
        $Group = $Computer.Create("Group", $groupName)
        $Group.SetInfo()
        $Group.Description = $groupName
        $Group.SetInfo()
    }
    else
    {
        "Group : $groupName already exist."
    }
}

# PS function to check for the group in the local machine...
function CheckGroupMember($groupName,$memberName)
{
    $group = [ADSI]"WinNT://$Env:COMPUTERNAME/$groupName"

    $members = @($group.psbase.Invoke("Members"))
    $memberNames = $members | foreach {$_.GetType().InvokeMember("Name", 'GetProperty', $null, $_, $null)} 

    $memberFound = $memberNames -contains $memberName
    return $memberFound
}

# PS function to add a user to the group...
function AddUserToGroup ($groupName, $userName)
{
    $group = [ADSI]"WinNT://$Env:COMPUTERNAME/$groupName"
    $user = [ADSI]"WinNT://$Env:COMPUTERNAME/$userName"
    $memberExist = CheckGroupMember $groupName $userName
    if($memberExist -eq $false)
    {
        $group = [ADSI]"WinNT://$Env:COMPUTERNAME/$groupName"  
        $user = [ADSI]"WinNT://$Env:COMPUTERNAME/$userName" 
        $group.Add($user.Path)
    }
}

Function Test-RegistryValue 
{
    param(
        [Alias("RegistryPath")]
        [Parameter(Position = 0)]
        [String]$Path
        ,
        [Alias("KeyName")]
        [Parameter(Position = 1)]
        [String]$Name
    )

    process 
    {
        if (Test-Path $Path) 
        {
            $Key = Get-Item -LiteralPath $Path
            if ($Key.GetValue($Name, $null) -ne $null)
            {
                if ($PassThru)
                {
                    Get-ItemProperty $Path $Name
                }       
                else
                {
                    $true
                }
            }
            else
            {
                $false
            }
        }
        else
        {
            $false
        }
    }
}

Function Disable-UAC
{
    $EnableUACRegistryPath = "REGISTRY::HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Policies\System"
    $EnableUACRegistryKeyName = "EnableLUA"
    $UACKeyExists = Test-RegistryValue -RegistryPath $EnableUACRegistryPath -KeyName $EnableUACRegistryKeyName 
    if ($UACKeyExists)
    {
        Set-ItemProperty -Path $EnableUACRegistryPath -Name $EnableUACRegistryKeyName -Value 0
    }
    else
    {
        New-ItemProperty -Path $EnableUACRegistryPath -Name $EnableUACRegistryKeyName -Value 0 -PropertyType "DWord"
    }
}

# Constants
if (!(Test-Path variable:\NET_FW_DISABLED))        { Set-Variable NET_FW_DISABLED        $False }
if (!(Test-Path variable:\NET_FW_ENABLED))         { Set-Variable NET_FW_ENABLED         $True }
if (!(Test-Path variable:\NET_FW_IP_PROTOCOL_TCP)) { Set-Variable NET_FW_IP_PROTOCOL_TCP 6 }
if (!(Test-Path variable:\NET_FW_IP_PROTOCOL_UDP)) { Set-Variable NET_FW_IP_PROTOCOL_UDP 17 }
if (!(Test-Path variable:\NET_FW_PROFILE_DOMAIN))  { Set-Variable NET_FW_PROFILE_DOMAIN  0x1 }
if (!(Test-Path variable:\NET_FW_PROFILE_PRIVATE)) { Set-Variable NET_FW_PROFILE_PRIVATE 0x2 }
if (!(Test-Path variable:\NET_FW_PROFILE_PUBLIC))  { Set-Variable NET_FW_PROFILE_PUBLIC  0x2 }
if (!(Test-Path variable:\NET_FW_PROFILE_ALL))     { Set-Variable NET_FW_PROFILE_ALL     0x7FFFFFFF }

function Enable-FirewallRule([String] $name, [String] $description = "", [ScriptBlock] $filter = { $_.Name = $name }, [ScriptBlock] $createRule = {}) {
    $rules = @($policy.Rules | Where-Object $filter)
    if ($rules.Count -eq 0) {
        $rule = New-Object -com HNetCfg.FWRule
        $rule.Name = $name
        $rule.Description = $description
        $rule.Protocol = $NET_FW_IP_PROTOCOL_TCP
        if ($createRule -ne $null) { $createRule.Invoke($rule) }
        $rule.Enabled = $NET_FW_ENABLED
        $policy.Rules.Add($rule)
        
        Write-Verbose ("Created the rule ""{0}""" -f $rule.Name)
    } elseif (@($rules | Where-Object { $_.Enabled }).Count -eq 0) {
        $rules | Where-Object { !$_.Enabled } | Select-Object -f 1 | ForEach-Object { 
            $_.Enabled = $NET_FW_ENABLED
            Write-Verbose ("Enabled the rule ""{0}""" -f $_.Name)
        }
    } else {
        $rules | Where-Object { $_.Enabled } | ForEach-Object {
            Write-Verbose ("The rule ""{0}"" was already enabled" -f $_.Name)
        }
    }
}

function Remove-FirewallRules([ScriptBlock] $filter = {}) {
    $rules = @($policy.Rules | Where-Object $filter)
    if ($rules.Count -gt 0) {
        $rules | ForEach-Object { Write-Verbose ("Deleting rule: ""{0}""" -f $_.Name); $policy.Rules.Remove($_.Name) }
    } else {
        Write-Verbose "No rules matched the supplied filter"
    }
}

$policy = New-Object -com HNetCfg.FwPolicy2

#endregion

#Start script
$reboot = "FALSE"
if (!(LocalUserExist $user)) {
	$pass = Read-Host 'What is the ansible password?' -AsSecureString
	create-account $user $pass
	Write-Verbose "$user created"
} else {
	Write-Verbose "$user already exists"
}
AddUserToGroup "Remote Desktop Users" $user
AddUserToGroup "Administrators" $user

$localdir = "c:\Syntigo\"
if (!(Test-Path $localdir)) {
	mkdir $localdir
}

Disable-UAC
Set-ExecutionPolicy RemoteSigned -Force
#cd ${env:windir}/system32
Regsvr32 ${env:windir}/system32/WsmAuto.dll /s
Regsvr32 ${env:windir}/system32/WSManMigrationPlugin.dll /s


$ErrorActionPreference = "Stop"

#Detect PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 3)
{
    Write-Error "PowerShell/Windows Management Framework needs to be updated to 3 or higher."
	$reboot = "TRUE"
	$powershellpath = "C:\powershell"


	if (!(test-path $powershellpath))
	{
		New-Item -ItemType directory -Path $powershellpath
	}

	Get-ChildItem 'HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP' -recurse | Get-ItemProperty -name Version -EA 0 | Select Version  | ft -HideTableHeaders | Out-String -OutVariable version  > $null
	$version=$version[0].split(".")
	Write-Verbose "Installed .Net framework: $version"
	
	if ($version[0] -lt 4)
	{
		Write-Verbose "Upgrading .NET framework"
		$DownloadUrl = "http://download.microsoft.com/download/1/6/7/167F0D79-9317-48AE-AEDB-17120579F8E2/NDP451-KB2858728-x86-x64-AllOS-ENU.exe"
		$FileName = $DownLoadUrl.Split('/')[-1]
		download-file $downloadurl "$powershellpath\$filename"
		Start-Process "$powershellpath\$filename" -ArgumentList  "/q /norestart"  -NoNewWindow -Wait
	}

	$osminor = [environment]::OSVersion.Version.Minor

	if ($osminor -eq 1)
	{
		$DownloadUrl = "http://download.microsoft.com/download/E/7/6/E76850B8-DA6E-4FF5-8CCE-A24FC513FD16/Windows6.1-KB2506143-x64.msu"
	}
	elseif ($osminor -eq 0)
	{
		$DownloadUrl = "http://download.microsoft.com/download/E/7/6/E76850B8-DA6E-4FF5-8CCE-A24FC513FD16/Windows6.0-KB2506146-x64.msu"
	}

	$FileName = $DownLoadUrl.Split('/')[-1]
	download-file $downloadurl "$powershellpath\$filename"

	Write-Verbose "Upgrading Powershell"
	#Start-Process -FilePath "$powershellpath\$filename" -ArgumentList  "/quiet /norestart"  -Wait
	Start-Process "wusa.exe" -ArgumentList "$powershellpath\$filename /quiet /norestart"  -Wait
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
 
#Firewall
Enable-FirewallRule "Enable WinRM HTTPS" `
	-filter { $_.Enabled -and (	$_.LocalPorts -eq "5986" -or $_.Name -eq "Enable WinRM HTTPS" ) } `
	-createRule { param($rule) $rule.Protocol = $NET_FW_IP_PROTOCOL_TCP; $rule.LocalPorts = "5986"; $rule.RemoteAddresses = "10.15.12.76" }

Write-Verbose "PS Remoting successfully setup for Ansible"

if (!($reboot)) {
	Write-Verbose "a reboot is required."
	$retval = Read-Host 'Do you wish to reboot? [y/N]'
	if ( ($retval -eq 'y') -or ($retval -eq 'yes') ) 
	{
		Restart-Computer
	}
}

