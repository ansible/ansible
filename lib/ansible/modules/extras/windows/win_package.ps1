#!powershell
# (c) 2014, Trond Hindenes <trond@hindenes.com>, and others
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

#region DSC

data LocalizedData
{
    # culture="en-US"
    # TODO: Support WhatIf
    ConvertFrom-StringData @'
InvalidIdentifyingNumber=The specified IdentifyingNumber ({0}) is not a valid Guid
InvalidPath=The specified Path ({0}) is not in a valid format. Valid formats are local paths, UNC, and HTTP
InvalidNameOrId=The specified Name ({0}) and IdentifyingNumber ({1}) do not match Name ({2}) and IdentifyingNumber ({3}) in the MSI file
NeedsMoreInfo=Either Name or ProductId is required
InvalidBinaryType=The specified Path ({0}) does not appear to specify an EXE or MSI file and as such is not supported
CouldNotOpenLog=The specified LogPath ({0}) could not be opened
CouldNotStartProcess=The process {0} could not be started
UnexpectedReturnCode=The return code {0} was not expected. Configuration is likely not correct
PathDoesNotExist=The given Path ({0}) could not be found
CouldNotOpenDestFile=Could not open the file {0} for writing
CouldNotGetHttpStream=Could not get the {0} stream for file {1}
ErrorCopyingDataToFile=Encountered error while writing the contents of {0} to {1}
PackageConfigurationComplete=Package configuration finished
PackageConfigurationStarting=Package configuration starting
InstalledPackage=Installed package
UninstalledPackage=Uninstalled package
NoChangeRequired=Package found in desired state, no action required
RemoveExistingLogFile=Remove existing log file
CreateLogFile=Create log file
MountSharePath=Mount share to get media
DownloadHTTPFile=Download the media over HTTP or HTTPS
StartingProcessMessage=Starting process {0} with arguments {1}
RemoveDownloadedFile=Remove the downloaded file
PackageInstalled=Package has been installed
PackageUninstalled=Package has been uninstalled
MachineRequiresReboot=The machine requires a reboot
PackageDoesNotAppearInstalled=The package {0} is not installed
PackageAppearsInstalled=The package {0} is already installed
PostValidationError=Package from {0} was installed, but the specified ProductId and/or Name does not match package details
'@
}

$Debug = $true
Function Trace-Message
{
    param([string] $Message)
    if($Debug)
    {
        Write-Verbose $Message
    }
}

$CacheLocation = "$env:ProgramData\Microsoft\Windows\PowerShell\Configuration\BuiltinProvCache\MSFT_PackageResource"

Function Throw-InvalidArgumentException
{
    param(
        [string] $Message,
        [string] $ParamName
    )
    
    $exception = new-object System.ArgumentException $Message,$ParamName
    $errorRecord = New-Object System.Management.Automation.ErrorRecord $exception,$ParamName,"InvalidArgument",$null
    throw $errorRecord
}

Function Throw-InvalidNameOrIdException
{
    param(
        [string] $Message
    )
    
    $exception = new-object System.ArgumentException $Message
    $errorRecord = New-Object System.Management.Automation.ErrorRecord $exception,"NameOrIdNotInMSI","InvalidArgument",$null
    throw $errorRecord
}

Function Throw-TerminatingError
{
    param(
        [string] $Message,
        [System.Management.Automation.ErrorRecord] $ErrorRecord
    )
    
    $exception = new-object "System.InvalidOperationException" $Message,$ErrorRecord.Exception
    $errorRecord = New-Object System.Management.Automation.ErrorRecord $exception,"MachineStateIncorrect","InvalidOperation",$null
    throw $errorRecord
}

Function Get-RegistryValueIgnoreError
{
    param
    (
        [parameter(Mandatory = $true)]
        [Microsoft.Win32.RegistryHive]
        $RegistryHive,

        [parameter(Mandatory = $true)]
        [System.String]
        $Key,

        [parameter(Mandatory = $true)]
        [System.String]
        $Value,

        [parameter(Mandatory = $true)]
        [Microsoft.Win32.RegistryView]
        $RegistryView
    )

    try
    {
        $baseKey = [Microsoft.Win32.RegistryKey]::OpenBaseKey($RegistryHive, $RegistryView)
        $subKey =  $baseKey.OpenSubKey($Key)
        if($subKey -ne $null)
        {
            return $subKey.GetValue($Value)
        }
    }
    catch
    {        
        $exceptionText = ($_ | Out-String).Trim()
        Write-Verbose "Exception occured in Get-RegistryValueIgnoreError: $exceptionText"        
    }
    return $null
}

