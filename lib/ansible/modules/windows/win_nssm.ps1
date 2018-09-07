#!powershell

# Copyright: (c) 2015, George Frank <george@georgefrank.net>
# Copyright: (c) 2015, Adam Keech <akeech@chathamfinancial.com>
# Copyright: (c) 2015, Hans-Joachim Kliemeck <git@kliemeck.de>
# Copyright: (c) 2018, Kevin Subileau (@ksubileau)
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

Function Invoke-NssmCommand
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$cmd
    )

    $nssm_result = Run-Command -command "nssm $cmd"

    return $nssm_result
}

Function Test-NssmServiceExists
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    return [bool](Get-Service "$service" -ErrorAction SilentlyContinue)
}

Function Uninstall-NssmService
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    if (Test-NssmServiceExists -service $service)
    {
        if ((Get-Service -Name $service).Status -ne "Stopped") {
            $cmd = "stop ""$service"""
            $nssm_result = Invoke-NssmCommand $cmd
        }
        $cmd = "remove ""$service"" confirm"
        $nssm_result = Invoke-NssmCommand $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error removing service ""$service"""
        }

        $result.changed_by = "remove_service"
        $result.changed = $true
     }
}

Function Install-NssmService
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        [Parameter(Mandatory=$true)]
        [AllowEmptyString()]
        [string]$application
    )

    if (!$application)
    {
        Throw "Error installing service ""$service"". No application was supplied."
    }
    If (-Not (Test-Path -Path $application -PathType Leaf)) {
        Throw "$application does not exist on the host"
    }

    if (!(Test-NssmServiceExists -service $service))
    {
        $nssm_result = Invoke-NssmCommand "install ""$service"" ""$application"""

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error installing service ""$service"""
        }

        $result.changed_by = "install_service"
        $result.changed = $true

     } else {
        $nssm_result = Invoke-NssmCommand "get ""$service"" Application"

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error installing service ""$service"""
        }

        if ($nssm_result.stdout.split("`n`r")[0] -ne $application)
        {
            $cmd = "set ""$service"" Application ""$application"""

            $nssm_result = Invoke-NssmCommand $cmd

            if ($nssm_result.rc -ne 0)
            {
                $result.nssm_error_cmd = $cmd
                $result.nssm_error_log = $nssm_result.stderr
                Throw "Error installing service ""$service"""
            }
            $result.application = "$application"

            $result.changed_by = "reinstall_service"
            $result.changed = $true
        }
     }

     if ($result.changed)
     {
        $applicationPath = (Get-Item $application).DirectoryName
        $cmd = "set ""$service"" AppDirectory ""$applicationPath"""

        $nssm_result = Invoke-NssmCommand $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error installing service ""$service"""
        }
     }
}

Function Parse-AppParameters
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

Function Update-NssmServiceAppParameters
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        $appParameters,
        [string]$appParametersFree
    )

    $cmd = "get ""$service"" AppParameters"
    $nssm_result = Invoke-NssmCommand $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error updating AppParameters for service ""$service"""
    }

    $appParamKeys = @()
    $appParamVals = @()
    $singleLineParams = ""

    if ($null -ne $appParameters)
    {
        $appParametersHash = Parse-AppParameters -appParameters $appParameters
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
        $cmd = "set ""$service"" AppParameters $singleLineParams"

        $nssm_result = Invoke-NssmCommand $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error updating AppParameters for service ""$service"""
        }

        $result.changed_by = "update_app_parameters"
        $result.changed = $true
    }
}

Function Update-NssmServiceOutputFiles
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        [string]$stdout,
        [string]$stderr
    )

    $cmd = "get ""$service"" AppStdout"
    $nssm_result = Invoke-NssmCommand $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error retrieving existing stdout file for service ""$service"""
    }

    if ($nssm_result.stdout.split("`n`r")[0] -ne $stdout)
    {
        if (!$stdout)
        {
            $cmd = "reset ""$service"" AppStdout"
        } else {
            $cmd = "set ""$service"" AppStdout $stdout"
        }

        $nssm_result = Invoke-NssmCommand $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error setting stdout file for service ""$service"""
        }

        $result.changed_by = "set_stdout"
        $result.changed = $true
    }

    $cmd = "get ""$service"" AppStderr"
    $nssm_result = Invoke-NssmCommand $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error retrieving existing stderr file for service ""$service"""
    }

    if ($nssm_result.stdout.split("`n`r")[0] -ne $stderr)
    {
        if (!$stderr)
        {
            $cmd = "reset ""$service"" AppStderr"
            $nssm_result = Invoke-NssmCommand $cmd

            if ($nssm_result.rc -ne 0)
            {
                $result.nssm_error_cmd = $cmd
                $result.nssm_error_log = $nssm_result.stderr
                Throw "Error clearing stderr file setting for service ""$service"""
            }
        } else {
            $cmd = "set ""$service"" AppStderr $stderr"
            $nssm_result = Invoke-NssmCommand $cmd

            if ($nssm_result.rc -ne 0)
            {
                $result.nssm_error_cmd = $cmd
                $result.nssm_error_log = $nssm_result.stderr
                Throw "Error setting stderr file for service ""$service"""
            }
        }

        $result.changed_by = "set_stderr"
        $result.changed = $true
    }

    ###
    # Setup file rotation so we don't accidentally consume too much disk
    ###

    #set files to overwrite
    $cmd = "set ""$service"" AppStdoutCreationDisposition 2"
    $nssm_result = Invoke-NssmCommand $cmd

    $cmd = "set ""$service"" AppStderrCreationDisposition 2"
    $nssm_result = Invoke-NssmCommand $cmd

    #enable file rotation
    $cmd = "set ""$service"" AppRotateFiles 1"
    $nssm_result = Invoke-NssmCommand $cmd

    #don't rotate until the service restarts
    $cmd = "set ""$service"" AppRotateOnline 0"
    $nssm_result = Invoke-NssmCommand $cmd

    #both of the below conditions must be met before rotation will happen
    #minimum age before rotating
    $cmd = "set ""$service"" AppRotateSeconds 86400"
    $nssm_result = Invoke-NssmCommand $cmd

    #minimum size before rotating
    $cmd = "set ""$service"" AppRotateBytes 104858"
    $nssm_result = Invoke-NssmCommand $cmd
}

