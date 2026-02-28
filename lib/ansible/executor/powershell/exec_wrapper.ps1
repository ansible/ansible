# (c) 2025 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

using namespace System.Collections
using namespace System.Collections.Generic
using namespace System.Diagnostics.CodeAnalysis
using namespace System.IO
using namespace System.Linq
using namespace System.Management.Automation
using namespace System.Management.Automation.Language
using namespace System.Management.Automation.Security
using namespace System.Reflection
using namespace System.Security.Cryptography
using namespace System.Text

[SuppressMessageAttribute(
    "PSUseCmdletCorrectly",
    "",
    Justification = "ConvertFrom-Json is being used in a steppable pipeline and works this way."
)]
[CmdletBinding()]
param (
    [Parameter(ValueFromPipeline)]
    [string]
    $InputObject,

    [Parameter()]
    [IDictionary]
    $Manifest,

    [Parameter()]
    [switch]
    $EncodeInputOutput,

    [Parameter()]
    [string]
    $MinOSVersion,

    [Parameter()]
    [string]
    $MinPSVersion,

    [Parameter()]
    [string]
    $TempPath,

    [Parameter()]
    [string]
    $PwshPath,

    [Parameter()]
    [PSObject]
    $ActionParameters
)

begin {
    $DebugPreference = "SilentlyContinue"
    $ErrorActionPreference = "Stop"
    $ProgressPreference = "SilentlyContinue"

    if ($PSCommandPath -and (Test-Path -LiteralPath $PSCommandPath)) {
        Remove-Item -LiteralPath $PSCommandPath -Force
    }

    # Try and set the console encoding to UTF-8 allowing Ansible to read the
    # output of the wrapper as UTF-8 bytes.
    try {
        [Console]::InputEncoding = [Console]::OutputEncoding = [UTF8Encoding]::new()
    }
    catch {
        # PSRP will not have a console host so this will fail. Fallback to
        # setting the private field we know is present on this version. This
        # is important as PowerShell uses this encoding when decoding output
        # from a new process that it spawns.
        if ($PSVersionTable.PSVersion -lt '6.0') {
            [Console].GetField('_outputEncoding', [BindingFlags]'NonPublic, Static').SetValue($null, [UTF8Encoding]::new())
        }
    }

    $respawnPipeline = $null
    if ($PwshPath) {
        $null = $PSBoundParameters.Remove('PwshPath')

        $targetPwsh = Get-Command -Name $PwshPath -CommandType Application -ErrorAction Ignore |
            ForEach-Object { [Path]::GetFullPath($_.Path) }
        if (-not $targetPwsh) {
            @{
                failed = $true
                msg = "Could not find the specified PowerShell interpreter '$PwshPath'."
            } | ConvertTo-Json -Compress
            $Host.SetShouldExit(1)
            return
        }

        # Resolve the path in case of a symbolic link, ResolveLinkTarget is
        # present in pwsh 7+.
        if ([Directory]::ResolveLinkTarget) {
            $targetPath = [Directory]::ResolveLinkTarget($targetPwsh, $true)
            if ($targetPath) {
                $targetPwsh = $targetPath.FullName
            }
        }
        else {
            while ($true) {
                $target = Get-Item -LiteralPath $targetPwsh
                if ($target.LinkType -ne 'SymbolicLink') {
                    break
                }

                $targetPath = $target.Target
                if ($targetPath -notmatch '([a-z]:[\\/])|([\\/]{2})') {
                    # If the target isn't rooted in a drive or UNC path then
                    # they are relative to the link location.
                    $targetPath = [Path]::Combine(
                        [Path]::GetDirectoryName($targetPwsh),
                        $targetPath)
                }
                $targetPwsh = [Path]::GetFullPath($targetPath)
            }
        }

        # We don't compare the exe as the current process may not be the
        # normal interpreter but the WSManProvHost used by PSRP. Instead see if
        # the PSHome path is the same as the target interpreter directory.
        $targetPSHome = Split-Path -Path $targetPwsh -Parent
        if ($targetPSHome -ne $PSHome) {
            $bootstrapWrapper = (Get-PSCallStack)[1].InvocationInfo.MyCommand.Definition
            $encCommand = [Convert]::ToBase64String([Encoding]::Unicode.GetBytes($bootstrapWrapper))

            $targetPwshArgs = @(
                '-NoProfile'
                '-NonInteractive'
                if ($PSVersionTable.PSVersion -lt '6.0' -or $IsWindows) {
                    '-ExecutionPolicy'
                    'Unrestricted'
                }
                '-EncodedCommand'
                $encCommand
            )

            $execManifest = @{
                name = 'exec_wrapper-respawn.ps1'
                params = $PSBoundParameters
                script = $MyInvocation.MyCommand.ScriptBlock.ToString()
            } | ConvertTo-Json -Compress -Depth 99

            $respawnPipeline = { & $targetPwsh @targetPwshArgs }.GetSteppablePipeline()

            # Need to set back to Continue to stderr ErrorRecords don't stop at
            # the first one (line).
            $ErrorActionPreference = 'Continue'
            $null = $respawnPipeline.Begin($true)
            $null = $respawnPipeline.Process($execManifest)
            $null = $respawnPipeline.Process("`0`0`0`0")
            # Remaining input will be sent in the process block
            return
        }
    }

    if ($MinOSVersion) {
        [version]$actualOSVersion = (Get-Item -LiteralPath $env:SystemRoot\System32\kernel32.dll).VersionInfo.ProductVersion

        if ($actualOSVersion -lt $MinOSVersion) {
            @{
                failed = $true
                msg = "This module cannot run on this OS as it requires a minimum version of $MinOSVersion, actual was $actualOSVersion"
            } | ConvertTo-Json -Compress
            $Host.SetShouldExit(1)
            return
        }
    }

    if ($MinPSVersion) {
        if ([version]$PSVersionTable.PSVersion -lt $MinPSVersion) {
            @{
                failed = $true
                msg = "This module cannot run as it requires a minimum PowerShell version of $MinPSVersion, actual was ""$($PSVersionTable.PSVersion)"""
            } | ConvertTo-Json -Compress
            $Host.SetShouldExit(1)
            return
        }
    }

    # $Script:AnsibleManifest = @{}  # Defined in process/end.
    $Script:AnsibleShouldConstrain = if ($PSVersionTable.PSVersion -lt '6.0' -or $IsWindows) {
        [SystemPolicy]::GetSystemLockdownPolicy() -eq 'Enforce'
    }
    else {
        $false
    }
    $Script:AnsibleTrustedHashList = [HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $Script:AnsibleUnsupportedHashList = [HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    $Script:AnsibleWrapperWarnings = [List[string]]::new()
    $Script:AnsibleTempPath = @(
        # Wrapper defined tmpdir
        [Environment]::ExpandEnvironmentVariables($TempPath)
        # Fallback to user's tmpdir
        [Path]::GetTempPath()
        # Should not happen but just in case use the current dir.
        $pwd.Path
    ) | Where-Object {
        if (-not $_) {
            return $false
        }

        try {
            Test-Path -LiteralPath $_ -ErrorAction Ignore
        }
        catch {
            # Access denied could cause Test-Path to throw an exception.
            $false
        }
    } | Select-Object -First 1
    $Script:AnsibleTempScripts = [List[string]]::new()
    $Script:AnsibleClrFacadeSet = $false

    Function Convert-JsonObject {
        param(
            [Parameter(Mandatory, ValueFromPipeline)]
            [AllowNull()]
            [object]
            $InputObject
        )

        process {
            # Using the full type name is important as PSCustomObject is an
            # alias for PSObject which all piped objects are.
            if ($InputObject -is [System.Management.Automation.PSCustomObject]) {
                $value = @{}
                foreach ($prop in $InputObject.PSObject.Properties) {
                    $value[$prop.Name] = Convert-JsonObject -InputObject $prop.Value
                }
                $value
            }
            elseif ($InputObject -is [Array]) {
                , @($InputObject | Convert-JsonObject)
            }
            else {
                $InputObject
            }
        }
    }

    Function Get-AnsibleScript {
        [CmdletBinding()]
        param (
            [Parameter(Mandatory)]
            [string]
            $Name,

            [Parameter()]
            [switch]
            $IncludeScriptBlock,

            [Parameter()]
            [switch]
            $SkipHashCheck
        )

        if (-not $Script:AnsibleManifest.scripts.Contains($Name)) {
            $err = [ErrorRecord]::new(
                [Exception]::new("Could not find the script '$Name'."),
                "ScriptNotFound",
                [ErrorCategory]::ObjectNotFound,
                $Name)
            $PSCmdlet.ThrowTerminatingError($err)
        }

        $scriptInfo = $Script:AnsibleManifest.scripts[$Name]
        $scriptBytes = [Convert]::FromBase64String($scriptInfo.script)
        $scriptContents = [Encoding]::UTF8.GetString($scriptBytes)

        $sbk = $null
        if ($IncludeScriptBlock) {
            $sbk = [Parser]::ParseInput(
                $scriptContents,
                $Name,
                [ref]$null,
                [ref]$null).GetScriptBlock()
        }

        $outputValue = [PSCustomObject]@{
            Name = $Name
            Script = $scriptContents
            Path = $scriptInfo.path
            ScriptBlock = $sbk
            ShouldConstrain = $false
        }

        if (-not $Script:AnsibleShouldConstrain) {
            $outputValue
            return
        }

        if (-not $SkipHashCheck) {
            $sha256 = [SHA256]::Create()
            $scriptHash = [BitConverter]::ToString($sha256.ComputeHash($scriptBytes)).Replace("-", "")
            $sha256.Dispose()

            if ($Script:AnsibleUnsupportedHashList.Contains($scriptHash)) {
                $err = [ErrorRecord]::new(
                    [Exception]::new("Provided script for '$Name' is marked as unsupported in CLM mode."),
                    "ScriptUnsupported",
                    [ErrorCategory]::SecurityError,
                    $Name)
                $PSCmdlet.ThrowTerminatingError($err)
            }
            elseif ($Script:AnsibleTrustedHashList.Contains($scriptHash)) {
                $outputValue
                return
            }
        }

        # If we have reached here we are running in a locked down environment
        # and the script is not trusted in the signed hashlists. Check if it
        # contains the authenticode signature and verify that using PowerShell.
        # [SystemPolicy]::GetFilePolicyEnforcement(...) is a new API but only
        # present in Server 2025+ so we need to rely on the known behaviour of
        # Get-Command to fail with CommandNotFoundException if the script is
        # not allowed to run.
        $outputValue.ShouldConstrain = $true
        if ($scriptContents -like "*`r`n# SIG # Begin signature block`r`n*") {
            Set-WinPSDefaultFileEncoding

            # If the script is manually signed we need to ensure the signature
            # is valid and trusted by the OS policy.
            # We must use '.ps1' so the ExternalScript WDAC check will apply.
            $tmpFile = [Path]::Combine($Script:AnsibleTempPath, "ansible-tmp-$([Guid]::NewGuid()).ps1")
            try {
                [File]::WriteAllBytes($tmpFile, $scriptBytes)
                $cmd = Get-Command -Name $tmpFile -CommandType ExternalScript -ErrorAction Stop

                # Get-Command caches the file contents after loading which we
                # use to verify it was not modified before the signature check.
                $expectedScript = $cmd.OriginalEncoding.GetString($scriptBytes)
                if ($expectedScript -ne $cmd.ScriptContents) {
                    $err = [ErrorRecord]::new(
                        [Exception]::new("Script has been modified during signature check."),
                        "ScriptModifiedTrusted",
                        [ErrorCategory]::SecurityError,
                        $Name)
                    $PSCmdlet.ThrowTerminatingError($err)
                }

                $outputValue.ShouldConstrain = $false
            }
            catch [CommandNotFoundException] {
                $null = $null  # No-op but satisfies the linter.
            }
            finally {
                if (Test-Path -LiteralPath $tmpFile) {
                    Remove-Item -LiteralPath $tmpFile -Force
                }
            }
        }

        if ($outputValue.ShouldConstrain -and $IncludeScriptBlock) {
            # If the script is untrusted and a scriptblock was requested we
            # error out as the sbk would have run in FLM.
            $err = [ErrorRecord]::new(
                [Exception]::new("Provided script for '$Name' is not trusted to run."),
                "ScriptNotTrusted",
                [ErrorCategory]::SecurityError,
                $Name)
            $PSCmdlet.ThrowTerminatingError($err)
        }
        else {
            $outputValue
        }
    }

    Function Get-NextAnsibleAction {
        [CmdletBinding()]
        param ()

        $action, $newActions = $Script:AnsibleManifest.actions
        $Script:AnsibleManifest.actions = @($newActions | Select-Object)

        $actionName = $action.name
        $actionParams = $action.params
        $actionScript = Get-AnsibleScript -Name $actionName -IncludeScriptBlock

        foreach ($kvp in $action.secure_params.GetEnumerator()) {
            if (-not $kvp.Value) {
                continue
            }

            $name = $kvp.Key
            $actionParams.$name = $kvp.Value | ConvertTo-SecureString -AsPlainText -Force
        }

        [PSCustomObject]@{
            Name = $actionName
            ScriptBlock = $actionScript.ScriptBlock
            Parameters = $actionParams
        }
    }

    Function Get-AnsibleExecWrapper {
        [CmdletBinding()]
        param (
            [Parameter()]
            [switch]
            $ManifestAsParam,

            [Parameter()]
            [switch]
            $EncodeInputOutput,

            [Parameter()]
            [switch]
            $IncludeScriptBlock
        )

        $scriptInfo = Get-AnsibleScript -Name exec_wrapper.ps1 -IncludeScriptBlock:$IncludeScriptBlock
        $params = @{
            # TempPath may contain env vars that change based on the runtime
            # environment. Ensure we use that and not the $script:AnsibleTempPath
            # when starting the exec wrapper.
            TempPath = $TempPath
            EncodeInputOutput = $EncodeInputOutput.IsPresent
        }

        $inputData = $null
        if ($ManifestAsParam) {
            $params.Manifest = $Script:AnsibleManifest
        }
        else {
            $inputData = ConvertTo-Json -InputObject $Script:AnsibleManifest -Depth 99 -Compress
            if ($EncodeInputOutput) {
                $inputData = [Convert]::ToBase64String([Encoding]::UTF8.GetBytes($inputData))
            }
        }

        [PSCustomObject]@{
            ScriptInfo = $scriptInfo
            Parameters = $params
            InputData = $inputData
        }
    }

    Function Import-PowerShellUtil {
        [CmdletBinding()]
        param (
            [Parameter(Mandatory)]
            [string[]]
            $Name
        )

        foreach ($moduleName in $Name) {
            $moduleInfo = Get-AnsibleScript -Name $moduleName -IncludeScriptBlock
            $moduleShortName = [Path]::GetFileNameWithoutExtension($moduleName)
            $null = New-Module -Name $moduleShortName -ScriptBlock $moduleInfo.ScriptBlock |
                Import-Module -Scope Global
        }
    }

    Function Import-CSharpUtil {
        [CmdletBinding()]
        param (
            [Parameter(Mandatory)]
            [string[]]
            $Name
        )

        Import-PowerShellUtil -Name Ansible.ModuleUtils.AddType.psm1

        $isBasicUtil = $false
        $csharpModules = foreach ($moduleName in $Name) {
            $scriptInfo = Get-AnsibleScript -Name $moduleName

            if ($scriptInfo.ShouldConstrain) {
                throw "C# module util '$Name' is not trusted and cannot be loaded."
            }
            if ($moduleName -eq 'Ansible.Basic.cs') {
                $isBasicUtil = $true
            }

            $scriptInfo.Script
        }

        $fakeModule = [PSCustomObject]@{
            Tmpdir = $Script:AnsibleTempPath
        }
        $warningFunc = [PSScriptMethod]::new('Warn', {
                param($message)
                $Script:AnsibleWrapperWarnings.Add($message)
            })
        $fakeModule.PSObject.Members.Add($warningFunc)
        Add-CSharpType -References $csharpModules -AnsibleModule $fakeModule

        if ($isBasicUtil) {
            # Ansible.Basic.cs is a special case where we need to provide it
            # with the wrapper warnings list so it injects it into the result.
            [Ansible.Basic.AnsibleModule]::_WrapperWarnings = $Script:AnsibleWrapperWarnings
        }
    }

    Function Import-SignedHashList {
        [CmdletBinding()]
        param (
            [Parameter(Mandatory, ValueFromPipeline)]
            [string]
            $Name
        )

        process {
            try {
                # We skip the hash check to ensure we verify based on the
                # authenticode signature and not whether it's trusted by an
                # existing signed hash list.
                $scriptInfo = Get-AnsibleScript -Name $Name -SkipHashCheck
                if ($scriptInfo.ShouldConstrain) {
                    throw "script is not signed or not trusted to run."
                }

                $hashListAst = [Parser]::ParseInput(
                    $scriptInfo.Script,
                    $Name,
                    [ref]$null,
                    [ref]$null)
                $manifestAst = $hashListAst.Find({ $args[0] -is [HashtableAst] }, $false)
                if ($null -eq $manifestAst) {
                    throw "expecting a single hashtable in the signed manifest."
                }

                $out = $manifestAst.SafeGetValue()
                if (-not $out.Contains('Version')) {
                    throw "expecting hash list to contain 'Version' key."
                }
                if ($out.Version -ne 1) {
                    throw "unsupported hash list Version $($out.Version), expecting 1."
                }

                if (-not $out.Contains('HashList')) {
                    throw "expecting hash list to contain 'HashList' key."
                }

                $out.HashList | ForEach-Object {
                    if ($_ -isnot [hashtable] -or -not $_.ContainsKey('Hash') -or $_.Hash -isnot [string] -or $_.Hash.Length -ne 64) {
                        throw "expecting hash list to contain hashtable with Hash key with a value of a SHA256 strings."
                    }

                    if ($_.Mode -eq 'Trusted') {
                        $null = $Script:AnsibleTrustedHashList.Add($_.Hash)
                    }
                    elseif ($_.Mode -eq 'Unsupported') {
                        # Allows us to provide a better error when trying to run
                        # something in CLM that is marked as unsupported.
                        $null = $Script:AnsibleUnsupportedHashList.Add($_.Hash)
                    }
                    else {
                        throw "expecting hash list entry for $($_.Hash) to contain a mode of 'Trusted' or 'Unsupported' but got '$($_.Mode)'."
                    }
                }
            }
            catch {
                $_.ErrorDetails = [ErrorDetails]::new("Failed to process signed manifest '$Name': $_")
                $PSCmdlet.WriteError($_)
            }
        }
    }

    Function New-TempAnsibleFile {
        [OutputType([string])]
        [CmdletBinding()]
        param (
            [Parameter(Mandatory)]
            [string]
            $FileName,

            [Parameter(Mandatory)]
            [string]
            $Content
        )

        $name = [Path]::GetFileNameWithoutExtension($FileName)
        $ext = [Path]::GetExtension($FileName)
        $newName = "$($name)-$([Guid]::NewGuid())$ext"

        $path = Join-Path -Path $Script:AnsibleTempPath $newName
        Set-WinPSDefaultFileEncoding
        [File]::WriteAllText($path, $Content, [UTF8Encoding]::new($false))

        $path
    }

    Function Set-WinPSDefaultFileEncoding {
        [CmdletBinding()]
        param ()

        # WinPS defaults to the locale encoding when loading a script from the
        # file path but in Ansible we expect it to always be UTF-8 without a
        # BOM. This lazily sets an internal field so pwsh reads it as UTF-8.
        # If we don't do this then scripts saved as UTF-8 on the Ansible
        # controller will not run as expected.
        if ($PSVersionTable.PSVersion -lt '6.0' -and -not $Script:AnsibleClrFacadeSet) {
            $clrFacade = [PSObject].Assembly.GetType('System.Management.Automation.ClrFacade')
            $defaultEncodingField = $clrFacade.GetField('_defaultEncoding', [BindingFlags]'NonPublic, Static')
            $defaultEncodingField.SetValue($null, [UTF8Encoding]::new($false))
            $Script:AnsibleClrFacadeSet = $true
        }
    }

    Function Write-AnsibleErrorJson {
        [CmdletBinding()]
        param (
            [Parameter(Mandatory)]
            [ErrorRecord]
            $ErrorRecord,

            [Parameter()]
            [string]
            $Message = "failure during exec_wrapper"
        )

        $exception = @(
            "$ErrorRecord"
            "$($ErrorRecord.InvocationInfo.PositionMessage)"
            "+ CategoryInfo          : $($ErrorRecord.CategoryInfo)"
            "+ FullyQualifiedErrorId : $($ErrorRecord.FullyQualifiedErrorId)"
            ""
            "ScriptStackTrace:"
            "$($ErrorRecord.ScriptStackTrace)"

            if ($ErrorRecord.Exception.StackTrace) {
                "$($ErrorRecord.Exception.StackTrace)"
            }
        ) -join ([Environment]::NewLine)

        @{
            failed = $true
            msg = "${Message}: $ErrorRecord"
            exception = $exception
        } | ConvertTo-Json -Compress
        $host.SetShouldExit(1)
    }

    Function Write-PowerShellClixmlStderr {
        [CmdletBinding()]
        param (
            [Parameter(Mandatory)]
            [AllowEmptyString()]
            [string]
            $Output
        )

        if (-not $Output) {
            return
        }

        # -EncodedCommand in WinPS will output CLIXML to stderr. This attempts to parse
        # it into a human readable format otherwise it'll just output the raw CLIXML.
        $wroteStderr = $false
        if ($Output.StartsWith('#< CLIXML')) {
            $clixml = $Output -split "\r?\n"
            if ($clixml.Count -eq 2) {
                try {
                    # PSSerialize.Deserialize doesn't tell us what streams each record
                    # is for so we get the S attribute manually.
                    $streams = @(([xml]$clixml[1]).Objs.GetEnumerator() | ForEach-Object { $_.S })
                    $objects = @([PSSerializer]::Deserialize($clixml[1]))

                    for ($i = 0; $i -lt $objects.Count; $i++) {
                        $msg = $objects[$i]
                        if ($msg -isnot [string] -or $streams.Length -le $i) {
                            continue
                        }

                        # Doesn't use TrimEnd() so it only removes the last newline
                        if ($msg.EndsWith([Environment]::NewLine)) {
                            $msg = $msg.Substring(0, $msg.Length - [Environment]::NewLine.Length)
                        }
                        $stream = $streams[$i]
                        switch ($stream) {
                            'error' { $host.UI.WriteErrorLine($msg) }
                            'debug' { $host.UI.WriteDebugLine($msg) }
                            'verbose' { $host.UI.WriteVerboseLine($msg) }
                            'warning' { $host.UI.WriteWarningLine($msg) }
                        }
                    }
                    $wroteStderr = $true
                }
                catch {
                    $null = $_
                }
            }
        }
        if (-not $wroteStderr) {
            $host.UI.WriteErrorLine($Output.TrimEnd())
        }
    }

    # To handle optional input for the incoming manifest and optional input to
    # the subsequent action we optionally run this step in the begin or end
    # block.
    $jsonPipeline = $null
    $actionPipeline = $null
    $setupManifest = {
        [CmdletBinding()]
        param (
            [Parameter()]
            [switch]
            $ExpectingInput
        )

        if ($jsonPipeline) {
            $Script:AnsibleManifest = $jsonPipeline.End()[0]
            $jsonPipeline.Dispose()
            $jsonPipeline = $null
        }
        else {
            $Script:AnsibleManifest = $Manifest
        }

        if ($Script:AnsibleShouldConstrain) {
            $Script:AnsibleManifest.signed_hashlist | Import-SignedHashList
        }

        $actionInfo = Get-NextAnsibleAction
        $actionParams = $actionInfo.Parameters

        if ($ActionParameters) {
            foreach ($prop in $ActionParameters.PSObject.Properties) {
                $actionParams[$prop.Name] = $prop.Value
            }
        }

        $actionPipeline = { & $actionInfo.ScriptBlock @actionParams }.GetSteppablePipeline()
        $actionPipeline.Begin($ExpectingInput)
        if (-not $ExpectingInput) {
            $null = $actionPipeline.Process()
        }
    }

    try {
        if ($Manifest) {
            # If the manifest was provided through the parameter, we can start the
            # action pipeline and all subsequent input (if any) will be sent to the
            # action.
            # It is important that $setupManifest is called by dot sourcing or
            # else the pipelines started in it loose access to all parent scopes.
            # https://github.com/PowerShell/PowerShell/issues/17868
            . $setupManifest -ExpectingInput:$MyInvocation.ExpectingInput
        }
        else {
            # Otherwise the first part of the input is the manifest json with the
            # chance for extra data afterwards.
            $jsonParams = @{}
            if ($IsCoreCLR) {
                # PowerShell 7 parses an ISO 8601 date string into a DateTime object. As we
                # want to preserve the original string we tell it using the DateKind param.
                $jsonParams.DateKind = 'String'
            }
            $jsonPipeline = { ConvertFrom-Json @jsonParams | Convert-JsonObject }.GetSteppablePipeline()
            $jsonPipeline.Begin($true)
        }
    }
    catch {
        Write-AnsibleErrorJson -ErrorRecord $_
    }
}

process {
    if ($respawnPipeline) {
        $null = $respawnPipeline.Process($InputObject)
        return
    }

    try {
        if ($actionPipeline) {
            # We received our manifest and started the action pipeline, redirect
            # all further input to that pipeline.
            $null = $actionPipeline.Process($InputObject)
        }
        elseif ([string]::Equals($InputObject, "`0`0`0`0")) {
            # Special marker used to indicate all subsequent input is for the
            # action. Setup that pipeline and finalise the manifest.
            . $setupManifest -ExpectingInput
        }
        elseif ($jsonPipeline) {
            # Data is for the JSON manifest, decode if needed.
            if ($EncodeInputOutput) {
                $jsonPipeline.Process([Encoding]::UTF8.GetString([Convert]::FromBase64String($InputObject)))
            }
            else {
                $jsonPipeline.Process($InputObject)
            }
        }
    }
    catch {
        Write-AnsibleErrorJson -ErrorRecord $_
    }
}

end {
    if ($respawnPipeline) {
        $respawnPipeline.End()
        return
    }

    try {
        if ($jsonPipeline) {
            # Only manifest input was received, process it now and start the
            # action pipeline with no input being provided.
            . $setupManifest
        }

        $out = $actionPipeline.End()
        if ($EncodeInputOutput) {
            [Convert]::ToBase64String([Encoding]::UTF8.GetBytes($out))
        }
        else {
            $out
        }
    }
    catch {
        Write-AnsibleErrorJson -ErrorRecord $_
    }
    finally {
        $actionPipeline.Dispose()
        if ($Script:AnsibleTempScripts) {
            Remove-Item -LiteralPath $Script:AnsibleTempScripts -Force -ErrorAction Ignore
        }
    }
}
