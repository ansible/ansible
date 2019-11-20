#!powershell

# Copyright: (c) 2019, Shachaf Goldstein <shachaf.gold@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

Set-StrictMode -Version 2.0

$spec = @{
    options = @{
        filter = @{ type = "str"; required = $false; }
        identity = @{ type = "str"; required = $false}
        includeDeletedObjects = @{ type = "bool"; required = $false; default = $false }
        jsonDepth = @{ type = "int"; required = $false; default = 3 }
        properties = @{ type = "list"; required = $false; default = @("*"); elements = "str" }
        server = @{ type = "str"; required = $false; aliases = @("domain_server") }
        ldapFilter = @{ type = "str"; required = $false; }
        searchScope = @{ type = "str"; choices = @("Base","OneLevel","Subtree"); required = $false; default = "Subtree" }
        SearchBase = @{ type = "str"; required = $false; }
        username = @{ type = "str"; required = $false; aliases = @("domain_username") }
        password = @{ type = "str"; required = $false; aliases = @("domain_password") }
    }
    required_together = @(,@("username","password"))
    required_one_of = @(,@("filter","identity","ldapFilter"))
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$filter = $module.Params.filter
$identity = $module.Params.identity
$includeDeletedObjects = $module.Params.includeDeletedObjects
$properties = $module.Params.properties
$server = $module.Params.searchScope
$ldapFilter = $module.Params.ldapFilter
$searchScope = $module.Params.searchScope
$searchBase = $module.Params.searchBase
$username = $module.Params.username
$password = $module.Params.password
$jsonDepth = $module.Params.jsonDepth

$result = @{
    changed = $false
    objects = @()
}

$args_array = @{}

if ($null -ne $filter)
{
    $args_array.filter = $filter
}

if ($null -ne $identity)
{
    $args_array.identity = $identity
}

if ($null -ne $includeDeletedObjects)
{
    $args_array.includeDeletedObjects = $includeDeletedObjects
}

if ($null -ne $properties)
{
    $args_array.properties = $properties
}

if ($null -ne $server)
{
    $args_array.server = $server
}

if ($null -ne $ldapFilter)
{
    $args_array.ldapFilter = $ldapFilter
}

if ($null -ne $searchScope)
{
    $args_array.searchScope = $searchScope
}

if ($null -ne $searchBase)
{
    $args_array.searchBase = $searchBase
}

if ($null -ne $username -and $null -ne $password)
{
    $args_array.Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $username, $password
}

Get-ADObject @args_array | ForEach-Object {
    $result.objects += ,($_ | ConvertTo-Json -Depth $jsonDepth -Compress)
}

$module.ExitJson()