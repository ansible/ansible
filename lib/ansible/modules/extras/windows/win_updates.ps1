#!powershell
# This file is part of Ansible
#
# Copyright 2014, Trond Hindenes <trond@hindenes.com>
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

function Write-Log
{
  param
  (
    [parameter(mandatory=$false)]
    [System.String]
    $message
  )

  $date = get-date -format 'yyyy-MM-dd hh:mm:ss.zz'

  Write-Host "$date $message"

  Out-File -InputObject "$date $message" -FilePath $global:LoggingFile -Append
}

$params = Parse-Args $args;
$result = New-Object PSObject;
Set-Attr $result "changed" $false;

if(($params.logPath).Length -gt 0) {
  $global:LoggingFile = $params.logPath
} else {
  $global:LoggingFile = "c:\ansible-playbook.log"
}
if ($params.category) {
  $category = $params.category
} else {
  $category = "critical"
}

$installed_prior = get-wulist -isinstalled | foreach { $_.KBArticleIDs }
set-attr $result "updates_already_present" $installed_prior

write-log "Looking for updates in '$category'"
set-attr $result "updates_category" $category
$to_install = get-wulist -category $category
$installed = @()
foreach ($u in $to_install) {
  $kb = $u.KBArticleIDs
  write-log "Installing $kb - $($u.Title)"
  $install_result = get-wuinstall -KBArticleID $u.KBArticleIDs -acceptall -ignorereboot
  Set-Attr $result "updates_installed_KB$kb" $u.Title
  $installed += $kb
}
write-log "Installed: $($installed.count)"
set-attr $result "updates_installed" $installed
set-attr $result "updates_installed_count" $installed.count
$result.changed = $installed.count -gt 0

$installed_afterwards = get-wulist -isinstalled | foreach { $_.KBArticleIDs }
set-attr $result "updates_installed_afterwards" $installed_afterwards

$reboot_needed = Get-WURebootStatus
write-log $reboot_needed
if ($reboot_needed -match "not") {
  write-log "Reboot not required"
} else {
  write-log "Reboot required"
  Set-Attr $result "updates_reboot_needed" $true
  $result.changed = $true
}

Set-Attr $result "updates_success" "true"
Exit-Json $result;
