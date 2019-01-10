#!powershell

# Copyright: (c) 2018, Daniele Lazzari  <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options             = @{
        query                    = @{ type = "str"; required = $true }
        database                 = @{ type = "str"; default = "master" }
        query_timeout            = @{ type = "int"; default = 60 }
        server_instance          = @{ type = "str"; default = $env:COMPUTERNAME }
        server_instance_user     = @{ type = "str"; default = $NULL }
        server_instance_password = @{ type = "str"; default = $NULL }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$query = $module.Params.query
$queryTimeout = $module.Params.query_timeout
$database = $module.Params.database
$serverInstance = $module.Params.server_instance
$serverInstanceUser = $module.Params.server_instance_user
$serverInstancePassword = $module.Params.server_instance_password

Function Invoke-Query {
    Param(
        [string]$Query,
        [int]$QueryTimeout,
        [string]$Database,
        [string]$ServerInstance,
        [string]$ServerInstanceUser,
        [string]$ServerInstancePassword,
        [bool]$CheckMode
    )
    $output = @()
    try {
        if (!($CheckMode)) {
            $sql_params = @{
                ServerInstance = $ServerInstance
                Database       = $Database
                Query          = $Query
                QueryTimeout   = $QueryTimeout
            }
            if ($ServerInstanceUser -and $ServerInstancePassword) {
                $sql_params["Username"] = $ServerInstanceUser
                $sql_params["Password"] = $ServerInstancePassword
            }
            $res = Invoke-SqlCmd @sql_params

        }
    }
    catch {
        $module.Result.query = $Query
        $module.Result.database = $Database
        $module.FailJson("Error: $($_.exception.message)")
    }
    if ($res) {
        if ($res -is [Array]) {
            $columns = $res[0].Table.Columns.Caption
        } 
        else {
            $columns = $res.Table.Columns.Caption
        }
        $output = @($res |Select-Object -Property $columns)
    }
    $module.Result.output = $output
    $module.Result.changed = $true
    $module.ExitJson()
}


Invoke-Query -Query $query `
    -QueryTimeout $queryTimeout `
    -Database $database `
    -ServerInstance $serverInstance `
    -ServerInstanceUser $serverInstanceUser `
    -ServerInstancePassword $serverInstancePassword `
    -CheckMode $module.CheckMode