Function Update-NssmServiceCredentials
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        [Parameter(Mandatory=$false)]
        [string]$user,
        [Parameter(Mandatory=$false)]
        [string]$password
    )

    $cmd = "get ""$service"" ObjectName"
    $nssm_result = Invoke-NssmCommand $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error updating credentials for service ""$service"""
    }

    if ($user) {
        if (!$password) {
            Throw "User without password is informed for service ""$service"""
        }
        else {
            $fullUser = $user
            If (-Not($user.contains("@")) -And ($user.Split("\").count -eq 1)) {
                $fullUser = ".\" + $user
            }

            If ($nssm_result.stdout.split("`n`r")[0] -ne $fullUser) {
                $cmd = "set ""$service"" ObjectName $fullUser '$password'"
                $nssm_result = Invoke-NssmCommand $cmd

                if ($nssm_result.rc -ne 0)
                {
                    $result.nssm_error_cmd = $cmd
                    $result.nssm_error_log = $nssm_result.stderr
                    Throw "Error updating credentials for service ""$service"""
                }

                $result.changed_by = "update_credentials"
                $result.changed = $true
            }
        }
    }
}

Function Update-NssmServiceDependencies
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        [Parameter(Mandatory=$false)]
        $dependencies
    )

    if($null -eq $dependencies) {
        # Don't make any change to dependencies if the parameter is omitted
        return
    }

    $cmd = "get ""$service"" DependOnService"
    $nssm_result = Invoke-NssmCommand $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error updating dependencies for service ""$service"""
    }

    $current_dependencies = @($nssm_result.stdout.split("`n`r") | where { $_ -ne '' })

    If (@(Compare-Object -ReferenceObject $current_dependencies -DifferenceObject $dependencies).Length -ne 0) {
        $dependencies_str = Argv-ToString -arguments $dependencies
        $cmd = "set ""$service"" DependOnService $dependencies_str"
        $nssm_result = Invoke-NssmCommand $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error updating dependencies for service ""$service"""
        }

        $result.changed_by = "update-dependencies"
        $result.changed = $true
    }
}

