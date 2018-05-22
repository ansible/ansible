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

$results = @{changed=$false}

$parsed_args = Parse-Args $args
$jid = Get-AnsibleParam $parsed_args "jid" -failifempty $true -resultobj $results
$mode = Get-AnsibleParam $parsed_args "mode" -Default "status" -ValidateSet "status","cleanup"
$_remote_tmp = Get-AnsibleParam $parsed_args "_ansible_remote_tmp" -type "path" -default $env:TMP

$log_path = [System.IO.Path]::Combine($_remote_tmp, ".ansible_async", $jid)

If(-not $(Test-Path $log_path))
{
    Fail-Json @{ansible_job_id=$jid; started=1; finished=1} "could not find job"
}

If($mode -eq "cleanup") {
    Remove-Item $log_path -Recurse
    Exit-Json @{ansible_job_id=$jid; erased=$log_path}
}

# NOT in cleanup mode, assume regular status mode
# no remote kill mode currently exists, but probably should
# consider log_path + ".pid" file and also unlink that above

$data = $null
Try {
    $data_raw = Get-Content $log_path

    # TODO: move this into module_utils/powershell.ps1?
    $jss = New-Object System.Web.Script.Serialization.JavaScriptSerializer
    $data = $jss.DeserializeObject($data_raw)
}
Catch {
    If(-not $data_raw) {
        # file not written yet?  That means it is running
        Exit-Json @{results_file=$log_path; ansible_job_id=$jid; started=1; finished=0}
    }
    Else {
        Fail-Json @{ansible_job_id=$jid; results_file=$log_path; started=1; finished=1} "Could not parse job output: $data"
    }
}

If (-not $data.ContainsKey("started")) {
    $data['finished'] = 1
    $data['ansible_job_id'] = $jid
}
ElseIf (-not $data.ContainsKey("finished")) {
    $data['finished'] = 0
}

Exit-Json $data
