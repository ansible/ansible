#!powershell

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil Ansible.Service
#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil

$module = [Ansible.Basic.AnsibleModule]::Create($args, @{})

$path = "$env:SystemRoot\System32\svchost.exe"

Function Assert-Equals {
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)][AllowNull()]$Actual,
        [Parameter(Mandatory=$true, Position=0)][AllowNull()]$Expected
    )

    $matched = $false
    if ($Actual -is [System.Collections.ArrayList] -or $Actual -is [Array] -or $Actual -is [System.Collections.IList]) {
        $Actual.Count | Assert-Equals -Expected $Expected.Count
        for ($i = 0; $i -lt $Actual.Count; $i++) {
            $actualValue = $Actual[$i]
            $expectedValue = $Expected[$i]
            Assert-Equals -Actual $actualValue -Expected $expectedValue
        }
        $matched = $true
    } else {
        $matched = $Actual -ceq $Expected
    }

    if (-not $matched) {
        if ($Actual -is [PSObject]) {
            $Actual = $Actual.ToString()
        }

        $call_stack = (Get-PSCallStack)[1]
        $module.Result.test = $test
        $module.Result.actual = $Actual
        $module.Result.expected = $Expected
        $module.Result.line = $call_stack.ScriptLineNumber
        $module.Result.method = $call_stack.Position.Text

        $module.FailJson("AssertionError: actual != expected")
    }
}

Function Invoke-Sc {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [String]
        $Action,

        [Parameter(Mandatory=$true)]
        [String]
        $Name,

        [Object]
        $Arguments
    )

    $commandArgs = [System.Collections.Generic.List[String]]@("sc.exe", $Action, $Name)
    if ($null -ne $Arguments) {
        if ($Arguments -is [System.Collections.IDictionary]) {
            foreach ($arg in $Arguments.GetEnumerator()) {
                $commandArgs.Add("$($arg.Key)=")
                $commandArgs.Add($arg.Value)
            }
        } else {
            foreach ($arg in $Arguments) {
                $commandArgs.Add($arg)
            }
        }
    }

    $command = Argv-ToString -arguments $commandArgs

    $res = Run-Command -command $command
    if ($res.rc -ne 0) {
        $module.Result.rc = $res.rc
        $module.Result.stdout = $res.stdout
        $module.Result.stderr = $res.stderr
        $module.FailJson("Failed to invoke sc with: $command")
    }

    $info = @{ Name = $Name }

    if ($Action -eq 'qtriggerinfo') {
        # qtriggerinfo is in a different format which requires some manual parsing from the norm.
        $info.Triggers = [System.Collections.Generic.List[PSObject]]@()
    }

    $currentKey = $null
    $qtriggerSection = @{}
    $res.stdout -split "`r`n" | Foreach-Object -Process {
        $line = $_.Trim()

        if ($Action -eq 'qtriggerinfo' -and $line -in @('START SERVICE', 'STOP SERVICE')) {
            if ($qtriggerSection.Count -gt 0) {
                $info.Triggers.Add([PSCustomObject]$qtriggerSection)
                $qtriggerSection = @{}
            }

            $qtriggerSection = @{
                Action = $line
            }
        }

        if (-not $line -or (-not $line.Contains(':') -and $null -eq $currentKey)) {
            return
        }

        $lineSplit = $line.Split(':', 2)
        if ($lineSplit.Length -eq 2) {
            $k = $lineSplit[0].Trim()
            if (-not $k) {
                $k = $currentKey
            }

            $v = $lineSplit[1].Trim()
        } else {
            $k = $currentKey
            $v = $line
        }

        if ($qtriggerSection.Count -gt 0) {
            if ($k -eq 'DATA') {
                $qtriggerSection.Data.Add($v)
            } else {
                $qtriggerSection.Type = $k
                $qtriggerSection.SubType = $v
                $qtriggerSection.Data = [System.Collections.Generic.List[String]]@()
            }
        } else {
            if ($info.ContainsKey($k)) {
                if ($info[$k] -isnot [System.Collections.Generic.List[String]]) {
                    $info[$k] = [System.Collections.Generic.List[String]]@($info[$k])
                }
                $info[$k].Add($v)
            } else {
                $currentKey = $k
                $info[$k] = $v
            }
        }
    }

    if ($qtriggerSection.Count -gt 0) {
        $info.Triggers.Add([PSCustomObject]$qtriggerSection)
    }

    [PSCustomObject]$info
}

