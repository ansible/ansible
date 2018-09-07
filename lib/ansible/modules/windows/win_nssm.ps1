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

function Test-NssmServiceExists {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    return [bool](Get-Service "$service" -ErrorAction SilentlyContinue)
}

function Install-NssmService {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        [Parameter(Mandatory=$true)]
        [AllowEmptyString()]
        [string]$application
    )

    if (!$application) {
        Fail-Json -obj $result -message "Error installing service ""$service"". No application was supplied."
    }
    if (-Not (Test-Path -Path $application -PathType Leaf)) {
        Fail-Json -obj $result -message "$application does not exist on the host"
    }

    if (!(Test-NssmServiceExists -service $service)) {
        $nssm_result = Invoke-NssmCommand -arguments @("install", $service, $application)

        if ($nssm_result.rc -ne 0) {
            $result.nssm_error_cmd = $nssm_result.arguments
            $result.nssm_error_log = $nssm_result.stderr
            Fail-Json -obj $result -message "Error installing service ""$service"""
        }

        $result.changed_by = "install_service"
        $result.changed = $true

    } else {
        $nssm_result = Invoke-NssmCommand -arguments @("get", $service, "Application")

        if ($nssm_result.rc -ne 0) {
            $result.nssm_error_cmd = $nssm_result.arguments
            $result.nssm_error_log = $nssm_result.stderr
            Fail-Json -obj $result -message "Error installing service ""$service"""
        }

        if ($nssm_result.stdout.split("`n`r")[0] -ne $application) {
            $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "Application", $application)

            if ($nssm_result.rc -ne 0) {
                $result.nssm_error_cmd = $nssm_result.arguments
                $result.nssm_error_log = $nssm_result.stderr
                Fail-Json -obj $result -message "Error installing service ""$service"""
            }
            $result.application = "$application"

            $result.changed_by = "reinstall_service"
            $result.changed = $true
        }
    }

    if ($result.changed) {
        $applicationPath = (Get-Item $application).DirectoryName

        $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "AppDirectory", $applicationPath)

        if ($nssm_result.rc -ne 0) {
            $result.nssm_error_cmd = $nssm_result.arguments
            $result.nssm_error_log = $nssm_result.stderr
            Fail-Json -obj $result -message "Error installing service ""$service"""
        }
    }
}

function Uninstall-NssmService {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service
    )

    if (Test-NssmServiceExists -service $service) {
        if ((Get-Service -Name $service).Status -ne "Stopped") {
            $nssm_result = Invoke-NssmCommand -arguments @("stop", $service)
        }

        $nssm_result = Invoke-NssmCommand -arguments @("remove", $service, "confirm")

        if ($nssm_result.rc -ne 0) {
            $result.nssm_error_cmd = $nssm_result.arguments
            $result.nssm_error_log = $nssm_result.stderr
            Fail-Json -obj $result -message "Error removing service ""$service"""
        }

        $result.changed_by = "remove_service"
        $result.changed = $true
    }
}

function Parse-AppParameters
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

function Update-NssmServiceAppParameters {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        $appParameters,
        [string]$appParametersFree
    )

    $nssm_result = Invoke-NssmCommand -arguments @("get", $service, "AppParameters")

    if ($nssm_result.rc -ne 0) {
        $result.nssm_error_cmd = $nssm_result.arguments
        $result.nssm_error_log = $nssm_result.stderr
        Fail-Json -obj $result -message "Error updating AppParameters for service ""$service"""
    }

    $appParamKeys = @()
    $appParamVals = @()
    $singleLineParams = ""

    if ($null -ne $appParameters) {
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

    if ($nssm_result.stdout.split("`n`r")[0] -ne $singleLineParams) {
        $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "AppParameters", $singleLineParams)

        if ($nssm_result.rc -ne 0) {
            $result.nssm_error_cmd = $nssm_result.arguments
            $result.nssm_error_log = $nssm_result.stderr
            Fail-Json -obj $result -message "Error updating AppParameters for service ""$service"""
        }

        $result.changed_by = "update_app_parameters"
        $result.changed = $true
    }
}

function Update-NssmServiceOutputFiles {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        [string]$stdout,
        [string]$stderr
    )

    $nssm_result = Invoke-NssmCommand -arguments @("get", $service, "AppStdout")

    if ($nssm_result.rc -ne 0) {
        $result.nssm_error_cmd = $nssm_result.arguments
        $result.nssm_error_log = $nssm_result.stderr
        Fail-Json -obj $result -message "Error retrieving existing stdout file for service ""$service"""
    }

    if ($nssm_result.stdout.split("`n`r")[0] -ne $stdout) {
        if (!$stdout) {
            $nssm_result = Invoke-NssmCommand -arguments @("reset", $service, "AppStdout")
        } else {
            $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "AppStdout", $stdout)
        }

        if ($nssm_result.rc -ne 0) {
            $result.nssm_error_cmd = $nssm_result.arguments
            $result.nssm_error_log = $nssm_result.stderr
            Fail-Json -obj $result -message "Error setting stdout file for service ""$service"""
        }

        $result.changed_by = "set_stdout"
        $result.changed = $true
    }

    $nssm_result = Invoke-NssmCommand -arguments @("get", $service, "AppStderr")

    if ($nssm_result.rc -ne 0) {
        $result.nssm_error_cmd = $nssm_result.arguments
        $result.nssm_error_log = $nssm_result.stderr
        Fail-Json -obj $result -message "Error retrieving existing stderr file for service ""$service"""
    }

    if ($nssm_result.stdout.split("`n`r")[0] -ne $stderr) {
        if (!$stderr) {
            $nssm_result = Invoke-NssmCommand -arguments @("reset", $service, "AppStderr")

            if ($nssm_result.rc -ne 0) {
                $result.nssm_error_cmd = $nssm_result.arguments
                $result.nssm_error_log = $nssm_result.stderr
                Fail-Json -obj $result -message "Error clearing stderr file setting for service ""$service"""
            }
        } else {
            $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "AppStderr", $stderr)

            if ($nssm_result.rc -ne 0) {
                $result.nssm_error_cmd = $nssm_result.arguments
                $result.nssm_error_log = $nssm_result.stderr
                Fail-Json -obj $result -message "Error setting stderr file for service ""$service"""
            }
        }

        $result.changed_by = "set_stderr"
        $result.changed = $true
    }

    ###
    # Setup file rotation so we don't accidentally consume too much disk
    ###

    #set files to overwrite
    $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "AppStdoutCreationDisposition", "2")
    $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "AppStderrCreationDisposition", "2")

    #enable file rotation
    $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "AppRotateFiles", "1")

    #don't rotate until the service restarts
    $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "AppRotateOnline", "0")

    #both of the below conditions must be met before rotation will happen
    #minimum age before rotating
    $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "AppRotateSeconds", "86400")

    #minimum size before rotating
    $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "AppRotateBytes", "104858")
}

