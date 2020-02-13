#!powershell

# Copyright: (c) 2020, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#AnsibleRequires -CSharpUtil Ansible.Service

$spec = @{
    options = @{
        name = @{ type = "str" }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$name = $module.Params.name

$module.Result.exists = $false
$module.Result.services = @(foreach ($rawService in (Get-Service -Name $name -ErrorAction SilentlyContinue)) {
    try {
        $service = New-Object -TypeName Ansible.Service.Service -ArgumentList @(
            $rawService.Name, [Ansible.Service.ServiceRights]'EnumerateDependents, QueryConfig, QueryStatus'
        )
    } catch [Ansible.Service.ServiceManagerException] {
        # ERROR_ACCESS_DENIED, ignore the service and continue on.
        if ($_.Exception.InnerException -and $_.Exception.InnerException.NativeErrorCode -eq 5) {
            $module.Warn("Failed to access service '$($rawService.Name) to get more info, ignoring")
            continue
        }

        throw
    }
    $module.Result.exists = $true

    $controlsAccepted = @($service.ControlsAccepted.ToString() -split ',' | ForEach-Object -Process {
        switch ($_.Trim()) {
            Stop { 'stop' }
            PauseContinue { 'pause_continue' }
            Shutdown { 'shutdown' }
            ParamChange { 'param_change' }
            NetbindChange { 'netbind_change' }
            HardwareProfileChange { 'hardware_profile_change' }
            PowerEvent { 'power_event' }
            SessionChange { 'session_change' }
            PreShutdown { 'pre_shutdown' }
        }
    })

    $rawFailureActions = $service.FailureActions
    $failureActions = @(foreach ($action in $rawFailureActions.Actions) {
        [Ordered]@{
            type = switch ($action.Type) {
                None { 'none' }
                Reboot { 'reboot' }
                Restart { 'restart' }
                RunCommand { 'run_command' }
            }
            delay_ms = $action.Delay
        }
    })

    # LaunchProtection is only valid in Windows 8.1 (2012 R2) or above.
    $launchProtection = 'none'
    if ($service.LaunchProtection) {
        $launchProtection = switch ($service.LaunchProtection) {
            None { 'none' }
            Windows { 'windows' }
            WindowsLight { 'windows_light' }
            AntimalwareLight { 'antimalware_light' }
        }
    }

    $serviceFlags = @($service.ServiceFlags.ToString() -split ',' | ForEach-Object -Process {
        switch ($_.Trim()) {
            RunsInSystemProcess { 'runs_in_system_process' }
        }
    })

    # The ServiceType value can contain other flags which are represented by other properties, this strips them out
    # so we don't include them in the service_type return value.
    $serviceType = [uint32]$service.ServiceType -band -bnot [uint32][Ansible.Service.ServiceType]::InteractiveProcess
    $serviceType = $serviceType -band -bnot [uint32][Ansible.Service.ServiceType]::UserServiceInstance
    $serviceType = switch (([Ansible.Service.ServiceType]$serviceType).ToString()) {
        KernelDriver { 'kernel_driver' }
        FileSystemDriver { 'file_system_driver' }
        Adapter { 'adapter' }
        RecognizerDriver { 'recognizer_driver' }
        Win32OwnProcess { 'win32_own_process' }
        Win32ShareProcess { 'win32_share_process' }
        UserOwnprocess { 'user_own_process' }
        UserShareProcess { 'user_share_process' }
        PkgService { 'pkg_service' }
    }

    $startType = switch ($service.StartType) {
        BootStart { 'boot_start' }
        SystemStart { 'system_start' }
        AutoStart { 'auto' }
        DemandStart { 'manual' }
        Disabled { 'disabled' }
        AutoStartDelayed { 'delayed' }
    }

    $state = switch ($service.State) {
        Stopped { 'stopped' }
        StartPending { 'start_pending' }
        StopPending { 'stop_pending' }
        Running { 'started' }
        ContinuePending { 'continue_pending' }
        PausePending { 'pause_pending' }
        paused { 'paused' }
    }

    $triggers = @(foreach ($trigger in $service.Triggers) {
        [Ordered]@{
            action = switch($trigger.Action) {
                ServiceStart { 'start_service' }
                ServiceStop { 'stop_service' }
            }
            type = switch($trigger.Type) {
                DeviceInterfaceArrival { 'device_interface_arrival' }
                IpAddressAvailability { 'ip_address_availability' }
                DomainJoin { 'domain_join' }
                FirewallPortEvent { 'firewall_port_event' }
                GroupPolicy { 'group_policy' }
                NetworkEndpoint { 'network_endpoint' }
                Custom { 'custom' }
            }
            sub_type = switch($trigger.SubType.ToString()) {
                ([Ansible.Service.Trigger]::NAMED_PIPE_EVENT_GUID) { 'named_pipe_event' }
                ([Ansible.Service.Trigger]::RPC_INTERFACE_EVENT_GUID) { 'rpc_interface_event' }
                ([Ansible.Service.Trigger]::DOMAIN_JOIN_GUID) { 'domain_join' }
                ([Ansible.Service.Trigger]::DOMAIN_LEAVE_GUID) { 'domain_leave' }
                ([Ansible.Service.Trigger]::FIREWALL_PORT_OPEN_GUID) { 'firewall_port_open' }
                ([Ansible.Service.Trigger]::FIREWALL_PORT_CLOSE_GUID) { 'firewall_port_close' }
                ([Ansible.Service.Trigger]::MACHINE_POLICY_PRESENT_GUID) { 'machine_policy_present' }
                ([Ansible.Service.Trigger]::USER_POLICY_PRESENT_GUID) { 'user_policy_present' }
                ([Ansible.Service.Trigger]::NETWORK_MANAGER_FIRST_IP_ADDRESS_ARRIVAL_GUID) { 'network_first_ip_arrival' }
                ([Ansible.Service.Trigger]::NETWORK_MANAGER_LAST_IP_ADDRESS_REMOVAL_GUID) { 'network_last_ip_removal' }
                default { 'custom' }
            }
            sub_type_guid = $trigger.SubType.ToString()
            data_items = @(foreach ($dataItem in $trigger.DataItems) {
                $dataValue = $dataItem.Data

                # We only need to convert byte and byte[] to a Base64 string, the rest can be serialised as is.
                if ($dataValue -is [byte]) {
                    $dataValue = [byte[]]@($dataValue)
                }

                if ($dataValue -is [byte[]]) {
                    $dataValue = [System.Convert]::ToBase64String($dataValue)
                }

                [Ordered]@{
                    type = switch ($dataItem.Type) {
                        Binary { 'binary' }
                        String { 'string' }
                        Level { 'level' }
                        KeywordAny { 'keyword_any' }
                        KeywordAll { 'keyword_all' }
                    }
                    data = $dataValue
                }
            })
        }
    })

    # These should closely reflect the options for win_service
    [Ordered]@{
        checkpoint = $service.Checkpoint
        controls_accepted = $controlsAccepted
        dependencies = $service.DependentOn
        dependency_of = $service.DependedBy
        description = $service.Description
        desktop_interact = $service.ServiceType.HasFlag([Ansible.Service.ServiceType]::InteractiveProcess)
        display_name = $service.DisplayName
        error_control = $service.ErrorControl.ToString().ToLowerInvariant()
        failure_actions = $failureActions
        failure_actions_on_non_crash_failure = $service.FailureActionsOnNonCrashFailures
        failure_command = $rawFailureActions.Command
        failure_reboot_msg = $rawFailureActions.RebootMsg
        failure_reset_period_sec = $rawFailureActions.ResetPeriod
        launch_protection = $launchProtection
        load_order_group = $service.LoadOrderGroup
        name = $service.ServiceName
        path = $service.Path
        pre_shutdown_timeout_ms = $service.PreShutdownTimeout
        preferred_node = $service.PreferredNode
        process_id = $service.ProcessId
        required_privileges = $service.RequiredPrivileges
        service_exit_code = $service.ServiceExitCode
        service_flags = $serviceFlags
        service_type = $serviceType
        sid_info = $service.ServiceSidInfo.ToString().ToLowerInvariant()
        start_mode = $startType
        state = $state
        triggers = $triggers
        username = $service.Account.Value
        wait_hint_ms = $service.WaitHint
        win32_exit_code = $service.Win32ExitCode
    }
})

$module.ExitJson()
