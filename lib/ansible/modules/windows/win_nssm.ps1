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

$start_modes_map = @{
    "auto" = "SERVICE_AUTO_START"
    "delayed" = "SERVICE_DELAYED_AUTO_START"
    "manual" = "SERVICE_DEMAND_START"
    "disabled" = "SERVICE_DISABLED"
}

$params = Parse-Args $args

$result = @{
    changed = $false
}

$name = Get-AnsibleParam -obj $params -name "name" -type "str" -failifempty $true
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "present" -validateset "present","absent","started","stopped","restarted" -resultobj $result

$application = Get-AnsibleParam -obj $params -name "application" -type "str"
$appParameters = Get-AnsibleParam -obj $params -name "app_parameters"
$appParametersFree  = Get-AnsibleParam -obj $params -name "app_parameters_free_form" -type "str"
$startMode = Get-AnsibleParam -obj $params -name "start_mode" -type "str" -default "auto" -validateset $start_modes_map.Keys -resultobj $result

$stdoutFile = Get-AnsibleParam -obj $params -name "stdout_file" -type "str"
$stderrFile = Get-AnsibleParam -obj $params -name "stderr_file" -type "str"
$dependencies = Get-AnsibleParam -obj $params -name "dependencies" -type "list"

$user = Get-AnsibleParam -obj $params -name "user" -type "str"
$password = Get-AnsibleParam -obj $params -name "password" -type "str"

function Invoke-NssmCommand {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true,ValueFromRemainingArguments=$true)]
        [string[]]$arguments
    )

    $executable = "nssm"
    $argument_string = Argv-ToString -arguments $arguments

    $command = "$executable $argument_string"
    $result = Run-Command -command $command

    #TODO Add this to CommandUtil.psm1 ?
    $result.arguments = $argument_string

    return $result
}

function Get-NssmServiceStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    return Invoke-NssmCommand -arguments @("status", $service)
}

function Get-NssmServiceParameter {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        [Parameter(Mandatory=$true)]
        [Alias("param")]
        [string]$parameter,
        [Parameter(Mandatory=$false)]
        [string]$subparameter
    )

    $arguments = @("get", $service, $parameter)
    if($subparameter -ne "") {
        $arguments += $subparameter
    }
    return Invoke-NssmCommand -arguments $arguments
}

function Set-NssmServiceParameter {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        [Parameter(Mandatory=$true)]
        [string]$parameter,
        [Parameter(Mandatory=$true,ValueFromRemainingArguments=$true)]
        [Alias("value")]
        [string[]]$arguments
    )

    return Invoke-NssmCommand -arguments (@("set", $service, $parameter) + $arguments)
}

function Reset-NssmServiceParameter {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        [Parameter(Mandatory=$true)]
        [Alias("param")]
        [string]$parameter
    )

    return Invoke-NssmCommand -arguments @("reset", $service, $parameter)
}

function Update-NssmServiceParameter {
    <#
    .SYNOPSIS
    A generic cmdlet to idempotently set a nssm service parameter.
    .PARAMETER service
    [String] The service name
    .PARAMETER parameter
    [String] The name of the nssm parameter to set.
    .PARAMETER arguments
    [String[]] Target value (or list of value) or array of arguments to pass to the 'nssm set' command.
    .PARAMETER compare
    [scriptblock] An optionnal idempotency check scriptblock that must return true when
    the current value is equal to the desired value. Usefull when 'nssm get' doesn't return
    the same value as 'nssm set' takes in argument, like for the ObjectName parameter.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,

        [Parameter(Mandatory=$true)]
        [string]$parameter,

        [Parameter(Mandatory=$true,ValueFromRemainingArguments=$true)]
        [AllowEmptyString()]
        [AllowNull()]
        [Alias("value")]
        [string[]]$arguments,

        [Parameter()]
        [scriptblock]$compare = {param($actual,$expected) @(Compare-Object -ReferenceObject $actual -DifferenceObject $expected).Length -eq 0}
    )

    if($null -eq $arguments) { return }
    $arguments = @($arguments | where { $_ -ne '' })

    $nssm_result = Get-NssmServiceParameter -service $service -parameter $parameter

    if ($nssm_result.rc -ne 0) {
        $result.nssm_error_cmd = $nssm_result.arguments
        $result.nssm_error_log = $nssm_result.stderr
        Fail-Json -obj $result -message "Error retrieving $parameter for service ""$service"""
    }

    $current_values = @($nssm_result.stdout.split("`n`r") | where { $_ -ne '' })

    if (-not $compare.Invoke($current_values,$arguments)) {
        if($arguments.Count -gt 0) {
            $nssm_result = Set-NssmServiceParameter -service $service -parameter $parameter -arguments $arguments
        }
        else {
            $nssm_result = Reset-NssmServiceParameter -service $service -parameter $parameter
        }

        if ($nssm_result.rc -ne 0) {
            $result.nssm_error_cmd = $nssm_result.arguments
            $result.nssm_error_log = $nssm_result.stderr
            Fail-Json -obj $result -message "Error setting $parameter for service ""$service"""
        }

        $result.changed_by = $parameter
        $result.changed = $true
    }
}

