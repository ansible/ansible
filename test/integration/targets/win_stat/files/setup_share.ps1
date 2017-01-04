$share_stat = Get-WmiObject -Class Win32_Share -Filter "name='folder-share'"
If ($share_stat) {
    $share_stat.Delete()
}
$wmi = [wmiClass] 'Win32_Share'
$wmi.Create($args[0], 'folder-share', 0)
