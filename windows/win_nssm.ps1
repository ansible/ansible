#!powershell
# This file is part of Ansible
#
# Copyright 2015, George Frank <george@georgefrank.net>
# Copyright 2015, Adam Keech <akeech@chathamfinancial.com>
# Copyright 2015, Hans-Joachim Kliemeck <git@kliemeck.de>
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

$ErrorActionPreference = "Stop"

# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;

$result = New-Object PSObject;
Set-Attr $result "changed" $false;

$name = Get-Attr $params "name" -failifempty $true
$state = Get-Attr $params "state" -default "present" -validateSet "present", "absent", "started", "stopped", "restarted" -resultobj $result

$application = Get-Attr $params "application" -default $null
$appParameters = Get-Attr $params "app_parameters" -default $null
$startMode = Get-Attr $params "start_mode" -default "auto" -validateSet "auto", "manual", "disabled" -resultobj $result

$stdoutFile = Get-Attr $params "stdout_file" -default $null
$stderrFile = Get-Attr $params "stderr_file" -default $null
$dependencies = Get-Attr $params "dependencies" -default $null

$user = Get-Attr $params "user" -default $null
$password = Get-Attr $params "password" -default $null

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
        $cmd = "nssm stop ""$name"""
        $results = invoke-expression $cmd

        $cmd = "nssm remove ""$name"" confirm"
        $results = invoke-expression $cmd

        if ($LastExitCode -ne 0)
        {
            Set-Attr $result "nssm_error_cmd" $cmd
            Set-Attr $result "nssm_error_log" "$results"
            Throw "Error removing service ""$name"""
        }

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

    if (!(Service-Exists -name $name))
    {
        $cmd = "nssm install ""$name"" $application"

        $results = invoke-expression $cmd

        if ($LastExitCode -ne 0)
        {
            Set-Attr $result "nssm_error_cmd" $cmd
            Set-Attr $result "nssm_error_log" "$results"
            Throw "Error installing service ""$name"""
        }

        $result.changed = $true
        
     } else {
        $cmd = "nssm get ""$name"" Application"
        $results = invoke-expression $cmd

        if ($LastExitCode -ne 0)
        {
            Set-Attr $result "nssm_error_cmd" $cmd
            Set-Attr $result "nssm_error_log" "$results"
            Throw "Error installing service ""$name"""
        }

        if ($results -ne $application)
        {
            $cmd = "nssm set ""$name"" Application $application"

            $results = invoke-expression $cmd

            if ($LastExitCode -ne 0)
            {
                Set-Attr $result "nssm_error_cmd" $cmd
                Set-Attr $result "nssm_error_log" "$results"
                Throw "Error installing service ""$name"""
            }

            $result.changed = $true
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
        [Parameter(Mandatory=$true)]
        [AllowEmptyString()]
        [string]$appParameters
    )

    $cmd = "nssm get ""$name"" AppParameters"
    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "nssm_error_cmd" $cmd
        Set-Attr $result "nssm_error_log" "$results"
        Throw "Error updating AppParameters for service ""$name"""
    }

    $appParamKeys = @()
    $appParamVals = @()
    $singleLineParams = ""
    
    if ($appParameters)
    {
        $appParametersHash = ParseAppParameters -appParameters $appParameters
        $appParametersHash.GetEnumerator() |
            % {
                $key = $($_.Name)
                $val = $($_.Value)

                $appParamKeys += $key
                $appParamVals += $val

                if ($key -eq "_") {
                    $singleLineParams = "$val " + $singleLineParams
                } else {
                    $singleLineParams = $singleLineParams + "$key ""$val"""
                }
            }

        Set-Attr $result "nssm_app_parameters_parsed" $appParametersHash
        Set-Attr $result "nssm_app_parameters_keys" $appParamKeys
        Set-Attr $result "nssm_app_parameters_vals" $appParamVals
    }

    Set-Attr $result "nssm_app_parameters" $appParameters
    Set-Attr $result "nssm_single_line_app_parameters" $singleLineParams

    if ($results -ne $singleLineParams)
    {
        if ($appParameters)
        {
            $cmd = "nssm set ""$name"" AppParameters $singleLineParams"
        } else {
            $cmd = "nssm set ""$name"" AppParameters '""""'"
        }
        $results = invoke-expression $cmd

        if ($LastExitCode -ne 0)
        {
            Set-Attr $result "nssm_error_cmd" $cmd
            Set-Attr $result "nssm_error_log" "$results"
            Throw "Error updating AppParameters for service ""$name"""
        }

        $result.changed = $true
    }
}

