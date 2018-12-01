#!powershell

# Copyright: (c) 2015, George Frank <george@georgefrank.net>
# Copyright: (c) 2015, Adam Keech <akeech@chathamfinancial.com>
# Copyright: (c) 2015, Hans-Joachim Kliemeck <git@kliemeck.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil

$ErrorActionPreference = "Stop"

$params = Parse-Args $args

$result = @{
    changed = $false
}

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent","started","stopped","restarted" -resultobj $result

$application = Get-AnsibleParam -obj $params -name "application" -type "str"
$appParameters = Get-AnsibleParam -obj $params -name "app_parameters"
$appParametersFree  = Get-AnsibleParam -obj $params -name "app_parameters_free_form" -type "str"
$startMode = Get-AnsibleParam -obj $params -name "start_mode" -type "str" -default "auto" -validateset "auto","delayed","manual","disabled" -resultobj $result

$stdoutFile = Get-AnsibleParam -obj $params -name "stdout_file" -type "str"
$stderrFile = Get-AnsibleParam -obj $params -name "stderr_file" -type "str"
$dependencies = Get-AnsibleParam -obj $params -name "dependencies" -type "list"

$user = Get-AnsibleParam -obj $params -name "user" -type "str"
$password = Get-AnsibleParam -obj $params -name "password" -type "str"

if (($appParameters -ne $null) -and ($appParametersFree -ne $null))
{
    Fail-Json $result "Use either app_parameters or app_parameteres_free_form, but not both"
}
if (($appParameters -ne $null) -and ($appParameters -isnot [string])) {
    Fail-Json -obj $result -message "The app_parameters parameter must be a string representing a dictionary."
}

Function Nssm-Invoke
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$cmd
    )

    $nssm_result = Run-Command -command "nssm $cmd"

    return $nssm_result
}

Function Service-Exists
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name
    )

    return [bool](Get-Service "$name" -ErrorAction SilentlyContinue)
}

