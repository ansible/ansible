if (Test-Path -Path '{{win_output_dir}}\win_reboot_test') {
    New-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager' `
        -Name PendingFileRenameOperations `
        -Value @("\??\{{win_output_dir}}\win_reboot_test`0") `
        -PropertyType MultiString
    Restart-Computer -Force
    exit 1
}