Function Nssm-Set-Ouput-Files
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name,
        [string]$stdout,
        [string]$stderr
    )

    $cmd = "nssm get ""$name"" AppStdout"
    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "nssm_error_cmd" $cmd
        Set-Attr $result "nssm_error_log" "$results"
        Throw "Error retrieving existing stdout file for service ""$name"""
    }

    if ($results -ne $stdout)
    {
        if (!$stdout)
        {
            $cmd = "nssm reset ""$name"" AppStdout"
        } else {
            $cmd = "nssm set ""$name"" AppStdout $stdout"        
        }
    
        $results = invoke-expression $cmd

        if ($LastExitCode -ne 0)
        {
            Set-Attr $result "nssm_error_cmd" $cmd
            Set-Attr $result "nssm_error_log" "$results"
            Throw "Error setting stdout file for service ""$name"""
        }

        $result.changed = $true
    }

    $cmd = "nssm get ""$name"" AppStderr"
    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "nssm_error_cmd" $cmd
        Set-Attr $result "nssm_error_log" "$results"
        Throw "Error retrieving existing stderr file for service ""$name"""
    }

    if ($results -ne $stderr)
    {
        if (!$stderr)
        {
            $cmd = "nssm reset ""$name"" AppStderr"
            $results = invoke-expression $cmd

            if ($LastExitCode -ne 0)
            {
                Set-Attr $result "nssm_error_cmd" $cmd
                Set-Attr $result "nssm_error_log" "$results"
                Throw "Error clearing stderr file setting for service ""$name"""
            }
        } else {
            $cmd = "nssm set ""$name"" AppStderr $stderr"
            $results = invoke-expression $cmd

            if ($LastExitCode -ne 0)
            {
                Set-Attr $result "nssm_error_cmd" $cmd
                Set-Attr $result "nssm_error_log" "$results"
                Throw "Error setting stderr file for service ""$name"""
            }
        }

        $result.changed = $true
    }

    ###
    # Setup file rotation so we don't accidentally consume too much disk
    ###

    #set files to overwrite
    $cmd = "nssm set ""$name"" AppStdoutCreationDisposition 2"
    $results = invoke-expression $cmd

    $cmd = "nssm set ""$name"" AppStderrCreationDisposition 2"
    $results = invoke-expression $cmd

    #enable file rotation
    $cmd = "nssm set ""$name"" AppRotateFiles 1"
    $results = invoke-expression $cmd

    #don't rotate until the service restarts
    $cmd = "nssm set ""$name"" AppRotateOnline 0"
    $results = invoke-expression $cmd

    #both of the below conditions must be met before rotation will happen
    #minimum age before rotating
    $cmd = "nssm set ""$name"" AppRotateSeconds 86400"
    $results = invoke-expression $cmd

    #minimum size before rotating
    $cmd = "nssm set ""$name"" AppRotateBytes 104858"
    $results = invoke-expression $cmd
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

    $cmd = "nssm get ""$name"" ObjectName"
    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "nssm_error_cmd" $cmd
        Set-Attr $result "nssm_error_log" "$results"
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

            If ($results -ne $fullUser) {
                $cmd = "nssm set ""$name"" ObjectName $fullUser $password"
                $results = invoke-expression $cmd

                if ($LastExitCode -ne 0)
                {
                    Set-Attr $result "nssm_error_cmd" $cmd
                    Set-Attr $result "nssm_error_log" "$results"
                    Throw "Error updating credentials for service ""$name"""
                }

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
        [string]$dependencies
    )

    $cmd = "nssm get ""$name"" DependOnService"
    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "nssm_error_cmd" $cmd
        Set-Attr $result "nssm_error_log" "$results"
        Throw "Error updating dependencies for service ""$name"""
    }

    If (($dependencies) -and ($results.Tolower() -ne $dependencies.Tolower())) {
        $cmd = "nssm set ""$name"" DependOnService $dependencies"
        $results = invoke-expression $cmd

        if ($LastExitCode -ne 0)
        {
            Set-Attr $result "nssm_error_cmd" $cmd
            Set-Attr $result "nssm_error_log" "$results"
            Throw "Error updating dependencies for service ""$name"""
        }

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

    $cmd = "nssm get ""$name"" Start"
    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "nssm_error_cmd" $cmd
        Set-Attr $result "nssm_error_log" "$results"
        Throw "Error updating start mode for service ""$name"""
    }

    $modes=@{"auto" = "SERVICE_AUTO_START"; "manual" = "SERVICE_DEMAND_START"; "disabled" = "SERVICE_DISABLED"}
    $mappedMode = $modes.$mode
    if ($mappedMode -ne $results) {
        $cmd = "nssm set ""$name"" Start $mappedMode"
        $results = invoke-expression $cmd

        if ($LastExitCode -ne 0)
        {
            Set-Attr $result "nssm_error_cmd" $cmd
            Set-Attr $result "nssm_error_log" "$results"
            Throw "Error updating start mode for service ""$name"""
        }

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

    $cmd = "nssm status ""$name"""
    $results = invoke-expression $cmd

    return ,$results
}

