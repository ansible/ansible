#!powershell
# This file is part of Ansible
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
$params = Parse-Args $args
$State = Get-AnsibleParam -obj $params -name "state" -failifempty $true
$TargetFile = Get-AnsibleParam -obj $params -name "src" -failifempty $true
$ShortcutFile = Get-AnsibleParam -obj $params -name "dest" -failifempty $true
$Arguments = Get-AnsibleParam -obj $params -name "arguments" -failempty $true
$Directory =  Get-AnsibleParam -obj $params -name "directory" -failempty $true
$Hotkey = Get-AnsibleParam -obj $params -name "hotkey" -failifempty $true
$Description = Get-AnsibleParam -obj $params -name "desc" -failifempty $true
$IconLocation = Get-AnsibleParam -obj $params -name "icon" -failifempty $true
$result = New-Object psobject @{
    changed = $FALSE
}
try
{
 if ($State -eq "absent")
 {
   if(Test-Path $ShortcutFile)
   {
     Remove-Item -Path "$ShortcutFile";
     $result.changed = $TRUE
   }
   else
    {
     Fail-Json (New-Object psobject) "missing required argument: Provide valid shortcut path to remove"
    }
  }
 elseif($State -eq "present")
 {
  if(!(Test-Path $TargetFile))
  {
   Fail-Json (New-Object psobject) "missing required argument: Provide valid exe path to create Shortcut"
  }
 $WScriptShell = New-Object -ComObject WScript.Shell
 $targetPath = $WScriptShell.CreateShortcut($ShortcutFile).TargetPath
 $ShortcutKey = $WScriptShell.CreateShortcut($ShortcutFile).HotKey
 $ShortcutIconloc = $WScriptShell.CreateShortcut($ShortcutFile).IconLocation
 $ShortcutDescription =  $WScriptShell.CreateShortcut($ShortcutFile).Description
 $ShortcutDirectory =  $WScriptShell.CreateShortcut($ShortcutFile).WorkingDirectory
 $ShortcutArguments = $WscriptShell.CreateShortcut($ShortcutFile).Arguments
 if(($targetPath -eq $TargetFile) -and ($ShortcutKey -eq $Hotkey) -and ($ShortcutIconloc -eq $IconLocation) -and ($ShortcutDescription -eq $Description) -and ($ShortcutDirectory -eq $Directory) -and ($ShortcutArguments -eq $Arguments))
  {
   $result.changed = $FALSE
  }
  else
  {
   $Shortcut = $WScriptShell.CreateShortcut($ShortcutFile)
   $Shortcut.TargetPath = $TargetFile
   $ShortCut.Arguments = $Arguments
   $Shortcut.WorkingDirectory = $Directory
   $Shortcut.HotKey = $Hotkey
   $Shortcut.IconLocation = $IconLocation
   $Shortcut.Description = $Description
   $Shortcut.Save()
   $result.changed = $TRUE
  }
 }
else
 {
  Fail-Json (New-Object psobject) "missing required argument: Provide state either :present or absent"
 }
}
catch
{
 Fail-Json $result $_.Exception.Message
}
Exit-Json $result
