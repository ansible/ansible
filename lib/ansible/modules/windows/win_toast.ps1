#!powershell
# This file is part of Ansible
#
# Copyright 2017, Jon Hawkesworth (@jhawkesworth) <figs@unity.demon.co.uk>
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

# WANT_JSON
# POWERSHELL_COMMON

$ErrorActionPreference = "Stop"

# version check
$osversion = [Environment]::OSVersion
$lowest_version = 10
if ($osversion.Version.Major -lt $lowest_version ) {
   Fail-Json $result "Sorry, this version of windows, $osversion, does not support Toast notifications.  Toast notifications are available from version $lowest_version" 
}

$stopwatch = [system.diagnostics.stopwatch]::startNew()
$now = [DateTime]::Now
$default_title = "Notification: " + $now.ToShortTimeString()

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

# $expire_at = Get-AnsibleParam -obj $params -name "msg" -type "str"
$expire_secs = Get-AnsibleParam -obj $params -name "expire_secs" -type "int" -default 45
$group = Get-AnsibleParam -obj $params -name "group" -type "str" -default "Powershell"
$msg = Get-AnsibleParam -obj $params -name "msg" -type "str" -default "Hello world!"
$popup = Get-AnsibleParam -obj $params -name "popup" -type "bool" -default $true
$tag = Get-AnsibleParam -obj $params -name "tag" -type "str" -default "Ansible"
$title = Get-AnsibleParam -obj $params -name "title" -type "str" -default $default_title

$timespan = New-TimeSpan -Seconds $expire_secs
$expire_at = $now + $timespan
$expire_at_utc = $($expire_at.ToUniversalTime()|Out-String).Trim()

$result = @{
    changed = $false
    expire_secs = $expire_secs
    expire_at = $expire_at.ToString()
    expire_at_utc = $expire_at_utc
    group = $group    
    msg = $msg
    popup = $popup
    tag = $tag
    title = $title
}


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
      Start-Sleep -Seconds $expire_secs
   }
} catch {
  $excep= $_
  Fail-Json $result "Failed to create toast notifier, exception was $($excep.Exception.Message) stack trace $($excep.ScriptStackStrace)".
}




$endsend_at = Get-Date| Out-String
$stopwatch.Stop()

$result.runtime_seconds = $stopwatch.Elapsed.TotalSeconds
$result.sent_localtime = $endsend_at.Trim()
  
Exit-Json $result
