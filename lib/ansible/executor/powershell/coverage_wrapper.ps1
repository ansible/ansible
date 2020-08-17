# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

param(
    [Parameter(Mandatory=$true)][System.Collections.IDictionary]$Payload
)

#AnsibleRequires -Wrapper module_wrapper

$ErrorActionPreference = "Stop"

Write-AnsibleLog "INFO - starting coverage_wrapper" "coverage_wrapper"

# Required to be set for psrp to we can set a breakpoint in the remote runspace
if ($PSVersionTable.PSVersion -ge [Version]'4.0') {
    $host.Runspace.Debugger.SetDebugMode([System.Management.Automation.DebugModes]::RemoteScript)
}

Function New-CoverageBreakpoint {
    Param (
        [String]$Path,
        [ScriptBlock]$Code,
        [String]$AnsiblePath
    )

    # It is quicker to pass in the code as a string instead of calling ParseFile as we already know the contents
    $predicate = {
        $args[0] -is [System.Management.Automation.Language.CommandBaseAst]
    }
    $script_cmds = $Code.Ast.FindAll($predicate, $true)

    # Create an object that tracks the Ansible path of the file and the breakpoints that have been set in it
    $info = [PSCustomObject]@{
        Path = $AnsiblePath
        Breakpoints = [System.Collections.Generic.List`1[System.Management.Automation.Breakpoint]]@()
    }

    # Keep track of lines that are already scanned. PowerShell can contains multiple commands in 1 line
    $scanned_lines = [System.Collections.Generic.HashSet`1[System.Int32]]@()
    foreach ($cmd in $script_cmds) {
        if (-not $scanned_lines.Add($cmd.Extent.StartLineNumber)) {
            continue
        }

        # Do not add any -Action value, even if it is $null or {}. Doing so will balloon the runtime.
        $params = @{
            Script = $Path
            Line = $cmd.Extent.StartLineNumber
            Column = $cmd.Extent.StartColumnNumber
        }
        $info.Breakpoints.Add((Set-PSBreakpoint @params))
    }

    $info
}

Function Compare-PathFilterPattern {
    Param (
        [String[]]$Patterns,
        [String]$Path
    )

    foreach ($pattern in $Patterns) {
        if ($Path -like $pattern) {
            return $true
        }
    }
    return $false
}

$module_name = $Payload.module_args["_ansible_module_name"]
Write-AnsibleLog "INFO - building coverage payload for '$module_name'" "coverage_wrapper"

# A PS Breakpoint needs an actual path to work properly, we create a temp directory that will store the module and
# module_util code during execution
$temp_path = Join-Path -Path ([System.IO.Path]::GetTempPath()) -ChildPath "ansible-coverage-$([System.IO.Path]::GetRandomFileName())"
Write-AnsibleLog "INFO - Creating temp path for coverage files '$temp_path'" "coverage_wrapper"
New-Item -Path $temp_path -ItemType Directory > $null
$breakpoint_info = [System.Collections.Generic.List`1[PSObject]]@()

# Ensures we create files with UTF-8 encoding and a BOM. This is critical to force the powershell engine to read files
# as UTF-8 and not as the system's codepage.
$file_encoding = 'UTF8'

try {
    $scripts = [System.Collections.Generic.List`1[System.Object]]@($script:common_functions)

    $coverage_path_filter = $Payload.coverage.path_filter.Split(":", [StringSplitOptions]::RemoveEmptyEntries)

    # We need to track what utils have already been added to the script for loading. This is because the load
    # order is important and can have module_utils that rely on other utils.
    $loaded_utils = [System.Collections.Generic.HashSet`1[System.String]]@()
    $parse_util = {
        $util_name = $args[0]
        if (-not $loaded_utils.Add($util_name)) {
            return
        }

        $util_code = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.powershell_modules.$util_name))
        $util_sb = [ScriptBlock]::Create($util_code)
        $util_path = Join-Path -Path $temp_path -ChildPath "$($util_name).psm1"

        Write-AnsibleLog "INFO - Outputting module_util $util_name to temp file '$util_path'" "coverage_wrapper"
        Set-Content -LiteralPath $util_path -Value $util_code -Encoding $file_encoding

        $ansible_path = $Payload.coverage.module_util_paths.$util_name
        if ((Compare-PathFilterPattern -Patterns $coverage_path_filter -Path $ansible_path)) {
            $cov_params = @{
                Path = $util_path
                Code = $util_sb
                AnsiblePath = $ansible_path
            }
            $breakpoints = New-CoverageBreakpoint @cov_params
            $breakpoint_info.Add($breakpoints)
        }

        if ($null -ne $util_sb.Ast.ScriptRequirements) {
            foreach ($required_util in $util_sb.Ast.ScriptRequirements.RequiredModules) {
                &$parse_util $required_util.Name
            }
        }
        Write-AnsibleLog "INFO - Adding util $util_name to scripts to run" "coverage_wrapper"
        $scripts.Add("Import-Module -Name '$util_path'")
    }
    foreach ($util in $Payload.powershell_modules.Keys) {
        &$parse_util $util
    }

    $module = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($Payload.module_entry))
    $module_path = Join-Path -Path $temp_path -ChildPath "$($module_name).ps1"
    Write-AnsibleLog "INFO - Ouputting module $module_name to temp file '$module_path'" "coverage_wrapper"
    Set-Content -LiteralPath $module_path -Value $module -Encoding $file_encoding
    $scripts.Add($module_path)

    $ansible_path = $Payload.coverage.module_path
    if ((Compare-PathFilterPattern -Patterns $coverage_path_filter -Path $ansible_path)) {
        $cov_params = @{
            Path = $module_path
            Code = [ScriptBlock]::Create($module)
            AnsiblePath = $Payload.coverage.module_path
        }
        $breakpoints = New-CoverageBreakpoint @cov_params
        $breakpoint_info.Add($breakpoints)
    }

    $variables = [System.Collections.ArrayList]@(@{ Name = "complex_args"; Value = $Payload.module_args; Scope = "Global" })
    $entrypoint = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($payload.module_wrapper))
    $entrypoint = [ScriptBlock]::Create($entrypoint)

    $params = @{
        Scripts = $scripts
        Variables = $variables
        Environment = $Payload.environment
        ModuleName = $module_name
    }
    if ($breakpoint_info) {
        $params.Breakpoints = $breakpoint_info.Breakpoints
    }

    try {
        &$entrypoint @params
    } finally {
        # Processing here is kept to an absolute minimum to make sure each task runtime is kept as small as
        # possible. Once all the tests have been run ansible-test will collect this info and process it locally in
        # one go.
        Write-AnsibleLog "INFO - Creating coverage result output" "coverage_wrapper"
        $coverage_info = @{}
        foreach ($info in $breakpoint_info) {
            $coverage_info.($info.Path) = $info.Breakpoints | Select-Object -Property Line, HitCount
        }

        # The coverage.output value is a filename set by the Ansible controller. We append some more remote side
        # info to the filename to make it unique and identify the remote host a bit more.
        $ps_version = "$($PSVersionTable.PSVersion.Major).$($PSVersionTable.PSVersion.Minor)"
        $coverage_output_path = "$($Payload.coverage.output)=powershell-$ps_version=coverage.$($env:COMPUTERNAME).$PID.$(Get-Random)"
        $code_cov_json = ConvertTo-Json -InputObject $coverage_info -Compress

        Write-AnsibleLog "INFO - Outputting coverage json to '$coverage_output_path'" "coverage_wrapper"
        # Ansible controller expects these files to be UTF-8 without a BOM, use .NET for this.
        $utf8_no_bom = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false
        [System.IO.File]::WriteAllbytes($coverage_output_path, $utf8_no_bom.GetBytes($code_cov_json))
    }
} finally {
    try {
        if ($breakpoint_info) {
            foreach ($b in $breakpoint_info.Breakpoints) {
                Remove-PSBreakpoint -Breakpoint $b
            }
        }
    } finally {
        Write-AnsibleLog "INFO - Remove temp coverage folder '$temp_path'" "coverage_wrapper"
        Remove-Item -LiteralPath $temp_path -Force -Recurse
    }
}

Write-AnsibleLog "INFO - ending coverage_wrapper" "coverage_wrapper"