Function Validate-StandardArguments
{
    param(
        $Path,
        $ProductId,
        $Name
    )
    
    Trace-Message "Validate-StandardArguments, Path was $Path"
    $uri = $null
    try
    {
        $uri = [uri] $Path
    }
    catch
    {
        Throw-InvalidArgumentException ($LocalizedData.InvalidPath -f $Path) "Path"
    }
    
    if(-not @("file", "http", "https") -contains $uri.Scheme)
    {
        Trace-Message "The uri scheme was $uri.Scheme"
        Throw-InvalidArgumentException ($LocalizedData.InvalidPath -f $Path) "Path"
    }
    
    $pathExt = [System.IO.Path]::GetExtension($Path)
    Trace-Message "The path extension was $pathExt"
    if(-not @(".msi",".exe") -contains $pathExt.ToLower())
    {
        Throw-InvalidArgumentException ($LocalizedData.InvalidBinaryType -f $Path) "Path"
    }
    
    $identifyingNumber = $null
    if(-not $Name -and -not $ProductId)
    {
        #It's a tossup here which argument to blame, so just pick ProductId to encourage customers to use the most efficient version
        Throw-InvalidArgumentException ($LocalizedData.NeedsMoreInfo -f $Path) "ProductId"
    }
    elseif($ProductId)
    {
        try
        {
            Trace-Message "Parsing $ProductId as an identifyingNumber"
            $identifyingNumber = "{{{0}}}" -f [Guid]::Parse($ProductId).ToString().ToUpper()
            Trace-Message "Parsed $ProductId as $identifyingNumber"
        }
        catch
        {
            Throw-InvalidArgumentException ($LocalizedData.InvalidIdentifyingNumber -f $ProductId) $ProductId
        }
    }
    
    return $uri, $identifyingNumber
}

Function Get-ProductEntry
{
    param
    (
        [string] $Name,
        [string] $IdentifyingNumber,
        [string] $InstalledCheckRegKey,
        [string] $InstalledCheckRegValueName,
        [string] $InstalledCheckRegValueData
    )
    
    $uninstallKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    $uninstallKeyWow64 = "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    
    if($IdentifyingNumber)
    {
        $keyLocation = "$uninstallKey\$identifyingNumber"
        $item = Get-Item $keyLocation -EA SilentlyContinue
        if(-not $item)
        {
            $keyLocation = "$uninstallKeyWow64\$identifyingNumber"
            $item = Get-Item $keyLocation -EA SilentlyContinue
        }

        return $item
    }
    
    foreach($item in (Get-ChildItem -EA Ignore $uninstallKey, $uninstallKeyWow64))
    {
        if($Name -eq (Get-LocalizableRegKeyValue $item "DisplayName"))
        {
            return $item
        }
    }
    
    if ($InstalledCheckRegKey -and $InstalledCheckRegValueName -and $InstalledCheckRegValueData)
    {
        $installValue = $null

        #if 64bit OS, check 64bit registry view first
        if ((Get-WmiObject -Class Win32_OperatingSystem -ComputerName "localhost" -ea 0).OSArchitecture -eq '64-bit') 
        {
            $installValue = Get-RegistryValueIgnoreError LocalMachine "$InstalledCheckRegKey" "$InstalledCheckRegValueName" Registry64
        }
        
        if($installValue -eq $null)
        {
            $installValue = Get-RegistryValueIgnoreError LocalMachine "$InstalledCheckRegKey" "$InstalledCheckRegValueName" Registry32
        }

        if($installValue)
        {
            if($InstalledCheckRegValueData -and $installValue -eq $InstalledCheckRegValueData)
            {
                return @{
                    Installed = $true
                }
            }
        } 
    }

    return $null
}

function Test-TargetResource 
{
    param
    (
        [ValidateSet("Present", "Absent")]
        [string] $Ensure = "Present",
        
        [parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string] $Name,
        
        [parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string] $Path,
        
        [parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string] $ProductId,
        
        [string] $Arguments,
        
        [pscredential] $Credential,
        
        [int[]] $ReturnCode,
        
        [string] $LogPath,

        [pscredential] $RunAsCredential,

        [string] $InstalledCheckRegKey,

        [string] $InstalledCheckRegValueName,

        [string] $InstalledCheckRegValueData
    )
    
    $uri, $identifyingNumber = Validate-StandardArguments $Path $ProductId $Name
    $product = Get-ProductEntry $Name $identifyingNumber $InstalledCheckRegKey $InstalledCheckRegValueName $InstalledCheckRegValueData
    Trace-Message "Ensure is $Ensure"
    if($product)
    {
        Trace-Message "product found"
    }
    else
    {
        Trace-Message "product installation cannot be determined"
    }
    Trace-Message ("product as boolean is {0}" -f [boolean]$product)
    $res = ($product -ne $null -and $Ensure -eq "Present") -or ($product -eq $null -and $Ensure -eq "Absent")

    # install registry test overrides the product id test and there is no true product information
    # when doing a lookup via registry key
    if ($product -and $InstalledCheckRegKey -and $InstalledCheckRegValueName -and $InstalledCheckRegValueData)
    {
        Write-Verbose ($LocalizedData.PackageAppearsInstalled -f $Name)
    }
    else
    {
        if ($product -ne $null)
        {
            $name = Get-LocalizableRegKeyValue $product "DisplayName"
            Write-Verbose ($LocalizedData.PackageAppearsInstalled -f $name)
        }
        else
        {   
            $displayName = $null
            if($Name)
            {
                $displayName = $Name
            }
            else
            {
                $displayName = $ProductId
            }
        
            Write-Verbose ($LocalizedData.PackageDoesNotAppearInstalled -f $displayName)
        }

    }
    
    return $res
}

