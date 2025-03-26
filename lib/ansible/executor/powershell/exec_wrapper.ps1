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
    [Version]
    $MinOSVersion,

    [Parameter()]
    [Version]
    $MinPSVersion,

    [Parameter()]
    [string]
    $TempPath,

    [Parameter()]
    [PSObject]
    $ActionParameters
)

begin {
    $DebugPreference = "SilentlyContinue"
    $ErrorActionPreference = "Stop"
    $ProgressPreference = "SilentlyContinue"

    # Try and set the console encoding to UTF-8 allowing Ansible to read the
    # output of the wrapper as UTF-8 bytes.
    try {
        [Console]::InputEncoding = [Console]::OutputEncoding = [UTF8Encoding]::new()
    }
    catch {
        # PSRP will not have a console host so this will fail. The line here is
        # to ignore sanity checks.
        $null = $_
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
        if ($PSVersionTable.PSVersion -lt $MinPSVersion) {
            @{
                failed = $true
                msg = "This module cannot run as it requires a minimum PowerShell version of $MinPSVersion, actual was ""$($PSVersionTable.PSVersion)"""
            } | ConvertTo-Json -Compress
            $Host.SetShouldExit(1)
            return
        }
    }

    # $Script:AnsibleManifest = @{}  # Defined in process/end.
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
            $IncludeScriptBlock
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

        [PSCustomObject]@{
            Name = $Name
            Script = $scriptContents
            Path = $scriptInfo.path
            ScriptBlock = $sbk
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

        $sbk = Get-AnsibleScript -Name exec_wrapper.ps1 -IncludeScriptBlock:$IncludeScriptBlock
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
            Script = $sbk.Script
            ScriptBlock = $sbk.ScriptBlock
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
            (Get-AnsibleScript -Name $moduleName).Script

            if ($moduleName -eq 'Ansible.Basic.cs') {
                $isBasicUtil = $true
            }
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
            $jsonPipeline = { ConvertFrom-Json | Convert-JsonObject }.GetSteppablePipeline()
            $jsonPipeline.Begin($true)
        }
    }
    catch {
        Write-AnsibleErrorJson -ErrorRecord $_
    }
}

process {
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
    }
}