$tests = [Ordered]@{
    "Props on service created by New-Service" = {
        $actual = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName

        $actual.ServiceName | Assert-Equals -Expected $serviceName
        $actual.ServiceType | Assert-Equals -Expected ([Ansible.Service.ServiceType]::Win32OwnProcess)
        $actual.StartType | Assert-Equals -Expected ([Ansible.Service.ServiceStartType]::DemandStart)
        $actual.ErrorControl | Assert-Equals -Expected ([Ansible.Service.ErrorControl]::Normal)
        $actual.Path | Assert-Equals -Expected ('"{0}"' -f $path)
        $actual.LoadOrderGroup | Assert-Equals -Expected ""
        $actual.DependentOn.Count | Assert-Equals -Expected 0
        $actual.Account | Assert-Equals -Expected (
            [System.Security.Principal.SecurityIdentifier]'S-1-5-18').Translate([System.Security.Principal.NTAccount]
        )
        $actual.DisplayName | Assert-Equals -Expected $serviceName
        $actual.Description | Assert-Equals -Expected $null
        $actual.FailureActions.ResetPeriod | Assert-Equals -Expected 0
        $actual.FailureActions.RebootMsg | Assert-Equals -Expected $null
        $actual.FailureActions.Command | Assert-Equals -Expected $null
        $actual.FailureActions.Actions.Count | Assert-Equals -Expected 0
        $actual.FailureActionsOnNonCrashFailures | Assert-Equals -Expected $false
        $actual.ServiceSidInfo | Assert-Equals -Expected ([Ansible.Service.ServiceSidInfo]::None)
        $actual.RequiredPrivileges.Count | Assert-Equals -Expected 0
        # Cannot test default values as it differs per OS version
        $null -ne $actual.PreShutdownTimeout | Assert-Equals -Expected $true
        $actual.Triggers.Count | Assert-Equals -Expected 0
        $actual.PreferredNode | Assert-Equals -Expected $null
        if ([Environment]::OSVersion.Version -ge [Version]'6.3') {
            $actual.LaunchProtection | Assert-Equals -Expected ([Ansible.Service.LaunchProtection]::None)
        } else {
            $actual.LaunchProtection | Assert-Equals -Expected $null
        }
        $actual.State | Assert-Equals -Expected ([Ansible.Service.ServiceStatus]::Stopped)
        $actual.Win32ExitCode | Assert-Equals -Expected 1077  # ERROR_SERVICE_NEVER_STARTED
        $actual.ServiceExitCode | Assert-Equals -Expected 0
        $actual.Checkpoint | Assert-Equals -Expected 0
        $actual.WaitHint | Assert-Equals -Expected 0
        $actual.ProcessId | Assert-Equals -Expected 0
        $actual.ServiceFlags | Assert-Equals -Expected ([Ansible.Service.ServiceFlags]::None)
        $actual.DependedBy.Count | Assert-Equals 0
    }

    "Service creation through util" = {
        $testName = "$($serviceName)_2"
        $actual = [Ansible.Service.Service]::Create($testName, '"{0}"' -f $path)

        try {
            $cmdletService = Get-Service -Name $testName -ErrorAction SilentlyContinue
            $null -ne $cmdletService | Assert-Equals -Expected $true

            $actual.ServiceName | Assert-Equals -Expected $testName
            $actual.ServiceType | Assert-Equals -Expected ([Ansible.Service.ServiceType]::Win32OwnProcess)
            $actual.StartType | Assert-Equals -Expected ([Ansible.Service.ServiceStartType]::DemandStart)
            $actual.ErrorControl | Assert-Equals -Expected ([Ansible.Service.ErrorControl]::Normal)
            $actual.Path | Assert-Equals -Expected ('"{0}"' -f $path)
            $actual.LoadOrderGroup | Assert-Equals -Expected ""
            $actual.DependentOn.Count | Assert-Equals -Expected 0
            $actual.Account | Assert-Equals -Expected (
                [System.Security.Principal.SecurityIdentifier]'S-1-5-18').Translate([System.Security.Principal.NTAccount]
            )
            $actual.DisplayName | Assert-Equals -Expected $testName
            $actual.Description | Assert-Equals -Expected $null
            $actual.FailureActions.ResetPeriod | Assert-Equals -Expected 0
            $actual.FailureActions.RebootMsg | Assert-Equals -Expected $null
            $actual.FailureActions.Command | Assert-Equals -Expected $null
            $actual.FailureActions.Actions.Count | Assert-Equals -Expected 0
            $actual.FailureActionsOnNonCrashFailures | Assert-Equals -Expected $false
            $actual.ServiceSidInfo | Assert-Equals -Expected ([Ansible.Service.ServiceSidInfo]::None)
            $actual.RequiredPrivileges.Count | Assert-Equals -Expected 0
            $null -ne $actual.PreShutdownTimeout | Assert-Equals -Expected $true
            $actual.Triggers.Count | Assert-Equals -Expected 0
            $actual.PreferredNode | Assert-Equals -Expected $null
            if ([Environment]::OSVersion.Version -ge [Version]'6.3') {
                $actual.LaunchProtection | Assert-Equals -Expected ([Ansible.Service.LaunchProtection]::None)
            } else {
                $actual.LaunchProtection | Assert-Equals -Expected $null
            }
            $actual.State | Assert-Equals -Expected ([Ansible.Service.ServiceStatus]::Stopped)
            $actual.Win32ExitCode | Assert-Equals -Expected 1077  # ERROR_SERVICE_NEVER_STARTED
            $actual.ServiceExitCode | Assert-Equals -Expected 0
            $actual.Checkpoint | Assert-Equals -Expected 0
            $actual.WaitHint | Assert-Equals -Expected 0
            $actual.ProcessId | Assert-Equals -Expected 0
            $actual.ServiceFlags | Assert-Equals -Expected ([Ansible.Service.ServiceFlags]::None)
            $actual.DependedBy.Count | Assert-Equals 0
        } finally {
            $actual.Delete()
        }
    }

    "Fail to open non-existing service" = {
        $failed = $false
        try {
            $null = New-Object -TypeName Ansible.Service.Service -ArgumentList 'fake_service'
        } catch [Ansible.Service.ServiceManagerException] {
            # 1060 == ERROR_SERVICE_DOES_NOT_EXIST
            $_.Exception.Message -like '*Win32ErrorCode 1060 - 0x00000424*' | Assert-Equals -Expected $true
            $failed = $true
        }

        $failed | Assert-Equals -Expected $true
    }

    "Open with specific access rights" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList @(
            $serviceName, [Ansible.Service.ServiceRights]'QueryConfig, QueryStatus'
        )

        # QueryStatus can get the status
        $service.State | Assert-Equals -Expected ([Ansible.Service.ServiceStatus]::Stopped)

        # Should fail to get the config because we did not request that right
        $failed = $false
        try {
            $service.Path = 'fail'
        } catch [Ansible.Service.ServiceManagerException] {
            # 5 == ERROR_ACCESS_DENIED
            $_.Exception.Message -like '*Win32ErrorCode 5 - 0x00000005*' | Assert-Equals -Expected $true
            $failed = $true
        }

        $failed | Assert-Equals -Expected $true

    }

    "Modfiy ServiceType" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.ServiceType = [Ansible.Service.ServiceType]::Win32ShareProcess

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.ServiceType | Assert-Equals -Expected ([Ansible.Service.ServiceType]::Win32ShareProcess)
        $actual.TYPE | Assert-Equals -Expected "20  WIN32_SHARE_PROCESS"

        $null = Invoke-Sc -Action config -Name $serviceName -Arguments @{type="own"}
        $service.Refresh()
        $service.ServiceType | Assert-Equals -Expected ([Ansible.Service.ServiceType]::Win32OwnProcess)
    }

    "Create desktop interactive service" = {
        $service = New-Object -Typename Ansible.Service.Service -ArgumentList $serviceName
        $service.ServiceType = [Ansible.Service.ServiceType]'Win32OwnProcess, InteractiveProcess'

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $actual.TYPE | Assert-Equals -Expected "110  WIN32_OWN_PROCESS (interactive)"
        $service.ServiceType | Assert-Equals -Expected ([Ansible.Service.ServiceType]'Win32OwnProcess, InteractiveProcess')

        # Change back from interactive process
        $service.ServiceType = [Ansible.Service.ServiceType]::Win32OwnProcess

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $actual.TYPE | Assert-Equals -Expected "10  WIN32_OWN_PROCESS"
        $service.ServiceType | Assert-Equals -Expected ([Ansible.Service.ServiceType]::Win32OwnProcess)

        $service.Account = [System.Security.Principal.SecurityIdentifier]'S-1-5-20'

        $failed = $false
        try {
            $service.ServiceType = [Ansible.Service.ServiceType]'Win32OwnProcess, InteractiveProcess'
        } catch [Ansible.Service.ServiceManagerException] {
            $failed = $true
            $_.Exception.NativeErrorCode | Assert-Equals -Expected 87  # ERROR_INVALID_PARAMETER
        }
        $failed | Assert-Equals -Expected $true

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $actual.TYPE | Assert-Equals -Expected "10  WIN32_OWN_PROCESS"
    }

    "Modify StartType" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.StartType = [Ansible.Service.ServiceStartType]::Disabled

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.StartType | Assert-Equals -Expected ([Ansible.Service.ServiceStartType]::Disabled)
        $actual.START_TYPE | Assert-Equals -Expected "4   DISABLED"

        $null = Invoke-Sc -Action config -Name $serviceName -Arguments @{start="demand"}
        $service.Refresh()
        $service.StartType | Assert-Equals -Expected ([Ansible.Service.ServiceStartType]::DemandStart)
    }

    "Modify StartType auto delayed" = {
        # Delayed start type is a modifier of the AutoStart type. It uses a separate config entry to define and this
        # makes sure the util does that correctly from various types and back.
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.StartType = [Ansible.Service.ServiceStartType]::Disabled  # Start from Disabled

        # Disabled -> Auto Start Delayed
        $service.StartType = [Ansible.Service.ServiceStartType]::AutoStartDelayed

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.StartType | Assert-Equals -Expected ([Ansible.Service.ServiceStartType]::AutoStartDelayed)
        $actual.START_TYPE | Assert-Equals -Expected "2   AUTO_START  (DELAYED)"

        # Auto Start Delayed -> Auto Start
        $service.StartType = [Ansible.Service.ServiceStartType]::AutoStart

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.StartType | Assert-Equals -Expected ([Ansible.Service.ServiceStartType]::AutoStart)
        $actual.START_TYPE | Assert-Equals -Expected "2   AUTO_START"

        # Auto Start -> Auto Start Delayed
        $service.StartType = [Ansible.Service.ServiceStartType]::AutoStartDelayed

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.StartType | Assert-Equals -Expected ([Ansible.Service.ServiceStartType]::AutoStartDelayed)
        $actual.START_TYPE | Assert-Equals -Expected "2   AUTO_START  (DELAYED)"

        # Auto Start Delayed -> Manual
        $service.StartType = [Ansible.Service.ServiceStartType]::DemandStart

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.StartType | Assert-Equals -Expected ([Ansible.Service.ServiceStartType]::DemandStart)
        $actual.START_TYPE | Assert-Equals -Expected "3   DEMAND_START"
    }

    "Modify ErrorControl" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.ErrorControl = [Ansible.Service.ErrorControl]::Severe

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.ErrorControl | Assert-Equals -Expected ([Ansible.Service.ErrorControl]::Severe)
        $actual.ERROR_CONTROL | Assert-Equals -Expected "2   SEVERE"

        $null = Invoke-Sc -Action config -Name $serviceName -Arguments @{error="ignore"}
        $service.Refresh()
        $service.ErrorControl | Assert-Equals -Expected ([Ansible.Service.ErrorControl]::Ignore)
    }

    "Modify Path" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.Path = "Fake path"

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.Path | Assert-Equals -Expected "Fake path"
        $actual.BINARY_PATH_NAME | Assert-Equals -Expected "Fake path"

        $null = Invoke-Sc -Action config -Name $serviceName -Arguments @{binpath="other fake path"}
        $service.Refresh()
        $service.Path | Assert-Equals -Expected "other fake path"
    }

    "Modify LoadOrderGroup" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.LoadOrderGroup = "my group"

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.LoadOrderGroup | Assert-Equals -Expected "my group"
        $actual.LOAD_ORDER_GROUP | Assert-Equals -Expected "my group"

        $null = Invoke-Sc -Action config -Name $serviceName -Arguments @{group=""}
        $service.Refresh()
        $service.LoadOrderGroup | Assert-Equals -Expected ""
    }

    "Modify DependentOn" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.DependentOn = @("HTTP", "WinRM")

        $actual = Invoke-Sc -Action qc -Name $serviceName
        @(,$service.DependentOn) | Assert-Equals -Expected @("HTTP", "WinRM")
        @(,$actual.DEPENDENCIES) | Assert-Equals -Expected @("HTTP", "WinRM")

        $null = Invoke-Sc -Action config -Name $serviceName -Arguments @{depend=""}
        $service.Refresh()
        $service.DependentOn.Count | Assert-Equals -Expected 0
    }

    "Modify Account - service account" = {
        $systemSid = [System.Security.Principal.SecurityIdentifier]'S-1-5-18'
        $systemName =$systemSid.Translate([System.Security.Principal.NTAccount])
        $localSid = [System.Security.Principal.SecurityIdentifier]'S-1-5-19'
        $localName = $localSid.Translate([System.Security.Principal.NTAccount])
        $networkSid = [System.Security.Principal.SecurityIdentifier]'S-1-5-20'
        $networkName = $networkSid.Translate([System.Security.Principal.NTAccount])

        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.Account = $networkSid

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.Account | Assert-Equals -Expected $networkName
        $actual.SERVICE_START_NAME | Assert-Equals -Expected $networkName.Value

        $null = Invoke-Sc -Action config -Name $serviceName -Arguments @{obj=$localName.Value}
        $service.Refresh()
        $service.Account | Assert-Equals -Expected $localName

        $service.Account = $systemSid
        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.Account | Assert-Equals -Expected $systemName
        $actual.SERVICE_START_NAME | Assert-Equals -Expected "LocalSystem"
    }

    "Modify Account - user" = {
        $currentSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User

        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.Account = $currentSid
        $service.Password = 'password'

        $actual = Invoke-Sc -Action qc -Name $serviceName

        # When running tests in CI this seems to become .\Administrator
        if ($service.Account.Value.StartsWith('.\')) {
            $username = $service.Account.Value.Substring(2, $service.Account.Value.Length - 2)
            $actualSid = ([System.Security.Principal.NTAccount]"$env:COMPUTERNAME\$username").Translate(
                [System.Security.Principal.SecurityIdentifier]
            )
        } else {
            $actualSid = $service.Account.Translate([System.Security.Principal.SecurityIdentifier])
        }
        $actualSid.Value | Assert-Equals -Expected $currentSid.Value
        $actual.SERVICE_START_NAME | Assert-Equals -Expected $service.Account.Value

        # Go back to SYSTEM from account
        $systemSid = [System.Security.Principal.SecurityIdentifier]'S-1-5-18'
        $service.Account = $systemSid

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.Account | Assert-Equals -Expected $systemSid.Translate([System.Security.Principal.NTAccount])
        $actual.SERVICE_START_NAME | Assert-Equals -Expected "LocalSystem"
    }

    "Modify Account - virtual account" = {
        $account = [System.Security.Principal.NTAccount]"NT SERVICE\$serviceName"

        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.Account = $account

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.Account | Assert-Equals -Expected $account
        $actual.SERVICE_START_NAME | Assert-Equals -Expected $account.Value
    }

    "Modify Account - gMSA" = {
        # This cannot be tested through CI, only done on manual tests.
        return

        $gmsaName = [System.Security.Principal.NTAccount]'gMSA$@DOMAIN.LOCAL'  # Make sure this is UPN.
        $gmsaSid = $gmsaName.Translate([System.Security.Principal.SecurityIdentifier])
        $gmsaNetlogon = $gmsaSid.Translate([System.Security.Principal.NTAccount])

        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.Account = $gmsaName

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.Account | Assert-Equals -Expected $gmsaName
        $actual.SERVICE_START_NAME | Assert-Equals -Expected $gmsaName

        # Go from gMSA to account and back to verify the Password doesn't matter.
        $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
        $service.Account = $currentUser
        $service.Password = 'fake password'
        $service.Password = 'fake password2'

        # Now test in the Netlogon format.
        $service.Account = $gmsaSid

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.Account | Assert-Equals -Expected $gmsaNetlogon
        $actual.SERVICE_START_NAME | Assert-Equals -Expected $gmsaNetlogon.Value
    }

    "Modify DisplayName" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.DisplayName = "Custom Service Name"

        $actual = Invoke-Sc -Action qc -Name $serviceName
        $service.DisplayName | Assert-Equals -Expected "Custom Service Name"
        $actual.DISPLAY_NAME | Assert-Equals -Expected "Custom Service Name"

        $null = Invoke-Sc -Action config -Name $serviceName -Arguments @{displayname="New Service Name"}
        $service.Refresh()
        $service.DisplayName | Assert-Equals -Expected "New Service Name"
    }

    "Modify Description" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.Description = "My custom service description"

        $actual = Invoke-Sc -Action qdescription -Name $serviceName
        $service.Description | Assert-Equals -Expected "My custom service description"
        $actual.DESCRIPTION | Assert-Equals -Expected "My custom service description"

        $null = Invoke-Sc -Action description -Name $serviceName -Arguments @(,"new description")
        $service.Description | Assert-Equals -Expected "new description"

        $service.Description = $null

        $actual = Invoke-Sc -Action qdescription -Name $serviceName
        $service.Description | Assert-Equals -Expected $null
        $actual.DESCRIPTION | Assert-Equals -Expected ""
    }

    "Modify FailureActions" = {
        $newAction = [Ansible.Service.FailureActions]@{
            ResetPeriod = 86400
            RebootMsg = 'Reboot msg'
            Command = 'Command line'
            Actions = @(
                [Ansible.Service.Action]@{Type = [Ansible.Service.FailureAction]::RunCommand; Delay = 1000},
                [Ansible.Service.Action]@{Type = [Ansible.Service.FailureAction]::RunCommand; Delay = 2000},
                [Ansible.Service.Action]@{Type = [Ansible.Service.FailureAction]::Restart; Delay = 1000},
                [Ansible.Service.Action]@{Type = [Ansible.Service.FailureAction]::Reboot; Delay = 1000}
            )
        }
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.FailureActions = $newAction

        $actual = Invoke-Sc -Action qfailure -Name $serviceName
        $actual.'RESET_PERIOD (in seconds)' | Assert-Equals -Expected 86400
        $actual.REBOOT_MESSAGE | Assert-Equals -Expected 'Reboot msg'
        $actual.COMMAND_LINE | Assert-Equals -Expected 'Command line'
        $actual.FAILURE_ACTIONS.Count | Assert-Equals -Expected 4
        $actual.FAILURE_ACTIONS[0] | Assert-Equals -Expected "RUN PROCESS -- Delay = 1000 milliseconds."
        $actual.FAILURE_ACTIONS[1] | Assert-Equals -Expected "RUN PROCESS -- Delay = 2000 milliseconds."
        $actual.FAILURE_ACTIONS[2] | Assert-Equals -Expected "RESTART -- Delay = 1000 milliseconds."
        $actual.FAILURE_ACTIONS[3] | Assert-Equals -Expected "REBOOT -- Delay = 1000 milliseconds."
        $service.FailureActions.Actions.Count | Assert-Equals -Expected 4

        # Test that we can change individual settings and it doesn't change all
        $service.FailureActions = [Ansible.Service.FailureActions]@{ResetPeriod = 172800}

        $actual = Invoke-Sc -Action qfailure -Name $serviceName
        $actual.'RESET_PERIOD (in seconds)' | Assert-Equals -Expected 172800
        $actual.REBOOT_MESSAGE | Assert-Equals -Expected 'Reboot msg'
        $actual.COMMAND_LINE | Assert-Equals -Expected 'Command line'
        $actual.FAILURE_ACTIONS.Count | Assert-Equals -Expected 4
        $service.FailureActions.Actions.Count | Assert-Equals -Expected 4

        $service.FailureActions = [Ansible.Service.FailureActions]@{RebootMsg = "New reboot msg"}

        $actual = Invoke-Sc -Action qfailure -Name $serviceName
        $actual.'RESET_PERIOD (in seconds)' | Assert-Equals -Expected 172800
        $actual.REBOOT_MESSAGE | Assert-Equals -Expected 'New reboot msg'
        $actual.COMMAND_LINE | Assert-Equals -Expected 'Command line'
        $actual.FAILURE_ACTIONS.Count | Assert-Equals -Expected 4
        $service.FailureActions.Actions.Count | Assert-Equals -Expected 4

        $service.FailureActions = [Ansible.Service.FailureActions]@{Command = "New command line"}

        $actual = Invoke-Sc -Action qfailure -Name $serviceName
        $actual.'RESET_PERIOD (in seconds)' | Assert-Equals -Expected 172800
        $actual.REBOOT_MESSAGE | Assert-Equals -Expected 'New reboot msg'
        $actual.COMMAND_LINE | Assert-Equals -Expected 'New command line'
        $actual.FAILURE_ACTIONS.Count | Assert-Equals -Expected 4
        $service.FailureActions.Actions.Count | Assert-Equals -Expected 4

        # Test setting both ResetPeriod and Actions together
        $service.FailureActions = [Ansible.Service.FailureActions]@{
            ResetPeriod = 86400
            Actions = @(
                [Ansible.Service.Action]@{Type = [Ansible.Service.FailureAction]::RunCommand; Delay = 5000},
                [Ansible.Service.Action]@{Type = [Ansible.Service.FailureAction]::None; Delay = 0}
            )
        }

        $actual = Invoke-Sc -Action qfailure -Name $serviceName
        $actual.'RESET_PERIOD (in seconds)' | Assert-Equals -Expected 86400
        $actual.REBOOT_MESSAGE | Assert-Equals -Expected 'New reboot msg'
        $actual.COMMAND_LINE | Assert-Equals -Expected 'New command line'
        # sc.exe does not show the None action it just ends the list, so we verify from get_FailureActions
        $actual.FAILURE_ACTIONS | Assert-Equals -Expected "RUN PROCESS -- Delay = 5000 milliseconds."
        $service.FailureActions.Actions.Count | Assert-Equals -Expected 2
        $service.FailureActions.Actions[1].Type | Assert-Equals -Expected ([Ansible.Service.FailureAction]::None)

        # Test setting just Actions without ResetPeriod
        $service.FailureActions = [Ansible.Service.FailureActions]@{
            Actions = [Ansible.Service.Action]@{Type = [Ansible.Service.FailureAction]::RunCommand; Delay = 10000}
        }
        $actual = Invoke-Sc -Action qfailure -Name $serviceName
        $actual.'RESET_PERIOD (in seconds)' | Assert-Equals -Expected 86400
        $actual.REBOOT_MESSAGE | Assert-Equals -Expected 'New reboot msg'
        $actual.COMMAND_LINE | Assert-Equals -Expected 'New command line'
        $actual.FAILURE_ACTIONS | Assert-Equals -Expected "RUN PROCESS -- Delay = 10000 milliseconds."
        $service.FailureActions.Actions.Count | Assert-Equals -Expected 1

        # Test removing all actions
        $service.FailureActions = [Ansible.Service.FailureActions]@{
            Actions = @()
        }
        $actual = Invoke-Sc -Action qfailure -Name $serviceName
        $actual.'RESET_PERIOD (in seconds)' | Assert-Equals -Expected 0  # ChangeServiceConfig2W resets this back to 0.
        $actual.REBOOT_MESSAGE | Assert-Equals -Expected 'New reboot msg'
        $actual.COMMAND_LINE | Assert-Equals -Expected 'New command line'
        $actual.PSObject.Properties.Name.Contains('FAILURE_ACTIONS') | Assert-Equals -Expected $false
        $service.FailureActions.Actions.Count | Assert-Equals -Expected 0

        # Test that we are reading the right values
        $null = Invoke-Sc -Action failure -Name $serviceName -Arguments @{
            reset = 172800
            reboot = "sc reboot msg"
            command = "sc command line"
            actions = "run/5000/reboot/800"
        }

        $actual = $service.FailureActions
        $actual.ResetPeriod | Assert-Equals -Expected 172800
        $actual.RebootMsg | Assert-Equals -Expected "sc reboot msg"
        $actual.Command | Assert-Equals -Expected "sc command line"
        $actual.Actions.Count | Assert-Equals -Expected 2
        $actual.Actions[0].Type | Assert-Equals -Expected ([Ansible.Service.FailureAction]::RunCommand)
        $actual.Actions[0].Delay | Assert-Equals -Expected 5000
        $actual.Actions[1].Type | Assert-Equals -Expected ([Ansible.Service.FailureAction]::Reboot)
        $actual.Actions[1].Delay | Assert-Equals -Expected 800
    }

    "Modify FailureActionsOnNonCrashFailures" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.FailureActionsOnNonCrashFailures = $true

        $actual = Invoke-Sc -Action qfailureflag -Name $serviceName
        $service.FailureActionsOnNonCrashFailures | Assert-Equals -Expected $true
        $actual.FAILURE_ACTIONS_ON_NONCRASH_FAILURES | Assert-Equals -Expected "TRUE"

        $null = Invoke-Sc -Action failureflag -Name $serviceName -Arguments @(,0)
        $service.FailureActionsOnNonCrashFailures | Assert-Equals -Expected $false
    }

    "Modify ServiceSidInfo" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.ServiceSidInfo = [Ansible.Service.ServiceSidInfo]::None

        $actual = Invoke-Sc -Action qsidtype -Name $serviceName
        $service.ServiceSidInfo | Assert-Equals -Expected ([Ansible.Service.ServiceSidInfo]::None)
        $actual.SERVICE_SID_TYPE | Assert-Equals -Expected 'NONE'

        $null = Invoke-Sc -Action sidtype -Name $serviceName -Arguments @(,'unrestricted')
        $service.ServiceSidInfo | Assert-Equals -Expected ([Ansible.Service.ServiceSidInfo]::Unrestricted)

        $service.ServiceSidInfo = [Ansible.Service.ServiceSidInfo]::Restricted

        $actual = Invoke-Sc -Action qsidtype -Name $serviceName
        $service.ServiceSidInfo | Assert-Equals -Expected ([Ansible.Service.ServiceSidInfo]::Restricted)
        $actual.SERVICE_SID_TYPE | Assert-Equals -Expected 'RESTRICTED'
    }

    "Modify RequiredPrivileges" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.RequiredPrivileges = @("SeBackupPrivilege", "SeTcbPrivilege")

        $actual = Invoke-Sc -Action qprivs -Name $serviceName
        ,$service.RequiredPrivileges | Assert-Equals -Expected @("SeBackupPrivilege", "SeTcbPrivilege")
        ,$actual.PRIVILEGES | Assert-Equals -Expected @("SeBackupPrivilege", "SeTcbPrivilege")

        # Ensure setting to $null is the same as an empty array
        $service.RequiredPrivileges = $null

        $actual = Invoke-Sc -Action qprivs -Name $serviceName
        ,$service.RequiredPrivileges | Assert-Equals -Expected @()
        ,$actual.PRIVILEGES | Assert-Equals -Expected @()

        $service.RequiredPrivileges = @("SeBackupPrivilege", "SeTcbPrivilege")
        $service.RequiredPrivileges = @()

        $actual = Invoke-Sc -Action qprivs -Name $serviceName
        ,$service.RequiredPrivileges | Assert-Equals -Expected @()
        ,$actual.PRIVILEGES | Assert-Equals -Expected @()

        $null = Invoke-Sc -Action privs -Name $serviceName -Arguments @(,"SeCreateTokenPrivilege/SeRestorePrivilege")
        ,$service.RequiredPrivileges | Assert-Equals -Expected @("SeCreateTokenPrivilege", "SeRestorePrivilege")
    }

    "Modify PreShutdownTimeout" = {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList $serviceName
        $service.PreShutdownTimeout = 60000

        # sc.exe doesn't seem to have a query argument for this, just get it from the registry
        $actual = (
            Get-ItemProperty -LiteralPath "HKLM:\SYSTEM\CurrentControlSet\Services\$serviceName" -Name PreshutdownTimeout
        ).PreshutdownTimeout
        $actual | Assert-Equals -Expected 60000
    }

    "Modify Triggers" = {
        $service = [Ansible.Service.Service]$serviceName
        $service.Triggers = @(
            [Ansible.Service.Trigger]@{
                Type = [Ansible.Service.TriggerType]::DomainJoin
                Action = [Ansible.Service.TriggerAction]::ServiceStop
                SubType = [Guid][Ansible.Service.Trigger]::DOMAIN_JOIN_GUID
            },
            [Ansible.Service.Trigger]@{
                Type = [Ansible.Service.TriggerType]::NetworkEndpoint
                Action = [Ansible.Service.TriggerAction]::ServiceStart
                SubType = [Guid][Ansible.Service.Trigger]::NAMED_PIPE_EVENT_GUID
                DataItems = [Ansible.Service.TriggerItem]@{
                    Type = [Ansible.Service.TriggerDataType]::String
                    Data = 'my named pipe'
                }
            },
            [Ansible.Service.Trigger]@{
                Type = [Ansible.Service.TriggerType]::NetworkEndpoint
                Action = [Ansible.Service.TriggerAction]::ServiceStart
                SubType = [Guid][Ansible.Service.Trigger]::NAMED_PIPE_EVENT_GUID
                DataItems = [Ansible.Service.TriggerItem]@{
                    Type = [Ansible.Service.TriggerDataType]::String
                    Data = 'my named pipe 2'
                }
            },
            [Ansible.Service.Trigger]@{
                Type = [Ansible.Service.TriggerType]::Custom
                Action = [Ansible.Service.TriggerAction]::ServiceStart
                SubType = [Guid]'9bf04e57-05dc-4914-9ed9-84bf992db88c'
                DataItems = @(
                    [Ansible.Service.TriggerItem]@{
                        Type = [Ansible.Service.TriggerDataType]::Binary
                        Data = [byte[]]@(1, 2, 3, 4)
                    },
                    [Ansible.Service.TriggerItem]@{
                        Type = [Ansible.Service.TriggerDataType]::Binary
                        Data = [byte[]]@(5, 6, 7, 8, 9)
                    }
                )
            }
            [Ansible.Service.Trigger]@{
                Type = [Ansible.Service.TriggerType]::Custom
                Action = [Ansible.Service.TriggerAction]::ServiceStart
                SubType = [Guid]'9fbcfc7e-7581-4d46-913b-53bb15c80c51'
                DataItems = @(
                    [Ansible.Service.TriggerItem]@{
                        Type = [Ansible.Service.TriggerDataType]::String
                        Data = 'entry 1'
                    },
                    [Ansible.Service.TriggerItem]@{
                        Type = [Ansible.Service.TriggerDataType]::String
                        Data = 'entry 2'
                    }
                )
            },
            [Ansible.Service.Trigger]@{
                Type = [Ansible.Service.TriggerType]::FirewallPortEvent
                Action = [Ansible.Service.TriggerAction]::ServiceStop
                SubType = [Guid][Ansible.Service.Trigger]::FIREWALL_PORT_CLOSE_GUID
                DataItems = [Ansible.Service.TriggerItem]@{
                    Type = [Ansible.Service.TriggerDataType]::String
                    Data = [System.Collections.Generic.List[String]]@("1234", "tcp", "imagepath", "servicename")
                }
            }
        )

        $actual = Invoke-Sc -Action qtriggerinfo -Name $serviceName

        $actual.Triggers.Count | Assert-Equals -Expected 6
        $actual.Triggers[0].Type | Assert-Equals -Expected 'DOMAIN JOINED STATUS'
        $actual.Triggers[0].Action | Assert-Equals -Expected 'STOP SERVICE'
        $actual.Triggers[0].SubType | Assert-Equals -Expected "$([Ansible.Service.Trigger]::DOMAIN_JOIN_GUID) [DOMAIN JOINED]"
        $actual.Triggers[0].Data.Count | Assert-Equals -Expected 0

        $actual.Triggers[1].Type | Assert-Equals -Expected 'NETWORK EVENT'
        $actual.Triggers[1].Action | Assert-Equals -Expected 'START SERVICE'
        $actual.Triggers[1].SubType | Assert-Equals -Expected "$([Ansible.Service.Trigger]::NAMED_PIPE_EVENT_GUID) [NAMED PIPE EVENT]"
        $actual.Triggers[1].Data.Count | Assert-Equals -Expected 1
        $actual.Triggers[1].Data[0] | Assert-Equals -Expected 'my named pipe'

        $actual.Triggers[2].Type | Assert-Equals -Expected 'NETWORK EVENT'
        $actual.Triggers[2].Action | Assert-Equals -Expected 'START SERVICE'
        $actual.Triggers[2].SubType | Assert-Equals -Expected "$([Ansible.Service.Trigger]::NAMED_PIPE_EVENT_GUID) [NAMED PIPE EVENT]"
        $actual.Triggers[2].Data.Count | Assert-Equals -Expected 1
        $actual.Triggers[2].Data[0] | Assert-Equals -Expected 'my named pipe 2'

        $actual.Triggers[3].Type | Assert-Equals -Expected 'CUSTOM'
        $actual.Triggers[3].Action | Assert-Equals -Expected 'START SERVICE'
        $actual.Triggers[3].SubType | Assert-Equals -Expected '9bf04e57-05dc-4914-9ed9-84bf992db88c [ETW PROVIDER UUID]'
        $actual.Triggers[3].Data.Count | Assert-Equals -Expected 2
        $actual.Triggers[3].Data[0] | Assert-Equals -Expected '01 02 03 04'
        $actual.Triggers[3].Data[1] | Assert-Equals -Expected '05 06 07 08 09'

        $actual.Triggers[4].Type | Assert-Equals -Expected 'CUSTOM'
        $actual.Triggers[4].Action | Assert-Equals -Expected 'START SERVICE'
        $actual.Triggers[4].SubType | Assert-Equals -Expected '9fbcfc7e-7581-4d46-913b-53bb15c80c51 [ETW PROVIDER UUID]'
        $actual.Triggers[4].Data.Count | Assert-Equals -Expected 2
        $actual.Triggers[4].Data[0] | Assert-Equals -Expected "entry 1"
        $actual.Triggers[4].Data[1] | Assert-Equals -Expected "entry 2"

        $actual.Triggers[5].Type | Assert-Equals -Expected 'FIREWALL PORT EVENT'
        $actual.Triggers[5].Action | Assert-Equals -Expected 'STOP SERVICE'
        $actual.Triggers[5].SubType | Assert-Equals -Expected "$([Ansible.Service.Trigger]::FIREWALL_PORT_CLOSE_GUID) [PORT CLOSE]"
        $actual.Triggers[5].Data.Count | Assert-Equals -Expected 1
        $actual.Triggers[5].Data[0] | Assert-Equals -Expected '1234;tcp;imagepath;servicename'

        # Remove trigger with $null
        $service.Triggers = $null

        $actual = Invoke-Sc -Action qtriggerinfo -Name $serviceName
        $actual.Triggers.Count | Assert-Equals -Expected 0

        # Add a single trigger
        $service.Triggers = [Ansible.Service.Trigger]@{
            Type = [Ansible.Service.TriggerType]::GroupPolicy
            Action = [Ansible.Service.TriggerAction]::ServiceStart
            SubType = [Guid][Ansible.Service.Trigger]::MACHINE_POLICY_PRESENT_GUID
        }

        $actual = Invoke-Sc -Action qtriggerinfo -Name $serviceName
        $actual.Triggers.Count | Assert-Equals -Expected 1
        $actual.Triggers[0].Type | Assert-Equals -Expected 'GROUP POLICY'
        $actual.Triggers[0].Action | Assert-Equals -Expected 'START SERVICE'
        $actual.Triggers[0].SubType | Assert-Equals -Expected "$([Ansible.Service.Trigger]::MACHINE_POLICY_PRESENT_GUID) [MACHINE POLICY PRESENT]"
        $actual.Triggers[0].Data.Count | Assert-Equals -Expected 0

        # Remove trigger with empty list
        $service.Triggers = @()

        $actual = Invoke-Sc -Action qtriggerinfo -Name $serviceName
        $actual.Triggers.Count | Assert-Equals -Expected 0

        # Add triggers through sc and check we get the values correctly
        $null = Invoke-Sc -Action triggerinfo -Name $serviceName -Arguments @(
            'start/namedpipe/abc',
            'start/namedpipe/def',
            'start/custom/d4497e12-ac36-4823-af61-92db0dbd4a76/11223344/aabbccdd',
            'start/strcustom/435a1742-22c5-4234-9db3-e32dafde695c/11223344/aabbccdd',
            'stop/portclose/1234;tcp;imagepath;servicename',
            'stop/networkoff'
        )

        $actual = $service.Triggers
        $actual.Count | Assert-Equals -Expected 6

        $actual[0].Type | Assert-Equals -Expected ([Ansible.Service.TriggerType]::NetworkEndpoint)
        $actual[0].Action | Assert-Equals -Expected ([Ansible.Service.TriggerAction]::ServiceStart)
        $actual[0].SubType = [Guid][Ansible.Service.Trigger]::NAMED_PIPE_EVENT_GUID
        $actual[0].DataItems.Count | Assert-Equals -Expected 1
        $actual[0].DataItems[0].Type | Assert-Equals -Expected ([Ansible.Service.TriggerDataType]::String)
        $actual[0].DataItems[0].Data | Assert-Equals -Expected 'abc'

        $actual[1].Type | Assert-Equals -Expected ([Ansible.Service.TriggerType]::NetworkEndpoint)
        $actual[1].Action | Assert-Equals -Expected ([Ansible.Service.TriggerAction]::ServiceStart)
        $actual[1].SubType = [Guid][Ansible.Service.Trigger]::NAMED_PIPE_EVENT_GUID
        $actual[1].DataItems.Count | Assert-Equals -Expected 1
        $actual[1].DataItems[0].Type | Assert-Equals -Expected ([Ansible.Service.TriggerDataType]::String)
        $actual[1].DataItems[0].Data | Assert-Equals -Expected 'def'

        $actual[2].Type | Assert-Equals -Expected ([Ansible.Service.TriggerType]::Custom)
        $actual[2].Action | Assert-Equals -Expected ([Ansible.Service.TriggerAction]::ServiceStart)
        $actual[2].SubType = [Guid]'d4497e12-ac36-4823-af61-92db0dbd4a76'
        $actual[2].DataItems.Count | Assert-Equals -Expected 2
        $actual[2].DataItems[0].Type | Assert-Equals -Expected ([Ansible.Service.TriggerDataType]::Binary)
        ,$actual[2].DataItems[0].Data | Assert-Equals -Expected ([byte[]]@(17, 34, 51, 68))
        $actual[2].DataItems[1].Type | Assert-Equals -Expected ([Ansible.Service.TriggerDataType]::Binary)
        ,$actual[2].DataItems[1].Data | Assert-Equals -Expected ([byte[]]@(170, 187, 204, 221))

        $actual[3].Type | Assert-Equals -Expected ([Ansible.Service.TriggerType]::Custom)
        $actual[3].Action | Assert-Equals -Expected ([Ansible.Service.TriggerAction]::ServiceStart)
        $actual[3].SubType = [Guid]'435a1742-22c5-4234-9db3-e32dafde695c'
        $actual[3].DataItems.Count | Assert-Equals -Expected 2
        $actual[3].DataItems[0].Type | Assert-Equals -Expected ([Ansible.Service.TriggerDataType]::String)
        $actual[3].DataItems[0].Data | Assert-Equals -Expected '11223344'
        $actual[3].DataItems[1].Type | Assert-Equals -Expected ([Ansible.Service.TriggerDataType]::String)
        $actual[3].DataItems[1].Data | Assert-Equals -Expected 'aabbccdd'

        $actual[4].Type | Assert-Equals -Expected ([Ansible.Service.TriggerType]::FirewallPortEvent)
        $actual[4].Action | Assert-Equals -Expected ([Ansible.Service.TriggerAction]::ServiceStop)
        $actual[4].SubType = [Guid][Ansible.Service.Trigger]::FIREWALL_PORT_CLOSE_GUID
        $actual[4].DataItems.Count | Assert-Equals -Expected 1
        $actual[4].DataItems[0].Type | Assert-Equals -Expected ([Ansible.Service.TriggerDataType]::String)
        ,$actual[4].DataItems[0].Data | Assert-Equals -Expected @('1234', 'tcp', 'imagepath', 'servicename')

        $actual[5].Type | Assert-Equals -Expected ([Ansible.Service.TriggerType]::IpAddressAvailability)
        $actual[5].Action | Assert-Equals -Expected ([Ansible.Service.TriggerAction]::ServiceStop)
        $actual[5].SubType = [Guid][Ansible.Service.Trigger]::NETWORK_MANAGER_LAST_IP_ADDRESS_REMOVAL_GUID
        $actual[5].DataItems.Count | Assert-Equals -Expected 0
    }

    # Cannot test PreferredNode as we can't guarantee CI is set up with NUMA support.
    # Cannot test LaunchProtection as once set we cannot remove unless rebooting
}

# setup and teardown should favour native tools to create and delete the service and not the util we are testing.
foreach ($testImpl in $tests.GetEnumerator()) {
    $serviceName = "ansible_$([System.IO.Path]::GetRandomFileName())"
    $null = New-Service -Name $serviceName -BinaryPathName ('"{0}"' -f $path) -StartupType Manual

    try {
        $test = $testImpl.Key
        &$testImpl.Value
    } finally {
        $null = Invoke-Sc -Action delete -Name $serviceName
    }
}

$module.Result.data = "success"
$module.ExitJson()
