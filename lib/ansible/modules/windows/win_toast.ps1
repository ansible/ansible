#!powershell

# Copyright: (c) 2017, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = "Stop"

# version check
$osversion = [Environment]::OSVersion
$lowest_version = 10
if ($osversion.Version.Major -lt $lowest_version ) {
   Fail-Json -obj $result -message "Sorry, this version of windows, $osversion, does not support Toast notifications.  Toast notifications are available from version $lowest_version" 
}

$stopwatch = [system.diagnostics.stopwatch]::startNew()
$now = [DateTime]::Now
$default_title = "Notification: " + $now.ToShortTimeString()

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$expire_seconds = Get-AnsibleParam -obj $params -name "expire" -type "int" -default 45
$group = Get-AnsibleParam -obj $params -name "group" -type "str" -default "Powershell"
$msg = Get-AnsibleParam -obj $params -name "msg" -type "str" -default "Hello world!"
$popup = Get-AnsibleParam -obj $params -name "popup" -type "bool" -default $true
$tag = Get-AnsibleParam -obj $params -name "tag" -type "str" -default "Ansible"
$title = Get-AnsibleParam -obj $params -name "title" -type "str" -default $default_title

$timespan = New-TimeSpan -Seconds $expire_seconds
$expire_at = $now + $timespan
$expire_at_utc = $($expire_at.ToUniversalTime()|Out-String).Trim()

$result = @{
    changed = $false
    expire_at = $expire_at.ToString()
    expire_at_utc = $expire_at_utc
    toast_sent = $false
}

# If no logged in users, there is no notifications service,
# and no-one to read the message, so exit but do not fail
# if there are no logged in users to notify.
 
if ((Get-Process -Name explorer -ErrorAction SilentlyContinue).Count -gt 0){

  [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
  $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText01)
  
  #Convert to .NET type for XML manipulation
  $toastXml = [xml] $template.GetXml()
  $toastXml.GetElementsByTagName("text").AppendChild($toastXml.CreateTextNode($title)) > $null
  # TODO add subtitle
  
  #Convert back to WinRT type
  $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
  $xml.LoadXml($toastXml.OuterXml)
  
  $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
  $toast.Tag = $tag
  $toast.Group = $group
  $toast.ExpirationTime = $expire_at
  $toast.SuppressPopup = -not $popup
  
  try {
     $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($msg)
     if (-not $check_mode) {
        $notifier.Show($toast)
        $result.toast_sent = $true
        Start-Sleep -Seconds $expire_seconds
     }
  } catch {
    $excep = $_
    $result.exception = $excep.ScriptStackTrace
    Fail-Json -obj $result -message "Failed to create toast notifier: $($excep.Exception.Message)"
  }
} else {
   $result.toast_sent = $false
   $result.no_toast_sent_reason = 'No logged in users to notifiy'
}

$endsend_at = Get-Date | Out-String
$stopwatch.Stop()

$result.time_taken = $stopwatch.Elapsed.TotalSeconds
$result.sent_localtime = $endsend_at.Trim()
  
Exit-Json -obj $result
