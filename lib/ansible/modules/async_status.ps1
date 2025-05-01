#!powershell

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

using namespace Ansible.Basic
using namespace System.IO

$spec = @{
    options = @{
        _async_dir = @{
            type = "path"
            required = $true
        }
        jid = @{
            type = "str"
            required = $true
        }
        mode = @{
            type = "str"
            choices = "cleanup", "status"
            default = "status"
        }
    }
    supports_check_mode = $true
}
$module = [AnsibleModule]::Create($args, $spec)

$asyncDir = $module.Params._async_dir
$jid = $module.Params.jid
$mode = $module.Params.mode

$module.Result.ansible_job_id = $jid

$logPath = [Path]::Combine($asyncDir, $jid)
if (-not (Test-Path -LiteralPath $logPath)) {
    $module.Result.finished = 1
    $module.Result.started = 1
    $module.FailJson("could not find job at '$asyncDir'")
}

if ($mode -eq "cleanup") {
    Remove-Item -LiteralPath $logPath -Recurse
    $module.Result.erased = $logPath
    $module.ExitJson()
}

$module.Result.finished = 0
$module.Result.started = 1

# NOT in cleanup mode, assume regular status mode
# no remote kill mode currently exists, but probably should
# consider log_path + ".pid" file and also unlink that above

$rawData = Get-Content -LiteralPath $logPath -Raw
if (-not $rawData) {
    # file not written yet? That means it is running
    $module.Result.results_file = $logPath
    $module.ExitJson()
}

try {
    $data = ConvertFrom-Json -InputObject $rawData
}
catch {
    $module.Result.results_file = $logPath
    $module.Result.finished = 1
    $module.FailJson("Could not parse job output: $rawData", $_)
}

foreach ($prop in $data.PSObject.Properties) {
    $module.Result[$prop.Name] = $prop.Value
}

$module.ExitJson()
