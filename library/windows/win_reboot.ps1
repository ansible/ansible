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

$params = Parse-Args $args

If ($params.state) {
    $state = $params.state.ToString().ToLower()
    If (($state -ne 'query') -and ($state -ne 'reboot') -and ($state -ne 'shutdown')) {
        Fail-Json $result "state is '$state'; must be 'query', 'reboot' or 'shutdown'"
    }
}
Elseif (!$params.state) {
    $state = "reboot"
}

$force = Get-Attr $params "force" $false | ConvertTo-Bool;

$result = New-Object psobject @{
    changed = $false
    needs_reboot = $false
};

# Checks for reboot needed based on:
# http://blogs.technet.com/b/heyscriptingguy/archive/2013/06/11/determine-pending-reboot-status-powershell-style-part-2.aspx
try {
    $reg_con = [Microsoft.Win32.RegistryKey]::OpenBaseKey([Microsoft.Win32.RegistryHive]"LocalMachine", [Microsoft.Win32.RegistryView]"Default")

    $wmi_os = Get-WmiObject -Class Win32_OperatingSystem -Property BuildNumber, CSName
    If ($wmi_os.BuildNumber -ge 6001) {
        $reg_cbs = $reg_con.OpenSubKey("SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\")
        $reg_cbs_subkeys = $reg_cbs.GetSubKeyNames()
        If ($reg_cbs_subkeys -contains "RebootPending") {
            $result.needs_reboot = $true
        }
    }

    $reg_wuau = $reg_con.OpenSubKey("SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\")
    $req_wuau_subkeys = $reg_wuau.GetSubKeyNames()
    If ($req_wuau_subkeys -contains "RebootRequired") {
        $result.needs_reboot = $true
    }

    $reg_sm = $reg_con.OpenSubKey("SYSTEM\CurrentControlSet\Control\Session Manager\")
    $reg_pfro = $reg_sm.GetValue("PendingFileRenameOperations", $null)
    If ($reg_pfro) {
        $result.needs_reboot = $true
    }

    $reg_con.Close()
}
catch {
    Fail-Json $result $_.Exception.Message
}

If (($force -eq $true) -or ($result.needs_reboot -eq $true)) {
    If ($state -eq "reboot") {
        Restart-Computer -Force
        $result.changed = $true
    }
    ElseIf ($state -eq "shutdown") {
        Stop-Computer -Force
        $result.changed = $true
    }
}

Exit-Json $result;