function Update-NssmServiceCredentials {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        [Parameter(Mandatory=$false)]
        [string]$user,
        [Parameter(Mandatory=$false)]
        [string]$password
    )

    $nssm_result = Invoke-NssmCommand -arguments @("get", $service, "ObjectName")

    if ($nssm_result.rc -ne 0) {
        $result.nssm_error_cmd = $nssm_result.arguments
        $result.nssm_error_log = $nssm_result.stderr
        Fail-Json -obj $result -message "Error updating credentials for service ""$service"""
    }

    if ($user) {
        if (!$password) {
            Fail-Json -obj $result -message "User without password is informed for service ""$service"""
        }
        else {
            $fullUser = $user
            if (-Not($user.contains("@")) -And ($user.Split("\").count -eq 1)) {
                $fullUser = ".\" + $user
            }

            if ($nssm_result.stdout.split("`n`r")[0] -ne $fullUser) {
                $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "ObjectName", $fullUser, $password)

                if ($nssm_result.rc -ne 0) {
                    $result.nssm_error_cmd = $nssm_result.arguments
                    $result.nssm_error_log = $nssm_result.stderr
                    Fail-Json -obj $result -message "Error updating credentials for service ""$service"""
                }

                $result.changed_by = "update_credentials"
                $result.changed = $true
            }
        }
    }
}

function Update-NssmServiceDependencies {
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

    $nssm_result = Invoke-NssmCommand -arguments @("get", $service, "DependOnService")

    if ($nssm_result.rc -ne 0) {
        $result.nssm_error_cmd = $nssm_result.arguments
        $result.nssm_error_log = $nssm_result.stderr
        Fail-Json -obj $result -message "Error updating dependencies for service ""$service"""
    }

    $current_dependencies = @($nssm_result.stdout.split("`n`r") | where { $_ -ne '' })

    if (@(Compare-Object -ReferenceObject $current_dependencies -DifferenceObject $dependencies).Length -ne 0) {
        $nssm_result = Invoke-NssmCommand -arguments (@("set", $service, "DependOnService") + $dependencies)

        if ($nssm_result.rc -ne 0) {
            $result.nssm_error_cmd = $nssm_result.arguments
            $result.nssm_error_log = $nssm_result.stderr
            Fail-Json -obj $result -message "Error updating dependencies for service ""$service"""
        }

        $result.changed_by = "update-dependencies"
        $result.changed = $true
    }
}

function Update-NssmServiceStartMode {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$service,
        [Parameter(Mandatory=$true)]
        [string]$mode
    )

    $nssm_result = Invoke-NssmCommand -arguments @("get", $service, "Start")

    if ($nssm_result.rc -ne 0) {
        $result.nssm_error_cmd = $nssm_result.arguments
        $result.nssm_error_log = $nssm_result.stderr
        Fail-Json -obj $result -message "Error updating start mode for service ""$service"""
    }

    $mappedMode = $start_modes_map.$mode
    if ($nssm_result.stdout -notlike "*$mappedMode*") {
        $nssm_result = Invoke-NssmCommand -arguments @("set", $service, "Start", $mappedMode)

        if ($nssm_result.rc -ne 0) {
            $result.nssm_error_cmd = $nssm_result.arguments
            $result.nssm_error_log = $nssm_result.stderr
            Fail-Json -obj $result -message "Error updating start mode for service ""$service"""
        }

        $result.changed_by = "start_mode"
        $result.changed = $true
    }
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

if ($state -eq 'absent') {
    Uninstall-NssmService -service $name
} else {
    Install-NssmService -service $name -application $application
    Update-NssmServiceAppParameters -service $name -appParameters $appParameters -appParametersFree $appParametersFree
    Update-NssmServiceOutputFiles -service $name -stdout $stdoutFile -stderr $stderrFile
    Update-NssmServiceDependencies -service $name -dependencies $dependencies
    Update-NssmServiceCredentials -service $name -user $user -password $password
    Update-NssmServiceStartMode -service $name -mode $startMode

    if ($state -in "stopped","restarted") {
        Stop-NssmService -service $name
    }

    if($state -in "started","restarted") {
        Start-NssmService -service $name
    }
}

Exit-Json $result