Function Nssm-Remove
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name
    )

    if (Service-Exists -name $name)
    {
        if ((Get-Service -Name $name).Status -ne "Stopped") {
            $cmd = "stop ""$name"""
            $nssm_result = Nssm-Invoke $cmd
        }
        $cmd = "remove ""$name"" confirm"
        $nssm_result = Nssm-Invoke $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error removing service ""$name"""
        }

        $result.changed_by = "remove_service"
        $result.changed = $true
     }
}

Function Nssm-Install
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name,
        [Parameter(Mandatory=$true)]
        [AllowEmptyString()]
        [string]$application
    )

    if (!$application)
    {
        Throw "Error installing service ""$name"". No application was supplied."
    }
    If (-Not (Test-Path -Path $application -PathType Leaf)) {
        Throw "$application does not exist on the host"
    }

    if (!(Service-Exists -name $name))
    {
        $nssm_result = Nssm-Invoke "install ""$name"" ""$application"""

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error installing service ""$name"""
        }

        $result.changed_by = "install_service"
        $result.changed = $true

     } else {
        $nssm_result = Nssm-Invoke "get ""$name"" Application"

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error installing service ""$name"""
        }

        if ($nssm_result.stdout.split("`n`r")[0] -ne $application)
        {
            $cmd = "set ""$name"" Application ""$application"""

            $nssm_result = Nssm-Invoke $cmd

            if ($nssm_result.rc -ne 0)
            {
                $result.nssm_error_cmd = $cmd
                $result.nssm_error_log = $nssm_result.stderr
                Throw "Error installing service ""$name"""
            }
            $result.application = "$application"

            $result.changed_by = "reinstall_service"
            $result.changed = $true
        }
     }

     if ($result.changed)
     {
        $applicationPath = (Get-Item $application).DirectoryName
        $cmd = "set ""$name"" AppDirectory ""$applicationPath"""

        $nssm_result = Nssm-Invoke $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error installing service ""$name"""
        }
     }
}

Function ParseAppParameters()
{
   [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [AllowEmptyString()]
        [string]$appParameters
    )

    $escapedAppParameters = $appParameters.TrimStart("@").TrimStart("{").TrimEnd("}").Replace("; ","`n").Replace("\","\\")

    return ConvertFrom-StringData -StringData $escapedAppParameters
}

Function Nssm-Update-AppParameters
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name,
        $appParameters,
        [string]$appParametersFree
    )

    $cmd = "get ""$name"" AppParameters"
    $nssm_result = Nssm-Invoke $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error updating AppParameters for service ""$name"""
    }

    $appParamKeys = @()
    $appParamVals = @()
    $singleLineParams = ""

    if ($null -ne $appParameters)
    {
        $appParametersHash = ParseAppParameters -appParameters $appParameters
        $appParamsArray = @()
        $appParametersHash.GetEnumerator() | foreach {
            $key = $($_.Name)
            $val = $($_.Value)

            $appParamKeys += $key
            $appParamVals += $val

            if ($key -ne "_") {
                $appParamsArray += $key
            }

            $appParamsArray += $val
        }

        $result.nssm_app_parameters_keys = $appParamKeys
        $result.nssm_app_parameters_vals = $appParamVals

        $singleLineParams = Argv-ToString -arguments $appParamsArray
    }
    elseif ($null -ne $appParametersFree) {
        $result.nssm_app_parameters_free_form = $appParametersFree
        $singleLineParams = $appParametersFree
    }

    $result.nssm_app_parameters = $appParameters
    $result.nssm_single_line_app_parameters = $singleLineParams

    if ($nssm_result.stdout.split("`n`r")[0] -ne $singleLineParams)
    {
        # Escape argument line to preserve possible quotes and spaces
        $singleLineParams = Escape-Argument -argument $singleLineParams
        $cmd = "set ""$name"" AppParameters $singleLineParams"

        $nssm_result = Nssm-Invoke $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error updating AppParameters for service ""$name"""
        }

        $result.changed_by = "update_app_parameters"
        $result.changed = $true
    }
}

Function Nssm-Set-Output-Files
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name,
        [string]$stdout,
        [string]$stderr
    )

    $cmd = "get ""$name"" AppStdout"
    $nssm_result = Nssm-Invoke $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error retrieving existing stdout file for service ""$name"""
    }

    if ($nssm_result.stdout.split("`n`r")[0] -ne $stdout)
    {
        if (!$stdout)
        {
            $cmd = "reset ""$name"" AppStdout"
        } else {
            $cmd = "set ""$name"" AppStdout $stdout"
        }

        $nssm_result = Nssm-Invoke $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error setting stdout file for service ""$name"""
        }

        $result.changed_by = "set_stdout"
        $result.changed = $true
    }

    $cmd = "get ""$name"" AppStderr"
    $nssm_result = Nssm-Invoke $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error retrieving existing stderr file for service ""$name"""
    }

    if ($nssm_result.stdout.split("`n`r")[0] -ne $stderr)
    {
        if (!$stderr)
        {
            $cmd = "reset ""$name"" AppStderr"
            $nssm_result = Nssm-Invoke $cmd

            if ($nssm_result.rc -ne 0)
            {
                $result.nssm_error_cmd = $cmd
                $result.nssm_error_log = $nssm_result.stderr
                Throw "Error clearing stderr file setting for service ""$name"""
            }
        } else {
            $cmd = "set ""$name"" AppStderr $stderr"
            $nssm_result = Nssm-Invoke $cmd

            if ($nssm_result.rc -ne 0)
            {
                $result.nssm_error_cmd = $cmd
                $result.nssm_error_log = $nssm_result.stderr
                Throw "Error setting stderr file for service ""$name"""
            }
        }

        $result.changed_by = "set_stderr"
        $result.changed = $true
    }

    ###
    # Setup file rotation so we don't accidentally consume too much disk
    ###

    #set files to overwrite
    $cmd = "set ""$name"" AppStdoutCreationDisposition 2"
    $nssm_result = Nssm-Invoke $cmd

    $cmd = "set ""$name"" AppStderrCreationDisposition 2"
    $nssm_result = Nssm-Invoke $cmd

    #enable file rotation
    $cmd = "set ""$name"" AppRotateFiles 1"
    $nssm_result = Nssm-Invoke $cmd

    #don't rotate until the service restarts
    $cmd = "set ""$name"" AppRotateOnline 0"
    $nssm_result = Nssm-Invoke $cmd

    #both of the below conditions must be met before rotation will happen
    #minimum age before rotating
    $cmd = "set ""$name"" AppRotateSeconds 86400"
    $nssm_result = Nssm-Invoke $cmd

    #minimum size before rotating
    $cmd = "set ""$name"" AppRotateBytes 104858"
    $nssm_result = Nssm-Invoke $cmd
}

Function Nssm-Update-Credentials
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name,
        [Parameter(Mandatory=$false)]
        [string]$user,
        [Parameter(Mandatory=$false)]
        [string]$password
    )

    $cmd = "get ""$name"" ObjectName"
    $nssm_result = Nssm-Invoke $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error updating credentials for service ""$name"""
    }

    if ($user) {
        if (!$password) {
            Throw "User without password is informed for service ""$name"""
        }
        else {
            $fullUser = $user
            If (-Not($user.contains("@")) -And ($user.Split("\").count -eq 1)) {
                $fullUser = ".\" + $user
            }

            If ($nssm_result.stdout.split("`n`r")[0] -ne $fullUser) {
                $cmd = Argv-ToString @("set", $name, "ObjectName", $fullUser, $password)
                $nssm_result = Nssm-Invoke $cmd

                if ($nssm_result.rc -ne 0)
                {
                    $result.nssm_error_cmd = $cmd
                    $result.nssm_error_log = $nssm_result.stderr
                    Throw "Error updating credentials for service ""$name"""
                }

                $result.changed_by = "update_credentials"
                $result.changed = $true
            }
        }
    }
}

