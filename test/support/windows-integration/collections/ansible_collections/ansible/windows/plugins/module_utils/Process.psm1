# Copyright (c) 2020 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

#AnsibleRequires -CSharpUtil .Process

Function Resolve-ExecutablePath {
    <#
    .SYNOPSIS
    Tries to resolve the file path to a valid executable.
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        $FilePath,

        [String]
        $WorkingDirectory
    )

    # Ensure the path has an extension set, default to .exe
    if (-not [IO.Path]::HasExtension($FilePath)) {
        $FilePath = "$FilePath.exe"
    }

    # See the if path is resolvable using the normal PATH logic. Also resolves absolute paths and relative paths if
    # they exist.
    $command = @(Get-Command -Name $FilePath -CommandType Application -ErrorAction SilentlyContinue)
    if ($command) {
        $command[0].Path
        return
    }

    # If -WorkingDirectory is specified, check if the path is relative to that
    if ($WorkingDirectory) {
        $file = $PSCmdlet.GetUnresolvedProviderPathFromPSPath((Join-Path -Path $WorkingDirectory -ChildPath $FilePath))
        if (Test-Path -LiteralPath $file) {
            $file
            return
        }
    }

    # Just hope for the best and use whatever was provided.
    $FilePath
}

Function ConvertFrom-EscapedArgument {
    <#
    .SYNOPSIS
    Extract individual arguments from a command line string.

    .PARAMETER InputObject
    The command line string to extract the arguments from.
    #>
    [CmdletBinding()]
    [OutputType([String])]
    param (
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [String[]]
        $InputObject
    )

    process {
        foreach ($command in $InputObject) {
            # CommandLineToArgv treats \" slightly different for the first argument for some reason (probably because
            # it expects it to be a filepath). We add a dummy value to ensure it splits the args in the same way as
            # each other and just discard that first arg in the output.
            $command = "a $command"
            [Ansible.Windows.Process.ProcessUtil]::CommandLineToArgv($command) | Select-Object -Skip 1
        }
    }
}

Function ConvertTo-EscapedArgument {
    <#
    .SYNOPSIS
    Escapes an argument value so it can be used in a call to CreateProcess.

    .PARAMETER InputObject
    The argument(s) to escape.
    #>
    [CmdletBinding()]
    [OutputType([String])]
    param (
        [Parameter(Mandatory = $true, ValueFromPipeline = $true)]
        [AllowEmptyString()]
        [AllowNull()]
        [String[]]
        $InputObject
    )

    process {
        if (-not $InputObject) {
            return '""'
        }

        foreach ($argument in $InputObject) {
            if (-not $argument) {
                return '""'
            }
            elseif ($argument -notmatch '[\s"]') {
                return $argument
            }

            # Replace any double quotes in an argument with '\"'
            $argument = $argument -replace '"', '\"'

            # Double up on any '\' chars that preceded '\"'
            $argument = $argument -replace '(\\+)\\"', '$1$1\"'

            # Double up '\' at the end of the argument so it doesn't escape end quote.
            $argument = $argument -replace '(\\+)$', '$1$1'

            # Finally wrap the entire argument in double quotes now we've escaped the double quotes within
            '"{0}"' -f $argument
        }
    }
}

Function Start-AnsibleWindowsProcess {
    <#
    .SYNOPSIS
    Start a process and wait for it to finish.

    .PARAMETER FilePath
    The file to execute.

    .PARAMETER ArgumentList
    Arguments to execute, these will be escaped so the literal value is used.

    .PARAMETER CommandLine
    The raw command line to call with CreateProcess. These values are not escaped for you so use at your own risk.

    .PARAMETER WorkingDirectory
    The working directory to set on the new process, defaults to the current working dir.

    .PARAMETER Environment
    Override the environment to set for the new process, if not set then the current environment will be used.

    .PARAMETER InputObject
    A string or byte[] array to send to the process' stdin when it has started.

    .PARAMETER OutputEncodingOverride
    The encoding name to use when reading the stdout/stderr of the process. Defaults to utf-8 if not set.

    .PARAMETER WaitChildren
    Whether to wait for any child process spawned to finish before returning. This only works on Windows hosts on
    Server 2012/Windows 8 or newer.

    .OUTPUTS
    [PSCustomObject]@{
        Command = The final command used to start the process
        Stdout = The stdout of the process
        Stderr = The stderr of the process
        ExitCode = The return code from the process
    }
    #>
    [CmdletBinding(DefaultParameterSetName = 'ArgumentList')]
    [OutputType('Ansible.Windows.Process.Info')]
    param (
        [Parameter(Mandatory = $true, ParameterSetName = 'ArgumentList')]
        [Parameter(ParameterSetName = 'CommandLine')]
        [String]
        $FilePath,

        [Parameter(ParameterSetName = 'ArgumentList')]
        [String[]]
        $ArgumentList,

        [Parameter(Mandatory = $true, ParameterSetName = 'CommandLine')]
        [String]
        $CommandLine,

        [String]
        # Default to the PowerShell location and not the process location.
        $WorkingDirectory = (Get-Location -PSProvider FileSystem),

        [Collections.IDictionary]
        $Environment,

        [Object]
        $InputObject,

        [String]
        [Alias('OutputEncoding')]
        $OutputEncodingOverride,

        [Switch]
        $WaitChildren
    )

    if ($WorkingDirectory) {
        if (-not (Test-Path -LiteralPath $WorkingDirectory)) {
            Write-Error -Message "Could not find specified -WorkingDirectory '$WorkingDirectory'"
            return
        }
    }

    if ($FilePath) {
        $applicationName = $FilePath
    }
    else {
        # If -FilePath is not set then -CommandLine must have been used. Select the path based on the first entry.
        $applicationName = [Ansible.Windows.Process.ProcessUtil]::CommandLineToArgv($CommandLine)[0]
    }
    $applicationName = Resolve-ExecutablePath -FilePath $applicationName -WorkingDirectory $WorkingDirectory

    # When -ArgumentList is used, we need to escape each argument, including the FilePath to build our CommandLine.
    if ($PSCmdlet.ParameterSetName -eq 'ArgumentList') {
        $CommandLine = ConvertTo-EscapedArgument -InputObject $applicationName
        if ($ArgumentList.Count) {
            $escapedArguments = @($ArgumentList | ConvertTo-EscapedArgument)
            $CommandLine += " $($escapedArguments -join ' ')"
        }
    }

    $stdin = $null
    if ($InputObject) {
        if ($InputObject -is [byte[]]) {
            $stdin = $InputObject
        }
        elseif ($InputObject -is [string]) {
            $stdin = [Text.Encoding]::UTF8.GetBytes($InputObject)
        }
        else {
            Write-Error -Message "InputObject must be a string or byte[]"
            return
        }
    }

    $res = [Ansible.Windows.Process.ProcessUtil]::CreateProcess($applicationName, $CommandLine, $WorkingDirectory,
        $Environment, $stdin, $OutputEncodingOverride, $WaitChildren)

    [PSCustomObject]@{
        PSTypeName = 'Ansible.Windows.Process.Info'
        Command = $CommandLine
        Stdout = $res.StandardOut
        Stderr = $res.StandardError
        ExitCode = $res.ExitCode
    }
}

$exportMembers = @{
    Function = 'ConvertFrom-EscapedArgument', 'ConvertTo-EscapedArgument', 'Resolve-ExecutablePath', 'Start-AnsibleWindowsProcess'
}
Export-ModuleMember @exportMembers