Function Update-NssmServiceStartMode
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        [Parameter(Mandatory=$true)]
        [string]$mode
    )

    $cmd = "get ""$service"" Start"
    $nssm_result = Invoke-NssmCommand $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error updating start mode for service ""$service"""
    }

    $modes=@{"auto" = "SERVICE_AUTO_START"; "delayed" = "SERVICE_DELAYED_AUTO_START"; "manual" = "SERVICE_DEMAND_START"; "disabled" = "SERVICE_DISABLED"}
    $mappedMode = $modes.$mode
    if ($nssm_result.stdout -notlike "*$mappedMode*") {
        $cmd = "set ""$service"" Start $mappedMode"
        $nssm_result = Invoke-NssmCommand $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error updating start mode for service ""$service"""
        }

        $result.changed_by = "start_mode"
        $result.changed = $true
    }
}

Function Get-NssmServiceStatus
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    $cmd = "status ""$service"""
    $nssm_result = Invoke-NssmCommand $cmd

    return $nssm_result
}

Function Start-NssmService
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    $currentStatus = Get-NssmServiceStatus -service $service

    if ($currentStatus.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $currentStatus.stderr
        Throw "Error starting service ""$service"""
    }

    switch -wildcard ($currentStatus.stdout)
    {
        "*SERVICE_RUNNING*" { <# Nothing to do #> }
        "*SERVICE_STOPPED*" { Invoke-NssmStart -service $service }

        "*SERVICE_CONTINUE_PENDING*" { Invoke-NssmStop -service $service; Invoke-NssmStart -service $service }
        "*SERVICE_PAUSE_PENDING*" { Invoke-NssmStop -service $service; Invoke-NssmStart -service $service }
        "*SERVICE_PAUSED*" { Invoke-NssmStop -service $service; Invoke-NssmStart -service $service }
        "*SERVICE_START_PENDING*" { Invoke-NssmStop -service $service; Invoke-NssmStart -service $service }
        "*SERVICE_STOP_PENDING*" { Invoke-NssmStop -service $service; Invoke-NssmStart -service $service }
    }
}

Function Invoke-NssmStart
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    $cmd = "start ""$service"""

    $nssm_result = Invoke-NssmCommand $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error starting service ""$service"""
    }

    $result.changed_by = "start_service"
    $result.changed = $true
}

Function Invoke-NssmStop
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    $cmd = "stop ""$service"""

    $nssm_result = Invoke-NssmCommand $cmd

    if ($nssm_result.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $nssm_result.stderr
        Throw "Error stopping service ""$service"""
    }

    $result.changed_by = "stop_service_command"
    $result.changed = $true
}

Function Stop-NssmService
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    $currentStatus = Get-NssmServiceStatus -service $service

    if ($currentStatus.rc -ne 0)
    {
        $result.nssm_error_cmd = $cmd
        $result.nssm_error_log = $currentStatus.stderr
        Throw "Error stopping service ""$service"""
    }

    if ($currentStatus.stdout -notlike "*SERVICE_STOPPED*")
    {
        $cmd = "stop ""$service"""

        $nssm_result = Invoke-NssmCommand $cmd

        if ($nssm_result.rc -ne 0)
        {
            $result.nssm_error_cmd = $cmd
            $result.nssm_error_log = $nssm_result.stderr
            Throw "Error stopping service ""$service"""
        }

        $result.changed_by = "stop_service"
        $result.changed = $true
    }
}

Function Restart-NssmService
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    Invoke-NssmStop -service $service
    Invoke-NssmStart -service $service
}

Function NssmProcedure
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    Install-NssmService -service $service -application $application
    Update-NssmServiceAppParameters -service $service -appParameters $appParameters -appParametersFree $appParametersFree
    Update-NssmServiceOutputFiles -service $service -stdout $stdoutFile -stderr $stderrFile
    Update-NssmServiceDependencies -service $service -dependencies $dependencies
    Update-NssmServiceCredentials -service $service -user $user -password $password
    Update-NssmServiceStartMode -service $service -mode $startMode
}

Try
{
    switch ($state)
    {
        "absent" {
            Uninstall-NssmService -service $name
        }
        "present" {
            NssmProcedure -service $name
        }
        "started" {
            NssmProcedure -service $name
            Start-NssmService -service $name
        }
        "stopped" {
            NssmProcedure -service $name
            Stop-NssmService -service $name
        }
        "restarted" {
            NssmProcedure -service $name
            Restart-NssmService -service $name
        }
    }

    Exit-Json $result
}
Catch
{
     Fail-Json $result $_.Exception.Message
}
