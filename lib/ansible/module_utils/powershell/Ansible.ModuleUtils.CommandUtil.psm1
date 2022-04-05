# Copyright (c) 2017 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

#AnsibleRequires -CSharpUtil Ansible.Process

Function Get-ExecutablePath {
    <#
    .SYNOPSIS
    Get's the full path to an executable, will search the directory specified or ones in the PATH env var.

    .PARAMETER executable
    [String]The executable to search for.

    .PARAMETER directory
    [String] If set, the directory to search in.

    .OUTPUT
    [String] The full path the executable specified.
    #>
    Param(
        [String]$executable,
        [String]$directory = $null
    )

    # we need to add .exe if it doesn't have an extension already
    if (-not [System.IO.Path]::HasExtension($executable)) {
        $executable = "$($executable).exe"
    }
    $full_path = [System.IO.Path]::GetFullPath($executable)

    if ($full_path -ne $executable -and $directory -ne $null) {
        $file = Get-Item -LiteralPath "$directory\$executable" -Force -ErrorAction SilentlyContinue
    }
    else {
        $file = Get-Item -LiteralPath $executable -Force -ErrorAction SilentlyContinue
    }

    if ($null -ne $file) {
        $executable_path = $file.FullName
    }
    else {
        $executable_path = [Ansible.Process.ProcessUtil]::SearchPath($executable)
    }
    return $executable_path
}

Function Run-Command {
    <#
    .SYNOPSIS
    Run a command with the CreateProcess API and return the stdout/stderr and return code.

    .PARAMETER command
    The full command, including the executable, to run.

    .PARAMETER working_directory
    The working directory to set on the new process, will default to the current working dir.

    .PARAMETER stdin
    A string to sent over the stdin pipe to the new process.

    .PARAMETER environment
    A hashtable of key/value pairs to run with the command. If set, it will replace all other env vars.

    .PARAMETER output_encoding_override
    The character encoding name for decoding stdout/stderr output of the process.

    .OUTPUT
    [Hashtable]
        [String]executable - The full path to the executable that was run
        [String]stdout - The stdout stream of the process
        [String]stderr - The stderr stream of the process
        [Int32]rc - The return code of the process
    #>
    Param(
        [string]$command,
        [string]$working_directory = $null,
        [string]$stdin = "",
        [hashtable]$environment = @{},
        [string]$output_encoding_override = $null
    )

    # need to validate the working directory if it is set
    if ($working_directory) {
        # validate working directory is a valid path
        if (-not (Test-Path -LiteralPath $working_directory)) {
            throw "invalid working directory path '$working_directory'"
        }
    }

    # lpApplicationName needs to be the full path to an executable, we do this
    # by getting the executable as the first arg and then getting the full path
    $arguments = [Ansible.Process.ProcessUtil]::ParseCommandLine($command)
    $executable = Get-ExecutablePath -executable $arguments[0] -directory $working_directory

    # run the command and get the results
    $command_result = [Ansible.Process.ProcessUtil]::CreateProcess($executable, $command, $working_directory, $environment, $stdin, $output_encoding_override)

    return , @{
        executable = $executable
        stdout = $command_result.StandardOut
        stderr = $command_result.StandardError
        rc = $command_result.ExitCode
    }
}

# this line must stay at the bottom to ensure all defined module parts are exported
Export-ModuleMember -Function Get-ExecutablePath, Run-Command
