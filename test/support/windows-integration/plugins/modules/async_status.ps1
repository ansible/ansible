#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$results = @{changed=$false}

$parsed_args = Parse-Args $args
$jid = Get-AnsibleParam $parsed_args "jid" -failifempty $true -resultobj $results
$mode = Get-AnsibleParam $parsed_args "mode" -Default "status" -ValidateSet "status","cleanup"

# parsed in from the async_status action plugin
$async_dir = Get-AnsibleParam $parsed_args "_async_dir" -type "path" -failifempty $true

$log_path = [System.IO.Path]::Combine($async_dir, $jid)

If(-not $(Test-Path $log_path))
{
    Fail-Json @{ansible_job_id=$jid; started=$true; finished=$true} "could not find job at '$async_dir'"
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
    $data['finished'] = $true
    $data['ansible_job_id'] = $jid
}
ElseIf (-not $data.ContainsKey("finished")) {
    $data['finished'] = $false
}

Exit-Json $data