function Get-LocalizableRegKeyValue
{
    param(
        [object] $RegKey,
        [string] $ValueName
    )
    
    $res = $RegKey.GetValue("{0}_Localized" -f $ValueName)
    if(-not $res)
    {
        $res = $RegKey.GetValue($ValueName)
    }
    
    return $res
}

function Get-TargetResource
{
    param
    (
        [parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string] $Name,
        
        [parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string] $Path,
        
        [parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string] $ProductId,

        [string] $InstalledCheckRegKey,

        [string] $InstalledCheckRegValueName,

        [string] $InstalledCheckRegValueData
    )
    
    #If the user gave the ProductId then we derive $identifyingNumber
    $uri, $identifyingNumber = Validate-StandardArguments $Path $ProductId $Name
    
    $localMsi = $uri.IsFile -and -not $uri.IsUnc
    
    $product = Get-ProductEntry $Name $identifyingNumber $InstalledCheckRegKey $InstalledCheckRegValueName $InstalledCheckRegValueData
    
    if(-not $product)
    {
        return @{
            Ensure = "Absent"
            Name = $Name
            ProductId = $identifyingNumber
            Installed = $false
            InstalledCheckRegKey = $InstalledCheckRegKey
            InstalledCheckRegValueName = $InstalledCheckRegValueName
            InstalledCheckRegValueData = $InstalledCheckRegValueData
        }
    }
    
    if ($InstalledCheckRegKey -and $InstalledCheckRegValueName -and $InstalledCheckRegValueData)
    {
        return @{
            Ensure = "Present"
            Name = $Name
            ProductId = $identifyingNumber
            Installed = $true
            InstalledCheckRegKey = $InstalledCheckRegKey
            InstalledCheckRegValueName = $InstalledCheckRegValueName
            InstalledCheckRegValueData = $InstalledCheckRegValueData
        }
    }

    #$identifyingNumber can still be null here (e.g. remote MSI with Name specified, local EXE)
    #If the user gave a ProductId just pass it through, otherwise fill it from the product
    if(-not $identifyingNumber)
    {
        $identifyingNumber = Split-Path -Leaf $product.Name
    }
    
    $date = $product.GetValue("InstallDate")
    if($date)
    {
        try
        {
            $date = "{0:d}" -f [DateTime]::ParseExact($date, "yyyyMMdd",[System.Globalization.CultureInfo]::CurrentCulture).Date
        }
        catch
        {
            $date = $null
        }
    }
    
    $publisher = Get-LocalizableRegKeyValue $product "Publisher"
    $size = $product.GetValue("EstimatedSize")
    if($size)
    {
        $size = $size/1024
    }
    
    $version = $product.GetValue("DisplayVersion")
    $description = $product.GetValue("Comments")
    $name = Get-LocalizableRegKeyValue $product "DisplayName"
    return @{
        Ensure = "Present"
        Name = $name
        Path = $Path
        InstalledOn = $date
        ProductId = $identifyingNumber
        Size = $size
        Installed = $true
        Version = $version
        PackageDescription = $description
        Publisher = $publisher
    }
}

