$share_name = $args[1]
$share_stat = Get-WmiObject -Class Win32_Share -Filter "name='$share_name'"
If ($share_stat) {
    $share_stat.Delete()
}
$wmi = [wmiClass] 'Win32_Share'
$wmi.Create($args[0], $share_name, 0)