function Test-NssmServiceExists {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    return [bool](Get-Service "$service" -ErrorAction SilentlyContinue)
}

function Invoke-NssmStart {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    $nssm_result = Invoke-NssmCommand -arguments @("start", $service)

    if ($nssm_result.rc -ne 0) {
        $result.nssm_error_cmd = $nssm_result.arguments
        $result.nssm_error_log = $nssm_result.stderr
        Fail-Json -obj $result -message "Error starting service ""$service"""
    }

    $result.changed_by = "start_service"
    $result.changed = $true
}

function Invoke-NssmStop {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    $nssm_result = Invoke-NssmCommand -arguments @("stop", $service)

    if ($nssm_result.rc -ne 0) {
        $result.nssm_error_cmd = $nssm_result.arguments
        $result.nssm_error_log = $nssm_result.stderr
        Fail-Json -obj $result -message "Error stopping service ""$service"""
    }

    $result.changed_by = "stop_service_command"
    $result.changed = $true
}

function Start-NssmService {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    $currentStatus = Get-NssmServiceStatus -service $service

    if ($currentStatus.rc -ne 0) {
        $result.nssm_error_cmd = $currentStatus.arguments
        $result.nssm_error_log = $currentStatus.stderr
        Fail-Json -obj $result -message "Error starting service ""$service"""
    }

    switch -wildcard ($currentStatus.stdout) {
        "*SERVICE_RUNNING*" { <# Nothing to do #> }
        "*SERVICE_STOPPED*" { Invoke-NssmStart -service $service }

        "*SERVICE_CONTINUE_PENDING*" { Invoke-NssmStop -service $service; Invoke-NssmStart -service $service }
        "*SERVICE_PAUSE_PENDING*" { Invoke-NssmStop -service $service; Invoke-NssmStart -service $service }
        "*SERVICE_PAUSED*" { Invoke-NssmStop -service $service; Invoke-NssmStart -service $service }
        "*SERVICE_START_PENDING*" { Invoke-NssmStop -service $service; Invoke-NssmStart -service $service }
        "*SERVICE_STOP_PENDING*" { Invoke-NssmStop -service $service; Invoke-NssmStart -service $service }
    }
}

function Stop-NssmService {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    $currentStatus = Get-NssmServiceStatus -service $service

    if ($currentStatus.rc -ne 0) {
        $result.nssm_error_cmd = $currentStatus.arguments
        $result.nssm_error_log = $currentStatus.stderr
        Fail-Json -obj $result -message "Error stopping service ""$service"""
    }

    if ($currentStatus.stdout -notlike "*SERVICE_STOPPED*") {
        Invoke-NssmStop -service $service
        $result.changed_by = "stop_service"
    }
}

if (($appParameters -ne $null) -and ($appParametersFree -ne $null)) {
    Fail-Json $result "Use either app_parameters or app_parameteres_free_form, but not both"
}

if (($appParameters -ne $null) -and ($appParameters -isnot [string])) {
    Fail-Json -obj $result -message "The app_parameters parameter must be a string representing a dictionary."
}

if ($state -ne 'absent') {
    if ($null -eq $application) {
        Fail-Json -obj $result -message "The application parameter must be defined when the state is not absent."
    }

    if (-not (Test-Path -Path $application -PathType Leaf)) {
        Fail-Json -obj $result -message "The application specified ""$application"" does not exist on the host."
    }

    #TODO Add module parameter
    $applicationPath = (Get-Item $application).DirectoryName
}


$service_exists = Test-NssmServiceExists -service $name

if ($state -eq 'absent') {
    if ($service_exists) {
        if ((Get-Service -Name $name).Status -ne "Stopped") {
            $nssm_result = Invoke-NssmStop -service $name
        }

        $nssm_result = Invoke-NssmCommand -arguments @("remove", $name, "confirm")

        if ($nssm_result.rc -ne 0) {
            $result.nssm_error_cmd = $nssm_result.arguments
            $result.nssm_error_log = $nssm_result.stderr
            Fail-Json -obj $result -message "Error removing service ""$name"""
        }

        $result.changed_by = "remove_service"
        $result.changed = $true
    }
} else {
    if (-not $service_exists) {
        $nssm_result = Invoke-NssmCommand -arguments @("install", $name, $application)

        if ($nssm_result.rc -ne 0) {
            $result.nssm_error_cmd = $nssm_result.arguments
            $result.nssm_error_log = $nssm_result.stderr
            Fail-Json -obj $result -message "Error installing service ""$name"""
        }

        $result.changed_by = "install_service"
        $result.changed = $true

    } else {
        Update-NssmServiceParameter -service $name -parameter "Application" -value $application
    }

    Update-NssmServiceParameter -service $name -parameter "AppDirectory" -value $applicationPath

    $appParamKeys = @()
    $appParamVals = @()
    $singleLineParams = ""

    if ($null -ne $appParameters) {
        $escapedAppParameters = $appParameters.TrimStart("@").TrimStart("{").TrimEnd("}").Replace("; ","`n").Replace("\","\\")
        $appParametersHash = ConvertFrom-StringData -StringData $escapedAppParameters

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
    } elseif ($null -ne $appParametersFree) {
        $result.nssm_app_parameters_free_form = $appParametersFree
        $singleLineParams = $appParametersFree
    }

    $result.nssm_app_parameters = $appParameters
    $result.nssm_single_line_app_parameters = $singleLineParams

    Update-NssmServiceParameter -service $name -parameter "AppParameters" -value $singleLineParams


    Update-NssmServiceParameter -service $name -parameter "AppStdout" -value $stdoutFile
    Update-NssmServiceParameter -service $name -parameter "AppStderr" -value $stderrFile

    ###
    # Setup file rotation so we don't accidentally consume too much disk
    ###

    #set files to overwrite
    Update-NssmServiceParameter -service $name -parameter "AppStdoutCreationDisposition" -value 2
    Update-NssmServiceParameter -service $name -parameter "AppStderrCreationDisposition" -value 2

    #enable file rotation
    Update-NssmServiceParameter -service $name -parameter "AppRotateFiles" -value 1

    #don't rotate until the service restarts
    Update-NssmServiceParameter -service $name -parameter "AppRotateOnline" -value 0

    #both of the below conditions must be met before rotation will happen
    #minimum age before rotating
    Update-NssmServiceParameter -service $name -parameter "AppRotateSeconds" -value 86400

    #minimum size before rotating
    Update-NssmServiceParameter -service $name -parameter "AppRotateBytes" -value 104858


    if($null -ne $dependencies) {
        Update-NssmServiceParameter -service $name -parameter "DependOnService" -arguments $dependencies
    }

    if ($user) {
        $fullUser = $user
        if (!$password) {
            Fail-Json -obj $result -message "User without password is informed for service ""$name"""
        }

        if (-Not($user.contains("@")) -And ($user.Split("\").count -eq 1)) {
            $fullUser = ".\" + $user
        }

        # Use custom compare callback to test only the username (and not the password)
        Update-NssmServiceParameter -service $name -parameter "ObjectName" -arguments @($fullUser, $password) -compare {param($actual,$expected) $actual[0] -eq $expected[0]}
    }

    $mappedMode = $start_modes_map.$startMode
    Update-NssmServiceParameter -service $name -parameter "Start" -value $mappedMode

    if ($state -in "stopped","restarted") {
        Stop-NssmService -service $name
    }

    if($state -in "started","restarted") {
        Start-NssmService -service $name
    }
}

Exit-Json $result
