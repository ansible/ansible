begin {
    $DebugPreference = "Continue"
    $ProgressPreference = "SilentlyContinue"
    $ErrorActionPreference = "Stop"
    Set-StrictMode -Version 2

    # common functions that are loaded in exec and module context, this is set
    # as a script scoped variable so async_watchdog and module_wrapper can
    # access the functions when creating their Runspaces
    $script:common_functions = {
        Function ConvertFrom-AnsibleJson {
            <#
            .SYNOPSIS
            Converts a JSON string to a Hashtable/Array in the fastest way
            possible. Unfortunately ConvertFrom-Json is still faster but outputs
            a PSCustomObject which is combersone for module consumption.

            .PARAMETER InputObject
            [String] The JSON string to deserialize.
            #>
            param(
                [Parameter(Mandatory=$true, Position=0)][String]$InputObject
            )

            # we can use -AsHashtable to get PowerShell to convert the JSON to
            # a Hashtable and not a PSCustomObject. This was added in PowerShell
            # 6.0, fall back to a manual conversion for older versions
            $cmdlet = Get-Command -Name ConvertFrom-Json -CommandType Cmdlet
            if ("AsHashtable" -in $cmdlet.Parameters.Keys) {
                return ,(ConvertFrom-Json -InputObject $InputObject -AsHashtable)
            } else {
                # get the PSCustomObject and then manually convert from there
                $raw_obj = ConvertFrom-Json -InputObject $InputObject

                Function ConvertTo-Hashtable {
                    param($InputObject)

                    if ($null -eq $InputObject) {
                        return $null
                    }

                    if ($InputObject -is [PSCustomObject]) {
                        $new_value = @{}
                        foreach ($prop in $InputObject.PSObject.Properties.GetEnumerator()) {
                            $new_value.($prop.Name) = (ConvertTo-Hashtable -InputObject $prop.Value)
                        }
                        return ,$new_value
                    } elseif ($InputObject -is [Array]) {
                        $new_value = [System.Collections.ArrayList]@()
                        foreach ($val in $InputObject) {
                            $new_value.Add((ConvertTo-Hashtable -InputObject $val)) > $null
                        }
                        return ,$new_value.ToArray()
                    } else {
                        return ,$InputObject
                    }
                }
                return ,(ConvertTo-Hashtable -InputObject $raw_obj)
            }
        }

        Function Add-CSharpType {
            <#
            .SYNOPSIS
            Compiles one or more C# scripts similar to Add-Type. This exposes
            more configuration options that are useable within Ansible and it
            also allows multiple C# sources to be compiled together.

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
            Cannot be used when AnsibleModule is set. This is a no-op when
            running on PSCore.

            .PARAMETER IncludeDebugInfo
            [Switch] Whether to include debug information in the compiled
            assembly. Cannot be used when AnsibleModule is set. This is a no-op
            when running on PSCore.
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

            # define special symbols CORECLR, WINDOWS, UNIX if required
            # the Is* variables are defined on PSCore, if absent we assume an
            # older version of PowerShell under .NET Framework and Windows
            $defined_symbols = [System.Collections.ArrayList]@()
            $is_coreclr = Get-Variable -Name IsCoreCLR -ErrorAction SilentlyContinue
            if ($null -ne $is_coreclr) {
                if ($is_coreclr.Value) {
                    $defined_symbols.Add("CORECLR") > $null
                }
            }
            $is_windows = Get-Variable -Name IsWindows -ErrorAction SilentlyContinue
            if ($null -ne $is_windows) {
                if ($is_windows.Value) {
                    $defined_symbols.Add("WINDOWS") > $null
                } else {
                    $defined_symbols.Add("UNIX") > $null
                }
            } else {
                $defined_symbols.Add("WINDOWS") > $null
            }

            # pattern used to find referenced assemblies in the code
            $assembly_pattern = "^//\s*AssemblyReference\s+-Name\s+(?<Name>[\w.]*)(\s+-CLR\s+(?<CLR>Core|Framework))?$"

            # PSCore vs PSDesktop use different methods to compile the code,
            # PSCore uses Roslyn and can compile the code purely in memory
            # without touching the disk while PSDesktop uses CodeDom and csc.exe
            # to compile the code. We branch out here and run each
            # distribution's method to add our C# code.
            if ($is_coreclr) {
                # compile the code using Roslyn on PSCore

                # Include the default assemblies using the logic in Add-Type
                # https://github.com/PowerShell/PowerShell/blob/master/src/Microsoft.PowerShell.Commands.Utility/commands/utility/AddType.cs
                $assemblies = [System.Collections.Generic.HashSet`1[Microsoft.CodeAnalysis.MetadataReference]]@(
                    [Microsoft.CodeAnalysis.CompilationReference]::CreateFromFile(([System.Reflection.Assembly]::GetAssembly([PSObject])).Location)
                )
                $netcore_app_ref_folder = [System.IO.Path]::Combine([System.IO.Path]::GetDirectoryName([PSObject].Assembly.Location), "ref")
                foreach ($file in [System.IO.Directory]::EnumerateFiles($netcore_app_ref_folder, "*.dll", [System.IO.SearchOption]::TopDirectoryOnly)) {
                    $assemblies.Add([Microsoft.CodeAnalysis.MetadataReference]::CreateFromFile($file)) > $null
                }

                # loop through the references, parse as a SyntaxTree and get
                # referenced assemblies
                $parse_options = ([Microsoft.CodeAnalysis.CSharp.CSharpParseOptions]::Default).WithPreprocessorSymbols($defined_symbols)
                $syntax_trees = [System.Collections.Generic.List`1[Microsoft.CodeAnalysis.SyntaxTree]]@()
                foreach ($reference in $References) {
                    $reference_code = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($reference))

                    # scan through code and add any assemblies that match
                    # //AssemblyReference -Name ... [-CLR Core]
                    $sr = New-Object -TypeName System.IO.StringReader -ArgumentList $reference_code
                    try {
                        while ($null -ne ($line = $sr.ReadLine())) {
                            if ($line -imatch $assembly_pattern) {
                                # verify the reference is not for .NET Framework
                                if ($Matches.ContainsKey("CLR") -and $Matches.CLR -ne "Core") {
                                    continue
                                }
                                $assemblies.Add($Matches.Name) > $null
                            }
                        }
                    } finally {
                        $sr.Close()
                    }
                    $syntax_trees.Add([Microsoft.CodeAnalysis.CSharp.CSharpSyntaxTree]::ParseText($reference_code, $parse_options)) > $null
                }

                # Release seems to contain the correct line numbers compared to
                # debug,may need to keep a closer eye on this in the future
                $compiler_options = (New-Object -TypeName Microsoft.CodeAnalysis.CSharp.CSharpCompilationOptions -ArgumentList @(
                    [Microsoft.CodeAnalysis.OutputKind]::DynamicallyLinkedLibrary
                )).WithOptimizationLevel([Microsoft.CodeAnalysis.OptimizationLevel]::Release)

                # set warnings to error out if IgnoreWarnings is not set
                if (-not $IgnoreWarnings.IsPresent) {
                    $compiler_options = $compiler_options.WithGeneralDiagnosticOption([Microsoft.CodeAnalysis.ReportDiagnostic]::Error)
                }

                # create compilation object
                $compilation = [Microsoft.CodeAnalysis.CSharp.CSharpCompilation]::Create(
                    [System.Guid]::NewGuid().ToString(),
                    $syntax_trees,
                    $assemblies,
                    $compiler_options
                )

                # Load the compiled code and pdb info, we do this so we can
                # include line number in a stracktrace
                $code_ms = New-Object -TypeName System.IO.MemoryStream
                $pdb_ms = New-Object -TypeName System.IO.MemoryStream
                try {
                    $emit_result = $compilation.Emit($code_ms, $pdb_ms)
                    if (-not $emit_result.Success) {
                        $errors = [System.Collections.ArrayList]@()

                        foreach ($e in $emit_result.Diagnostics) {
                            # builds the error msg, based on logic in Add-Type
                            # https://github.com/PowerShell/PowerShell/blob/master/src/Microsoft.PowerShell.Commands.Utility/commands/utility/AddType.cs#L1239
                            if ($null -eq $e.Location.SourceTree) {
                                $errors.Add($e.ToString()) > $null
                                continue
                            }

                            $cancel_token = New-Object -TypeName System.Threading.CancellationToken -ArgumentList $false
                            $text_lines = $e.Location.SourceTree.GetText($cancel_token).Lines
                            $line_span = $e.Location.GetLineSpan()

                            $diagnostic_message = $e.ToString()
                            $error_line_string = $text_lines[$line_span.StartLinePosition.Line].ToString()
                            $error_position = $line_span.StartLinePosition.Character

                            $sb = New-Object -TypeName System.Text.StringBuilder -ArgumentList ($diagnostic_message.Length + $error_line_string.Length * 2 + 4)
                            $sb.AppendLine($diagnostic_message)
                            $sb.AppendLine($error_line_string)

                            for ($i = 0; $i -lt $error_line_string.Length; $i++) {
                                if ([System.Char]::IsWhiteSpace($error_line_string[$i])) {
                                    continue
                                }
                                $sb.Append($error_line_string, 0, $i)
                                $sb.Append(' ', [Math]::Max(0, $error_position - $i))
                                $sb.Append("^")
                                break
                            }

                            $errors.Add($sb.ToString()) > $null
                        }

                        throw [InvalidOperationException]"Failed to compile C# code:`r`n$($errors -join "`r`n")"
                    }

                    $code_ms.Seek(0, [System.IO.SeekOrigin]::Begin) > $null
                    $pdb_ms.Seek(0, [System.IO.SeekOrigin]::Begin) > $null
                    $compiled_assembly = [System.Runtime.Loader.AssemblyLoadContext]::Default.LoadFromStream($code_ms, $pdb_ms)
                } finally {
                    $code_ms.Close()
                    $pdb_ms.Close()
                }
            } else {
                # compile the code using CodeDom on PSDesktop

                # configure compile options based on input
                if ($PSCmdlet.ParameterSetName -eq "Module") {
                    $temp_path = $AnsibleModule.TmpDir
                    $include_debug = $AnsibleModule.Verbosity -ge 3
                } else {
                    $temp_path = $TempPath
                    $include_debug = $IncludeDebugInfo.IsPresent
                }
                $compiler_options = [System.Collections.ArrayList]@("/optimize")
                if ($defined_symbols.Count -gt 0) {
                    $compiler_options.Add("/define:" + ([String]::Join(";", $defined_symbols.ToArray()))) > $null
                }

                $compile_parameters = New-Object -TypeName System.CodeDom.Compiler.CompilerParameters
                $compile_parameters.CompilerOptions = [String]::Join(" ", $compiler_options.ToArray())
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

                # create a code snippet for each reference and check if we need
                # to reference any extra assemblies
                # //AssemblyReference -Name ... [-CLR Framework]
                $compile_units = [System.Collections.Generic.List`1[System.CodeDom.CodeSnippetCompileUnit]]@()
                foreach ($reference in $References) {
                    $reference_code = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($reference))
                    $sr = New-Object -TypeName System.IO.StringReader -ArgumentList $reference_code
                    try {
                        while ($null -ne ($line = $sr.ReadLine())) {
                            if ($line -imatch $assembly_pattern) {
                                # verify the reference is not for .NET Core
                                if ($Matches.ContainsKey("CLR") -and $Matches.CLR -ne "Framework") {
                                    continue
                                }
                                $assemblies.Add($Matches.Name) > $null
                            }
                        }
                    } finally {
                        $sr.Close()
                    }
                    $compile_units.Add((New-Object -TypeName System.CodeDom.CodeSnippetCompileUnit -ArgumentList $reference_code)) > $null
                }
                $compile_parameters.ReferencedAssemblies.AddRange($assemblies)

                # compile the code together and check for errors
                $provider = New-Object -TypeName Microsoft.CSharp.CSharpCodeProvider
                $compile = $provider.CompileAssemblyFromDom($compile_parameters, $compile_units.ToArray())
                if ($compile.Errors.HasErrors) {
                    $msg = "Failed to compile C# code: "
                    foreach ($e in $compile.Errors) {
                        $msg += "`r`n" + $e.ToString()
                    }
                    throw [InvalidOperationException]$msg
                }
                $compiled_assembly = $compile.CompiledAssembly
            }

            # return the compiled assembly if PassThru is set.
            if ($PassThru) {
                return $compiled_assembly
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
            understands. Also optionally adds an exception record if the
            ErrorRecord is passed through.
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
            Write-Output -InputObject (ConvertTo-Json -InputObject $result -Depth 99 -Compress)
        }

        Function Write-AnsibleLog {
            <#
            .SYNOPSIS
            Used as a debugging tool to log events to a file as they run in the
            exec wrappers. By default this is a noop function but the $log_path
            can be manually set to enable it. Manually set ANSIBLE_EXEC_DEBUG as
            an env value on the Windows host that this is run on to enable.
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
