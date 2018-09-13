begin {
    $DebugPreference = "Continue"
    $ProgressPreference = "SilentlyContinue"
    $ErrorActionPreference = "Stop"
    Set-StrictMode -Version 2

    # common functions that are loaded in exec and module context, this is set
    # as a script scoped variable so async_watchdog and module_wrapper can
    # access the functions when creating their Runspaces
    $script:common_functions = {
        Function ConvertTo-AnsibleJson {
            <#
            .SYNOPSIS
            Create a JSON string from a PS object. This is designed to work on both
            PS Desktop and PS Core and have better performance than ConvertTo-Json.

            .PARAMETER InputObject
            Any PowerShell object to serialize to a JSON string.
            #>
            param([Parameter(Mandatory=$true)][Object]$InputObject)

            # .NET Core does not have the System.Web.Extensions and use Newtonsoft.JSON
            # .NET Framework does not have Newtonsoft.JSON so we need to detect what we
            # can use
            try {
                # The -ErrorAction is needed, the try/catch will not block it from creating
                # an error record if not set and the terminating except still fires
                Add-Type -AssemblyName System.Web.Extensions -ErrorAction SilentlyContinue
                $js_serial = $true
            } catch {
                $js_serial = $false
            }

            if ($js_serial) {
                $json = New-Object -TypeName System.Web.Script.Serialization.JavaScriptSerializer
                $json.MaxJsonLength = [Int32]::MaxValue
                $json.RecursionLimit = [Int32]::MaxValue
                return $json.Serialize($InputObject)
            } else {
                $json = [Newtonsoft.Json.JsonConvert]::SerializeObject($InputObject)
                return $json
            }
        }

        Function ConvertFrom-AnsibleJson {
            <#
            .SYNOPSIS
            Converts a JSON string to a PS Object, defaults to a Dictionary. This is
            designed to work on both PS Desktop and PS Core, have better performance
            than ConvertTo-Json and also add the ability to specify the output type.

            .PARAMETER InputObject
            [String] The JSON string to deserialize.

            .PARAMETER Type
            [Type] The type of object to create, by default will be Dictionary.
            #>
            param(
                [Parameter(Mandatory=$true)][String]$InputObject,
                [Type]$Type = [System.Collections.Generic.Dictionary`2[[String], [Object]]]
            )

            # .NET Core does not have the System.Web.Extensions and use Newtonsoft.JSON
            # .NET Framework does not have Newtonsoft.JSON so we need to detect what we
            # can use
            try {
                # The -ErrorAction is needed, the try/catch will not block it from creating
                # an error record if not set and the terminating except still fires
                Add-Type -AssemblyName System.Web.Extensions -ErrorAction SilentlyContinue
                $js_serial = $true
            } catch {
                $js_serial = $false
            }

            if ($js_serial) {
                $json = New-Object -TypeName System.Web.Script.Serialization.JavaScriptSerializer
                $json.MaxJsonLength = [Int32]::MaxValue
                $json.RecursionLimit = [Int32]::MaxValue
                return $json.Deserialize($InputObject, $Type)
            } else {
                # need to use Reflection to set the output type we want on the DeserializeObject method
                $binding_flags = [System.Reflection.BindingFlags]"DeclaredOnly, InvokeMethod, Public, Static"
                $methods = ([Newtonsoft.Json.JsonConvert]).GetMethods($binding_flags) | `
                    Where-Object { $_.Name -eq "DeserializeObject" -and $_.IsGenericMethod }

                $deserial_method = $null
                foreach ($method in $methods) {
                    $p = $method.GetParameters()
                    if ($p.Count -eq 2 -and $p[0].ParameterType -eq [System.String] -and $p[1].ParameterType -eq [Newtonsoft.Json.JsonSerializerSettings]) {
                        $deserial_method = $method.MakeGenericMethod($Type)
                        break
                    }
                }
                $settings = [System.Activator]::CreateInstance([Newtonsoft.Json.JsonSerializerSettings])
                $settings.FloatParseHandling = [Newtonsoft.Json.FloatParseHandling]::Decimal
                return $deserial_method.Invoke([Newtonsoft.Json.JsonConvert], @($InputObject, [Newtonsoft.Json.JsonSerializerSettings]$settings))
            }
        }

        Function Add-CSharpType {
            <#
            .SYNOPSIS
            Compiles one or more C# scripts into the current AppDomain similar
            to Add-Type. Exposes more configuration options that we may need to
            set within Ansible.

            .PARAMETER References
            [String[]] A collection of C# scripts to compile together.

            .PARAMETER IgnoreWarnings
            [Switch] Whether to compile code that contains compiler warnings, by
            default warnings will cause a compiler error.

            .PARAMETER PassThru
            [Switch] Whether to return the loaded Assembly

            .PARAMETER AnsibleModule
            TODO - This is an AnsibleModule object that is used to derive the
            TempPath and Debug values.
                TempPath is set to the TmpDir property of the class
                IncludeDebugInfo is set when the Ansible verbosity is >= 3

            .PARAMETER TempPath
            [String] The temporary directory in which the dynamic assembly is
            compiled to. This file is deleted once compilation is complete.
            Cannot be used when AnsibleModule is set.

            .PARAMETER IncludeDebugInfo
            [Switch] Whether to include debug information in the compiled
            assembly. Cannot be used when AnsibleModule is set.
            #>
            param(
                [Parameter(Mandatory=$true)][AllowEmptyCollection()][String[]]$References,
                [Switch]$IgnoreWarnings,
                [Switch]$PassThru,
                [Parameter(Mandatory=$true, ParameterSetName="Module")][Object]$AnsibleModule,
                [Parameter(ParameterSetName="Manual")][String]$TempPath = $env:TMP,
                [Parameter(ParameterSetName="Manual")][Switch]$IncludeDebugInfo
            )
            if ($null -eq $References -or $References.Length -eq 0) {
                return
            }

            # configure compile options based on input
            if ($PSCmdlet.ParameterSetName -eq "Module") {
                $temp_path = $AnsibleModule.TmpDir
                $include_debug = $AnsibleModule.Verbosity -ge 3
            } else {
                $temp_path = $TempPath
                $include_debug = $IncludeDebugInfo.IsPresent
            }
            $compile_parameters = New-Object -TypeName System.CodeDom.Compiler.CompilerParameters
            $compile_parameters.CompilerOptions = "/optimize"
            $compile_parameters.GenerateExecutable = $false
            $compile_parameters.GenerateInMemory = $true
            $compile_parameters.TreatWarningsAsErrors = (-not $IgnoreWarnings.IsPresent)
            $compile_parameters.IncludeDebugInformation = $include_debug
            $compile_parameters.TempFiles = (New-Object -TypeName System.CodeDom.Compiler.TempFileCollection -ArgumentList $temp_path, $false)

            # Add-Type automatically references System.dll, System.Core.dll,
            # and System.Management.Automation.dll which we replicate here
            $assemblies = [System.Collections.Generic.HashSet`1[String]]@(
                "System.dll",
                "System.Core.dll",
                ([System.Reflection.Assembly]::GetAssembly([PSObject])).Location
            )

            # create a code snippet for each reference and check if we need to
            # reference any extra assemblyies (//AssemblyReference -Name ....)
            $compile_units = [System.Collections.Generic.List`1[System.CodeDom.CodeSnippetCompileUnit]]@()
            foreach ($reference in $References) {
                $reference_code = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($reference))
                $sr = New-Object -TypeName System.IO.StringReader -ArgumentList $reference_code
                try {
                    while ($null -ne ($line = $sr.ReadLine())) {
                        if ($line -match "^//\s*AssemblyReference\s+-Name\s+([\w.]*)$") {
                            $assemblies.Add($Matches[1]) > $null
                        }
                    }
                } finally {
                    $sr.Close()
                }
                $compile_units.Add((New-Object -TypeName System.CodeDom.CodeSnippetCompileUnit -ArgumentList $reference_code)) > $null
            }
            $compile_parameters.ReferencedAssemblies.AddRange($assemblies)

            # compile
            $provider = New-Object -TypeName Microsoft.CSharp.CSharpCodeProvider
            $compile = $provider.CompileAssemblyFromDom($compile_parameters, $compile_units.ToArray())
            if ($compile.Errors.HasErrors) {
                $msg = "Failed to compile C# code: "
                foreach ($e in $compile.Errors) {
                    $msg += "`r`n" + $e.ToString()
                }
                throw [InvalidOperationException]$msg
            }

            if ($PassThru) {
                return $compile.CompiledAssembly
            }
        }

        Function Format-AnsibleException {
            <#
            .SYNOPSIS
            Formats a PowerShell ErrorRecord to a string that's fit for human
            consumption.

            .NOTES
            Using Out-String can give us the first part of the exception but it
            also wraps the messages at 80 chars which is not ideal. We also
            append the ScriptStackTrace and the .NET StackTrace if present.
            #>
            param([System.Management.Automation.ErrorRecord]$ErrorRecord)

            $exception = @"
$($ErrorRecord.ToString())
$($ErrorRecord.InvocationInfo.PositionMessage)
    + CategoryInfo          : $($ErrorRecord.CategoryInfo.ToString())
    + FullyQualifiedErrorId : $($ErrorRecord.FullyQualifiedErrorId.ToString())
"@
            # module_common strip comments and empty newlines, need to manually
            # add a preceding newline using `r`n
            $exception += "`r`n`r`nScriptStackTrace:`r`n$($ErrorRecord.ScriptStackTrace)`r`n"

            # exceptions from C# will also have a StackTrace which we
            # append if found
            if ($null -ne $ErrorRecord.Exception.StackTrace) {
                $exception += "`r`n$($ErrorRecord.Exception.ToString())"
            }

            return $exception
        }
    }
    .$common_functions

    # common wrapper functions used in the exec wrappers, this is defined in a
    # script scoped variable so async_watchdog can pass them into the async job
    $script:wrapper_functions = {
        Function Write-AnsibleError {
            <#
            .SYNOPSIS
            Writes an error message to a JSON string in the format that Ansible
            understands. Also optionally adds an exception record if the ErrorRecord
            is passed through.
            #>
            param(
                [Parameter(Mandatory=$true)][String]$Message,
                [System.Management.Automation.ErrorRecord]$ErrorRecord = $null
            )
            $result = @{
                msg = "internal error: $Message"
                failed = $true
            }
            if ($null -ne $ErrorRecord) {
                $result.msg += ": $($ErrorRecord.Exception.Message)"
                $result.exception = (Format-AnsibleException -ErrorRecord $ErrorRecord)
            }
            Write-Output -InputObject (ConvertTo-AnsibleJson -InputObject $result)
        }

        Function Write-AnsibleLog {
            <#
            .SYNOPSIS
            Used as a debugging tool to log events to a file as they run in the exec
            wrappers. By default this is a noop function but the $log_path can be
            manually set to enable it. Manually set ANSIBLE_EXEC_DEBUG as an env
            value on the Windows host that this is run on to enable.
            #>
            param(
                [Parameter(Mandatory=$true, Position=0)][String]$Message,
                [Parameter(Position=1)][String]$Wrapper
            )

            # TODO: is this a security concern, should we just have user's manually edit this if they want to enable it
            $log_path = $env:ANSIBLE_EXEC_DEBUG
            if ($log_path) {
                $log_path = [System.Environment]::ExpandEnvironmentVariables($log_path)
                $parent_path = [System.IO.Path]::GetDirectoryName($log_path)
                if (Test-Path -LiteralPath $parent_path -PathType Container) {
                    $msg = "{0:u} - {1} - {2} - " -f (Get-Date), $pid, ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
                    if ($null -ne $Wrapper) {
                        $msg += "$Wrapper - "
                    }
                    $msg += $Message + "`r`n"
                    $msg_bytes = [System.Text.Encoding]::UTF8.GetBytes($msg)

                    $fs = [System.IO.File]::Open($log_path, [System.IO.FileMode]::Append,
                        [System.IO.FileAccess]::Write, [System.IO.FileShare]::ReadWrite)
                    try {
                        $fs.Write($msg_bytes, 0, $msg_bytes.Length)
                    } finally {
                        $fs.Close()
                    }
                }
            }
        }
    }
    .$wrapper_functions

    # NB: do not adjust the following line - it is replaced when doing
    # non-streamed input
    $json_raw = ''
} process {
    $json_raw += [String]$input
} end {
    Write-AnsibleLog "INFO - starting exec_wrapper" "exec_wrapper"
    if (-not $json_raw) {
        Write-AnsibleError -Message "no input given to PowerShell exec wrapper"
        exit 1
    }

    Write-AnsibleLog "INFO - converting json raw to a payload" "exec_wrapper"
    $payload = ConvertFrom-AnsibleJson -InputObject $json_raw

    # TODO: handle binary modules
    # TODO: handle persistence

    if ($payload.min_os_version) {
        $min_os_version = [Version]$payload.min_os_version
        # Environment.OSVersion.Version is deprecated and may not return the
        # right version
        $actual_os_version = [Version](Get-Item -Path $env:SystemRoot\System32\kernel32.dll).VersionInfo.ProductVersion

        Write-AnsibleLog "INFO - checking if actual os version '$actual_os_version' is less than the min os version '$min_os_version'" "exec_wrapper"
        if ($actual_os_version -lt $min_os_version) {
            Write-AnsibleError -Message "This module cannot run on this OS as it requires a minimum version of $min_os_version, actual was $actual_os_version"
            exit 1
        }
    }
    if ($payload.min_ps_version) {
        $min_ps_version = [Version]$payload.min_ps_version
        $actual_ps_version = $PSVersionTable.PSVersion

        Write-AnsibleLog "INFO - checking if actual PS version '$actual_ps_version' is less than the min PS version '$min_ps_version'" "exec_wrapper"
        if ($actual_ps_version -lt $min_ps_version) {
            Write-AnsibleError -Message "This module cannot run as it requires a minimum PowerShell version of $min_ps_version, actual was $actual_ps_version"
            exit 1
        }
    }

    # pop 0th action as entrypoint
    $action = $payload.actions[0]
    Write-AnsibleLog "INFO - running action $action" "exec_wrapper"

    $entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($payload.($action)))
    $entrypoint = [ScriptBlock]::Create($entrypoint)
    # so we preserve the formatting and don't fall prey to locale issues, some
    # wrappers want the output to be in base64 form, we store the value here in
    # case the wrapper changes the value when they create a payload for their
    # own exec_wrapper
    $encoded_output = $payload.encoded_output

    try {
        $output = &$entrypoint -Payload $payload
        if ($encoded_output -and $null -ne $output) {
            $b64_output = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($output))
            Write-Output -InputObject $b64_output
        } else {
            Write-Output -InputObject $output
        }
    } catch {
        Write-AnsibleError -Message "failed to run exec_wrapper action $action" -ErrorRecord $_
        exit 1
    }
    Write-AnsibleLog "INFO - ending exec_wrapper" "exec_wrapper"
}