Function Get-MsiTools
{
    if($script:MsiTools)
    {
        return $script:MsiTools
    }
    
    $sig = @'
    [DllImport("msi.dll", CharSet = CharSet.Unicode, PreserveSig = true, SetLastError = true, ExactSpelling = true)]
    private static extern UInt32 MsiOpenPackageW(string szPackagePath, out IntPtr hProduct);

    [DllImport("msi.dll", CharSet = CharSet.Unicode, PreserveSig = true, SetLastError = true, ExactSpelling = true)]
    private static extern uint MsiCloseHandle(IntPtr hAny);

    [DllImport("msi.dll", CharSet = CharSet.Unicode, PreserveSig = true, SetLastError = true, ExactSpelling = true)]
    private static extern uint MsiGetPropertyW(IntPtr hAny, string name, StringBuilder buffer, ref int bufferLength);

    private static string GetPackageProperty(string msi, string property)
    {
        IntPtr MsiHandle = IntPtr.Zero;
        try
        {
            var res = MsiOpenPackageW(msi, out MsiHandle);
            if (res != 0)
            {
                return null;
            }
            
            int length = 256;
            var buffer = new StringBuilder(length);
            res = MsiGetPropertyW(MsiHandle, property, buffer, ref length);
            return buffer.ToString();
        }
        finally
        {
            if (MsiHandle != IntPtr.Zero)
            {
                MsiCloseHandle(MsiHandle);
            }
        }
    }
    public static string GetProductCode(string msi)
    {
        return GetPackageProperty(msi, "ProductCode");
    }
    
    public static string GetProductName(string msi)
    {
        return GetPackageProperty(msi, "ProductName");
    }
'@
    $script:MsiTools = Add-Type -PassThru -Namespace Microsoft.Windows.DesiredStateConfiguration.PackageResource `
        -Name MsiTools -Using System.Text -MemberDefinition $sig
    return $script:MsiTools
}


Function Get-MsiProductEntry
{
    param
    (
        [string] $Path
    )

    if(-not (Test-Path -PathType Leaf $Path) -and ($fileExtension -ne ".msi"))
    {
        Throw-TerminatingError ($LocalizedData.PathDoesNotExist -f $Path)
    }
    
    $tools = Get-MsiTools

    $pn = $tools::GetProductName($Path)

    $pc = $tools::GetProductCode($Path)

    return $pn,$pc
}


function Set-TargetResource 
{
    [CmdletBinding(SupportsShouldProcess=$true)]
    param
    (
        [ValidateSet("Present", "Absent")]
        [string] $Ensure = "Present",
        
        [parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string] $Name,
        
        [parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string] $Path,
        
        [parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string] $ProductId,
        
        [string] $Arguments,
        
        [pscredential] $Credential,
        
        [int[]] $ReturnCode,
        
        [string] $LogPath,

        [pscredential] $RunAsCredential,

        [string] $InstalledCheckRegKey,

        [string] $InstalledCheckRegValueName,

        [string] $InstalledCheckRegValueData
    )
    
    $ErrorActionPreference = "Stop"
    
    if((Test-TargetResource -Ensure $Ensure -Name $Name -Path $Path -ProductId $ProductId `
        -InstalledCheckRegKey $InstalledCheckRegKey -InstalledCheckRegValueName $InstalledCheckRegValueName `
        -InstalledCheckRegValueData $InstalledCheckRegValueData))
    {
        return
    }

    $uri, $identifyingNumber = Validate-StandardArguments $Path $ProductId $Name
    
    #Path gets overwritten in the download code path. Retain the user's original Path in case the install succeeded
    #but the named package wasn't present on the system afterward so we can give a better message
    $OrigPath = $Path
    
    Write-Verbose $LocalizedData.PackageConfigurationStarting
    if(-not $ReturnCode)
    {
        $ReturnCode = @(0)
    }
    
    $logStream = $null
    $psdrive = $null
    $downloadedFileName = $null
    try
    {
        $fileExtension = [System.IO.Path]::GetExtension($Path).ToLower()
        if($LogPath)
        {
            try
            {
                if($fileExtension -eq ".msi")
                {
                    #We want to pre-verify the path exists and is writable ahead of time
                    #even in the MSI case, as detecting WHY the MSI log doesn't exist would
                    #be rather problematic for the user
                    if((Test-Path $LogPath) -and $PSCmdlet.ShouldProcess($LocalizedData.RemoveExistingLogFile,$null,$null))
                    {
                        rm $LogPath
                    }
                    
                    if($PSCmdlet.ShouldProcess($LocalizedData.CreateLogFile, $null, $null))
                    {
                        New-Item -Type File $LogPath | Out-Null
                    }
                }
                elseif($PSCmdlet.ShouldProcess($LocalizedData.CreateLogFile, $null, $null))
                {
                    $logStream = new-object "System.IO.StreamWriter" $LogPath,$false
                }
            }
            catch
            {
                Throw-TerminatingError ($LocalizedData.CouldNotOpenLog -f $LogPath) $_
            }
        }
        
        #Download or mount file as necessary
        if(-not ($fileExtension -eq ".msi" -and $Ensure -eq "Absent"))
        {
            if($uri.IsUnc -and $PSCmdlet.ShouldProcess($LocalizedData.MountSharePath, $null, $null))
            {
                $psdriveArgs = @{Name=([guid]::NewGuid());PSProvider="FileSystem";Root=(Split-Path $uri.LocalPath)}
                if($Credential)
                {
                    #We need to optionally include these and then splat the hash otherwise
                    #we pass a null for Credential which causes the cmdlet to pop a dialog up
                    $psdriveArgs["Credential"] = $Credential
                }
                
                $psdrive = New-PSDrive @psdriveArgs
                $Path = Join-Path $psdrive.Root (Split-Path -Leaf $uri.LocalPath) #Necessary?
            }
            elseif(@("http", "https") -contains $uri.Scheme -and $Ensure -eq "Present" -and $PSCmdlet.ShouldProcess($LocalizedData.DownloadHTTPFile, $null, $null))
            {
                $scheme = $uri.Scheme
                $outStream = $null
                $responseStream = $null

                try
                {
                    Trace-Message "Creating cache location"

                    if(-not (Test-Path -PathType Container $CacheLocation))
                    {
                        mkdir $CacheLocation | Out-Null
                    }
                
                    $destName = Join-Path $CacheLocation (Split-Path -Leaf $uri.LocalPath)
                
                    Trace-Message "Need to download file from $scheme, destination will be $destName"

                    try
                    {
                        Trace-Message "Creating the destination cache file"
                        $outStream = New-Object System.IO.FileStream $destName, "Create"
                    }
                    catch
                    {
                        #Should never happen since we own the cache directory
                        Throw-TerminatingError ($LocalizedData.CouldNotOpenDestFile -f $destName) $_
                    }

                    try
                    {
                        Trace-Message "Creating the $scheme stream"
                        $request = [System.Net.WebRequest]::Create($uri)
                        Trace-Message "Setting default credential"
                        $request.Credentials = [System.Net.CredentialCache]::DefaultCredentials
                        if ($scheme -eq "http")
                        {
                            Trace-Message "Setting authentication level"
                            # default value is MutualAuthRequested, which applies to https scheme
                            $request.AuthenticationLevel = [System.Net.Security.AuthenticationLevel]::None                            
                        }
                        if ($scheme -eq "https")
                        {
                            Trace-Message "Ignoring bad certificates"
                            $request.ServerCertificateValidationCallBack = {$true}
                        }
                        Trace-Message "Getting the $scheme response stream"
                        $responseStream = (([System.Net.HttpWebRequest]$request).GetResponse()).GetResponseStream()
                    }
                    catch
                    {
                         Trace-Message ("Error: " + ($_ | Out-String))
                         Throw-TerminatingError ($LocalizedData.CouldNotGetHttpStream -f $scheme, $Path) $_
                    }

                    try
                    {
                        Trace-Message "Copying the $scheme stream bytes to the disk cache"
                        $responseStream.CopyTo($outStream)
                        $responseStream.Flush()
                        $outStream.Flush()
                    }
                    catch
                    {
                        Throw-TerminatingError ($LocalizedData.ErrorCopyingDataToFile -f $Path,$destName) $_
                    }
                }
                finally
                {
                    if($outStream)
                    {
                        $outStream.Close()
                    }
                    
                    if($responseStream)
                    {
                        $responseStream.Close()
                    }
                }
                Trace-Message "Redirecting package path to cache file location"
                $Path = $downloadedFileName = $destName
            }
        }
        
        #At this point the Path ought to be valid unless it's an MSI uninstall case
        if(-not (Test-Path -PathType Leaf $Path) -and -not ($Ensure -eq "Absent" -and $fileExtension -eq ".msi"))
        {
            Throw-TerminatingError ($LocalizedData.PathDoesNotExist -f $Path)
        }
        
        $startInfo = New-Object System.Diagnostics.ProcessStartInfo
        $startInfo.UseShellExecute = $false #Necessary for I/O redirection and just generally a good idea
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $startInfo
        $errLogPath = $LogPath + ".err" #Concept only, will never touch disk
        if($fileExtension -eq ".msi")
        {
            $startInfo.FileName = "$env:windir\system32\msiexec.exe"
            if($Ensure -eq "Present")
            {
                # check if Msi package contains the ProductName and Code specified

                $pName,$pCode = Get-MsiProductEntry -Path $Path

                if (
                    ( (-not [String]::IsNullOrEmpty($Name)) -and ($pName -ne $Name))  `
                -or ( (-not [String]::IsNullOrEmpty($identifyingNumber)) -and ($identifyingNumber -ne $pCode))
                )
                {
                    Throw-InvalidNameOrIdException ($LocalizedData.InvalidNameOrId -f $Name,$identifyingNumber,$pName,$pCode)
                }

                $startInfo.Arguments = '/i "{0}"' -f $Path
            }
            else
            {
                $product = Get-ProductEntry $Name $identifyingNumber
                $id = Split-Path -Leaf $product.Name #We may have used the Name earlier, now we need the actual ID
                $startInfo.Arguments = ("/x{0}" -f $id)
            }
            
            if($LogPath)
            {
                $startInfo.Arguments += ' /log "{0}"' -f $LogPath
            }
            
            $startInfo.Arguments += " /quiet"
            
            if($Arguments)
            {
                $startInfo.Arguments += " " + $Arguments
            }
        }
        else #EXE
        {
            Trace-Message "The binary is an EXE"
            $startInfo.FileName = $Path
            $startInfo.Arguments = $Arguments
            if($LogPath)
            {
                Trace-Message "User has requested logging, need to attach event handlers to the process"
                $startInfo.RedirectStandardError = $true
                $startInfo.RedirectStandardOutput = $true
                Register-ObjectEvent -InputObject $process -EventName "OutputDataReceived" -SourceIdentifier $LogPath
                Register-ObjectEvent -InputObject $process -EventName "ErrorDataReceived" -SourceIdentifier $errLogPath
            }
        }
        
        Trace-Message ("Starting {0} with {1}" -f $startInfo.FileName, $startInfo.Arguments)
        
        if($PSCmdlet.ShouldProcess(($LocalizedData.StartingProcessMessage -f $startInfo.FileName, $startInfo.Arguments), $null, $null))
        {
            try
            {
                $exitCode = 0

                if($PSBoundParameters.ContainsKey("RunAsCredential"))
                {
                    CallPInvoke
                    [Source.NativeMethods]::CreateProcessAsUser("""" + $startInfo.FileName + """ " + $startInfo.Arguments, `
                        $RunAsCredential.GetNetworkCredential().Domain, $RunAsCredential.GetNetworkCredential().UserName, `
                        $RunAsCredential.GetNetworkCredential().Password, [ref] $exitCode)
                }
                else
                {
                    $process.Start() | Out-Null

                    if($logStream) #Identical to $fileExtension -eq ".exe" -and $logPath
                    {
                        $process.BeginOutputReadLine();
                        $process.BeginErrorReadLine();
                    }
            
                    $process.WaitForExit()

                    if($process)
                    {
                        $exitCode = $process.ExitCode
                    }
                }
            }
            catch
            {
                Throw-TerminatingError ($LocalizedData.CouldNotStartProcess -f $Path) $_
            }

            
            if($logStream)
            {
                #We have to re-mux these since they appear to us as different streams
                #The underlying Win32 APIs prevent this problem, as would constructing a script
                #on the fly and executing it, but the former is highly problematic from PowerShell
                #and the latter doesn't let us get the return code for UI-based EXEs
                $outputEvents = Get-Event -SourceIdentifier $LogPath
                $errorEvents = Get-Event -SourceIdentifier $errLogPath
                $masterEvents = @() + $outputEvents + $errorEvents
                $masterEvents = $masterEvents | Sort-Object -Property TimeGenerated
                
                foreach($event in $masterEvents)
                {
                    $logStream.Write($event.SourceEventArgs.Data);
                }
                
                Remove-Event -SourceIdentifier $LogPath
                Remove-Event -SourceIdentifier $errLogPath
            }
            
            if(-not ($ReturnCode -contains $exitCode))
            {
                Throw-TerminatingError ($LocalizedData.UnexpectedReturnCode -f $exitCode.ToString())
            }
        }
    }
    finally
    {
        if($psdrive)
        {
            Remove-PSDrive -Force $psdrive
        }
        
        if($logStream)
        {
            $logStream.Dispose()
        }
    }
    
    if($downloadedFileName -and $PSCmdlet.ShouldProcess($LocalizedData.RemoveDownloadedFile, $null, $null))
    {
        #This is deliberately not in the Finally block. We want to leave the downloaded file on disk
        #in the error case as a debugging aid for the user
        rm $downloadedFileName
    }
    
    $operationString = $LocalizedData.PackageUninstalled
    if($Ensure -eq "Present")
    {
        $operationString = $LocalizedData.PackageInstalled
    }
    
    # Check if reboot is required, if so notify CA. The MSFT_ServerManagerTasks provider is missing on client SKUs
    $featureData = invoke-wmimethod -EA Ignore -Name GetServerFeature -namespace root\microsoft\windows\servermanager -Class MSFT_ServerManagerTasks
    $regData = Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" "PendingFileRenameOperations" -EA Ignore
    if(($featureData -and $featureData.RequiresReboot) -or $regData)
    {
        Write-Verbose $LocalizedData.MachineRequiresReboot
        $global:DSCMachineStatus = 1
    }
    
    if($Ensure -eq "Present")
    {
        $productEntry = Get-ProductEntry $Name $identifyingNumber $InstalledCheckRegKey $InstalledCheckRegValueName $InstalledCheckRegValueData
        if(-not $productEntry)
        {
            Throw-TerminatingError ($LocalizedData.PostValidationError -f $OrigPath)
        }
    }
    
    Write-Verbose $operationString
    Write-Verbose $LocalizedData.PackageConfigurationComplete
}

function CallPInvoke
{
$script:ProgramSource = @"
using System;
using System.Collections.Generic;
using System.Text;
using System.Security;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.Security.Principal;
using System.ComponentModel;
using System.IO;

namespace Source
{
    [SuppressUnmanagedCodeSecurity]
    public static class NativeMethods
    {
        //The following structs and enums are used by the various Win32 API's that are used in the code below
        
        [StructLayout(LayoutKind.Sequential)]
        public struct STARTUPINFO
        {
            public Int32 cb;
            public string lpReserved;
            public string lpDesktop;
            public string lpTitle;
            public Int32 dwX;
            public Int32 dwY;
            public Int32 dwXSize;
            public Int32 dwXCountChars;
            public Int32 dwYCountChars;
            public Int32 dwFillAttribute;
            public Int32 dwFlags;
            public Int16 wShowWindow;
            public Int16 cbReserved2;
            public IntPtr lpReserved2;
            public IntPtr hStdInput;
            public IntPtr hStdOutput;
            public IntPtr hStdError;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct PROCESS_INFORMATION
        {
            public IntPtr hProcess;
            public IntPtr hThread;
            public Int32 dwProcessID;
            public Int32 dwThreadID;
        }

        [Flags]
        public enum LogonType
        {
            LOGON32_LOGON_INTERACTIVE = 2,
            LOGON32_LOGON_NETWORK = 3,
            LOGON32_LOGON_BATCH = 4,
            LOGON32_LOGON_SERVICE = 5,
            LOGON32_LOGON_UNLOCK = 7,
            LOGON32_LOGON_NETWORK_CLEARTEXT = 8,
            LOGON32_LOGON_NEW_CREDENTIALS = 9
        }

        [Flags]
        public enum LogonProvider
        {
            LOGON32_PROVIDER_DEFAULT = 0,
            LOGON32_PROVIDER_WINNT35,
            LOGON32_PROVIDER_WINNT40,
            LOGON32_PROVIDER_WINNT50
        }
        [StructLayout(LayoutKind.Sequential)]
        public struct SECURITY_ATTRIBUTES
        {
            public Int32 Length;
            public IntPtr lpSecurityDescriptor;
            public bool bInheritHandle;
        }

        public enum SECURITY_IMPERSONATION_LEVEL
        {
            SecurityAnonymous,
            SecurityIdentification,
            SecurityImpersonation,
            SecurityDelegation
        }

        public enum TOKEN_TYPE
        {
            TokenPrimary = 1,
            TokenImpersonation
        }

        [StructLayout(LayoutKind.Sequential, Pack = 1)]
        internal struct TokPriv1Luid
        {
            public int Count;
            public long Luid;
            public int Attr;
        }

        public const int GENERIC_ALL_ACCESS = 0x10000000;
        public const int CREATE_NO_WINDOW = 0x08000000;
        internal const int SE_PRIVILEGE_ENABLED = 0x00000002;
        internal const int TOKEN_QUERY = 0x00000008;
        internal const int TOKEN_ADJUST_PRIVILEGES = 0x00000020;
        internal const string SE_INCRASE_QUOTA = "SeIncreaseQuotaPrivilege";

        [DllImport("kernel32.dll",
              EntryPoint = "CloseHandle", SetLastError = true,
              CharSet = CharSet.Auto, CallingConvention = CallingConvention.StdCall)]
        public static extern bool CloseHandle(IntPtr handle);

        [DllImport("advapi32.dll",
              EntryPoint = "CreateProcessAsUser", SetLastError = true,
              CharSet = CharSet.Ansi, CallingConvention = CallingConvention.StdCall)]
        public static extern bool CreateProcessAsUser(
            IntPtr hToken, 
            string lpApplicationName, 
            string lpCommandLine,
            ref SECURITY_ATTRIBUTES lpProcessAttributes, 
            ref SECURITY_ATTRIBUTES lpThreadAttributes,
            bool bInheritHandle, 
            Int32 dwCreationFlags, 
            IntPtr lpEnvrionment,
            string lpCurrentDirectory, 
            ref STARTUPINFO lpStartupInfo,
            ref PROCESS_INFORMATION lpProcessInformation
            );

        [DllImport("advapi32.dll", EntryPoint = "DuplicateTokenEx")]
        public static extern bool DuplicateTokenEx(
            IntPtr hExistingToken, 
            Int32 dwDesiredAccess,
            ref SECURITY_ATTRIBUTES lpThreadAttributes,
            Int32 ImpersonationLevel, 
            Int32 dwTokenType,
            ref IntPtr phNewToken
            );

        [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        public static extern Boolean LogonUser(
            String lpszUserName,
            String lpszDomain,
            String lpszPassword,
            LogonType dwLogonType,
            LogonProvider dwLogonProvider,
            out IntPtr phToken
            );

        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        internal static extern bool AdjustTokenPrivileges(
            IntPtr htok, 
            bool disall,
            ref TokPriv1Luid newst, 
            int len, 
            IntPtr prev, 
            IntPtr relen
            );

        [DllImport("kernel32.dll", ExactSpelling = true)]
        internal static extern IntPtr GetCurrentProcess();

        [DllImport("advapi32.dll", ExactSpelling = true, SetLastError = true)]
        internal static extern bool OpenProcessToken(
            IntPtr h, 
            int acc, 
            ref IntPtr phtok
            );

        [DllImport("kernel32.dll", ExactSpelling = true)]
        internal static extern int WaitForSingleObject(
            IntPtr h, 
            int milliseconds
            );

        [DllImport("kernel32.dll", ExactSpelling = true)]
        internal static extern bool GetExitCodeProcess(
            IntPtr h, 
            out int exitcode
            );

        [DllImport("advapi32.dll", SetLastError = true)]
        internal static extern bool LookupPrivilegeValue(
            string host, 
            string name,
            ref long pluid
            );

        public static void CreateProcessAsUser(string strCommand, string strDomain, string strName, string strPassword, ref int ExitCode )
        {
            var hToken = IntPtr.Zero;
            var hDupedToken = IntPtr.Zero;
            TokPriv1Luid tp;
            var pi = new PROCESS_INFORMATION();
            var sa = new SECURITY_ATTRIBUTES();
            sa.Length = Marshal.SizeOf(sa);
            Boolean bResult = false;
            try
            {
                bResult = LogonUser(
                    strName,
                    strDomain,
                    strPassword,
                    LogonType.LOGON32_LOGON_BATCH,
                    LogonProvider.LOGON32_PROVIDER_DEFAULT,
                    out hToken
                    );
                if (!bResult) 
                { 
                    throw new Win32Exception("Logon error #" + Marshal.GetLastWin32Error().ToString()); 
                }
                IntPtr hproc = GetCurrentProcess();
                IntPtr htok = IntPtr.Zero;
                bResult = OpenProcessToken(
                        hproc, 
                        TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, 
                        ref htok
                    );
                if(!bResult)
                {
                    throw new Win32Exception("Open process token error #" + Marshal.GetLastWin32Error().ToString());
                }
                tp.Count = 1;
                tp.Luid = 0;
                tp.Attr = SE_PRIVILEGE_ENABLED;
                bResult = LookupPrivilegeValue(
                    null, 
                    SE_INCRASE_QUOTA, 
                    ref tp.Luid
                    );
                if(!bResult)
                {
                    throw new Win32Exception("Lookup privilege error #" + Marshal.GetLastWin32Error().ToString());
                }
                bResult = AdjustTokenPrivileges(
                    htok, 
                    false, 
                    ref tp, 
                    0, 
                    IntPtr.Zero, 
                    IntPtr.Zero
                    );
                if(!bResult)
                {
                    throw new Win32Exception("Token elevation error #" + Marshal.GetLastWin32Error().ToString());
                }
                
                bResult = DuplicateTokenEx(
                    hToken,
                    GENERIC_ALL_ACCESS,
                    ref sa,
                    (int)SECURITY_IMPERSONATION_LEVEL.SecurityIdentification,
                    (int)TOKEN_TYPE.TokenPrimary,
                    ref hDupedToken
                    );
                if(!bResult)
                {
                    throw new Win32Exception("Duplicate Token error #" + Marshal.GetLastWin32Error().ToString());
                }
                var si = new STARTUPINFO();
                si.cb = Marshal.SizeOf(si);
                si.lpDesktop = "";
                bResult = CreateProcessAsUser(
                    hDupedToken,
                    null,
                    strCommand,
                    ref sa, 
                    ref sa,
                    false, 
                    0, 
                    IntPtr.Zero,
                    null, 
                    ref si, 
                    ref pi
                    );
                if(!bResult)
                {
                    throw new Win32Exception("Create process as user error #" + Marshal.GetLastWin32Error().ToString());
                }

                int status = WaitForSingleObject(pi.hProcess, -1);
                if(status == -1)
                {
                    throw new Win32Exception("Wait during create process failed user error #" + Marshal.GetLastWin32Error().ToString());
                }

                bResult = GetExitCodeProcess(pi.hProcess, out ExitCode);
                if(!bResult)
                {
                    throw new Win32Exception("Retrieving status error #" + Marshal.GetLastWin32Error().ToString());
                }
            }
            finally
            {
                if (pi.hThread != IntPtr.Zero)
                {
                    CloseHandle(pi.hThread);
                }
                if (pi.hProcess != IntPtr.Zero)
                {
                    CloseHandle(pi.hProcess);
                }
                 if (hDupedToken != IntPtr.Zero)
                {
                    CloseHandle(hDupedToken);
                }
            }
        }
    }
}

"@
            Add-Type -TypeDefinition $ProgramSource -ReferencedAssemblies "System.ServiceProcess"
}

#endregion


$params = Parse-Args $args;
$result = New-Object psobject;
Set-Attr $result "changed" $false;

$path = Get-Attr -obj $params -name path -failifempty $true -resultobj $result
$name = Get-Attr -obj $params -name name -default $path
$productid = Get-Attr -obj $params -name productid -failifempty $true -resultobj $result
$arguments = Get-Attr -obj $params -name arguments
$ensure = Get-Attr -obj $params -name state -default "present"
if (!$ensure)
{
    $ensure = Get-Attr -obj $params -name ensure -default "present"
}
$username = Get-Attr -obj $params -name user_name
$password = Get-Attr -obj $params -name user_password
$return_code = Get-Attr -obj $params -name expected_return_code -default 0

#Construct the DSC param hashtable
$dscparams = @{
    name=$name
    path=$path
    productid = $productid
    arguments = $arguments
    ensure = $ensure
    returncode = $return_code
}

if (($username -ne $null) -and ($password -ne $null))
{
    #Add network credential to the list
    $secpassword = $password | ConvertTo-SecureString -AsPlainText -Force
    $credential = New-Object pscredential -ArgumentList $username, $secpassword
    $dscparams.add("Credential",$credential)
}

#Always return the name
set-attr -obj $result -name "name" -value $name

$testdscresult = Test-TargetResource @dscparams
if ($testdscresult -eq $true)
{
    Exit-Json -obj $result
}
Else
{
    try
    {
        set-TargetResource @dscparams
    }
    catch
    {
        $errormsg = $_[0].exception
    }

    if ($errormsg)
    {
        Fail-Json -obj $result -message $errormsg.ToString()
    }
    Else
    {
        #Check if DSC thinks the computer needs a reboot:
        if ($global:DSCMachineStatus -eq 1)
        {
            Set-Attr $result "restart_required" $true
        }

        #Set-TargetResource did its job. We can assume a change has happened
        Set-Attr $result "changed" $true
        Exit-Json -obj $result
    }
}