Function Nssm-Start
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name
    )

    $currentStatus = Nssm-Get-Status -name $name

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "nssm_error_cmd" $cmd
        Set-Attr $result "nssm_error_log" "$results"
        Throw "Error starting service ""$name"""
    }

    switch ($currentStatus)
    {
        "SERVICE_RUNNING" { <# Nothing to do #> }
        "SERVICE_STOPPED" { Nssm-Start-Service-Command -name $name }
        
        "SERVICE_CONTINUE_PENDING" { Nssm-Stop-Service-Command -name $name; Nssm-Start-Service-Command -name $name }
        "SERVICE_PAUSE_PENDING" { Nssm-Stop-Service-Command -name $name; Nssm-Start-Service-Command -name $name }
        "SERVICE_PAUSED" { Nssm-Stop-Service-Command -name $name; Nssm-Start-Service-Command -name $name }
        "SERVICE_START_PENDING" { Nssm-Stop-Service-Command -name $name; Nssm-Start-Service-Command -name $name }
        "SERVICE_STOP_PENDING" { Nssm-Stop-Service-Command -name $name; Nssm-Start-Service-Command -name $name }
    }
}

Function Nssm-Start-Service-Command
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name
    )

    $cmd = "nssm start ""$name"""

    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "nssm_error_cmd" $cmd
        Set-Attr $result "nssm_error_log" "$results"
        Throw "Error starting service ""$name"""
    }

    $result.changed = $true
}

Function Nssm-Stop-Service-Command
{
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$name
    )

    $cmd = "nssm stop ""$name"""

    $results = invoke-expression $cmd

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "nssm_error_cmd" $cmd
        Set-Attr $result "nssm_error_log" "$results"
        Throw "Error stopping service ""$name"""
    }

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

    if ($LastExitCode -ne 0)
    {
        Set-Attr $result "nssm_error_cmd" $cmd
        Set-Attr $result "nssm_error_log" "$results"
        Throw "Error stopping service ""$name"""
    }

    if ($currentStatus -ne "SERVICE_STOPPED")
    {
        $cmd = "nssm stop ""$name"""

        $results = invoke-expression $cmd

        if ($LastExitCode -ne 0)
        {
            Set-Attr $result "nssm_error_cmd" $cmd
            Set-Attr $result "nssm_error_log" "$results"
            Throw "Error stopping service ""$name"""
        }

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
    Nssm-Update-AppParameters -name $name -appParameters $appParameters
    Nssm-Set-Ouput-Files -name $name -stdout $stdoutFile -stderr $stderrFile
    Nssm-Update-Dependencies -name $name -dependencies $dependencies
    Nssm-Update-Credentials -name $name -user $user -password $password
    Nssm-Update-StartMode -name $name -mode $startMode
}

Try
{
    switch ($state)
    {
        "absent" { Nssm-Remove -name $name }
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

    Exit-Json $result;
}
Catch
{
     Fail-Json $result $_.Exception.Message
}