Function Nssm-Update-Dependencies
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name,
        [Parameter(Mandatory=$false)]
        $dependencies
    )

    if($null -eq $dependencies) {
        # Don't make any change to dependencies if the parameter is omitted
        return
    }

    $cmd = "get ""$name"" DependOnService"
    $nssm_result = Nssm-Invoke $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error updating dependencies for service ""$name"""
    }

    $current_dependencies = @($nssm_result.stdout.split("`n`r") | where { $_ -ne '' })

    If (@(Compare-Object -ReferenceObject $current_dependencies -DifferenceObject $dependencies).Length -ne 0) {
        $dependencies_str = Argv-ToString -arguments $dependencies
        $cmd = "set ""$name"" DependOnService $dependencies_str"
        $nssm_result = Nssm-Invoke $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error updating dependencies for service ""$name"""
        }

        $result.changed_by = "update-dependencies"
        $result.changed = $true
    }
}

Function Nssm-Update-StartMode
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name,
        [Parameter(Mandatory=$true)]
        [string]$mode
    )

    $cmd = "get ""$name"" Start"
    $nssm_result = Nssm-Invoke $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error updating start mode for service ""$name"""
    }

    $modes=@{"auto" = "SERVICE_AUTO_START"; "delayed" = "SERVICE_DELAYED_AUTO_START"; "manual" = "SERVICE_DEMAND_START"; "disabled" = "SERVICE_DISABLED"}
    $mappedMode = $modes.$mode
    if ($nssm_result.stdout -notlike "*$mappedMode*") {
        $cmd = "set ""$name"" Start $mappedMode"
        $nssm_result = Nssm-Invoke $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error updating start mode for service ""$name"""
        }

        $result.changed_by = "start_mode"
        $result.changed = $true
    }
}

Function Nssm-Get-Status
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name
    )

    $cmd = "status ""$name"""
    $nssm_result = Nssm-Invoke $cmd

    return $nssm_result
}

Function Nssm-Start
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name
    )

    $currentStatus = Nssm-Get-Status -name $name

    if ($currentStatus.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $currentStatus.stderr
        Throw "Error starting service ""$name"""
    }

    switch -wildcard ($currentStatus.stdout)
    {
        "*SERVICE_RUNNING*" { <# Nothing to do #> }
        "*SERVICE_STOPPED*" { Nssm-Start-Service-Command -name $name }

        "*SERVICE_CONTINUE_PENDING*" { Nssm-Stop-Service-Command -name $name; Nssm-Start-Service-Command -name $name }
        "*SERVICE_PAUSE_PENDING*" { Nssm-Stop-Service-Command -name $name; Nssm-Start-Service-Command -name $name }
        "*SERVICE_PAUSED*" { Nssm-Stop-Service-Command -name $name; Nssm-Start-Service-Command -name $name }
        "*SERVICE_START_PENDING*" { Nssm-Stop-Service-Command -name $name; Nssm-Start-Service-Command -name $name }
        "*SERVICE_STOP_PENDING*" { Nssm-Stop-Service-Command -name $name; Nssm-Start-Service-Command -name $name }
    }
}

Function Nssm-Start-Service-Command
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name
    )

    $cmd = "start ""$name"""

    $nssm_result = Nssm-Invoke $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error starting service ""$name"""
    }

    $result.changed_by = "start_service"
    $result.changed = $true
}

Function Nssm-Stop-Service-Command
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name
    )

    $cmd = "stop ""$name"""

    $nssm_result = Nssm-Invoke $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error stopping service ""$name"""
    }

    $result.changed_by = "stop_service_command"
    $result.changed = $true
}

Function Nssm-Stop
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name
    )

    $currentStatus = Nssm-Get-Status -name $name

    if ($currentStatus.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $currentStatus.stderr
        Throw "Error stopping service ""$name"""
    }

    if ($currentStatus.stdout -notlike "*SERVICE_STOPPED*")
    {
        $cmd = "stop ""$name"""

        $nssm_result = Nssm-Invoke $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error stopping service ""$name"""
        }

        $result.changed_by = "stop_service"
        $result.changed = $true
    }
}

Function Nssm-Restart
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name
    )

    Nssm-Stop-Service-Command -name $name
    Nssm-Start-Service-Command -name $name
}

Function NssmProcedure
{
    Nssm-Install -name $name -application $application
    Nssm-Update-AppParameters -name $name -appParameters $appParameters -appParametersFree $appParametersFree
    Nssm-Set-Output-Files -name $name -stdout $stdoutFile -stderr $stderrFile
    Nssm-Update-Dependencies -name $name -dependencies $dependencies
    Nssm-Update-Credentials -name $name -user $user -password $password
    Nssm-Update-StartMode -name $name -mode $startMode
}

Try
{
    switch ($state)
    {
        "absent" {
            Nssm-Remove -name $name
        }
        "present" {
            NssmProcedure
        }
        "started" {
            NssmProcedure
            Nssm-Start -name $name
        }
        "stopped" {
            NssmProcedure
            Nssm-Stop -name $name
        }
        "restarted" {
            NssmProcedure
            Nssm-Restart -name $name
        }
    }

    Exit-Json $result
}
Catch
{
     Fail-Json $result $_.Exception.Message
}
