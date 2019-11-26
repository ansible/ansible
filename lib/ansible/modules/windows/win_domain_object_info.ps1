#!powershell

# Copyright: (c) 2019, Shachaf Goldstein <shachaf.gold@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

Set-StrictMode -Version 2.0

$spec = @{
    options = @{
        filter = @{ type = "str"; required = $false; }
        identity = @{ type = "str"; required = $false}
        include_deleted_objects = @{ type = "bool"; required = $false; default = $false }
        json_depth = @{ type = "int"; required = $false; default = 3 }
        properties = @{ type = "list"; required = $false; default = @("*"); elements = "str" }
        server = @{ type = "str"; required = $false; aliases = @("domain_server") }
        ldap_filter = @{ type = "str"; required = $false; }
        search_scope = @{ type = "str"; choices = @("Base","OneLevel","Subtree"); required = $false; default = "Subtree" }
        search_base = @{ type = "str"; required = $false; }
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
$include_deleted_objects = $module.Params.include_deleted_objects
$properties = $module.Params.properties
$server = $module.Params.server
$ldap_filter = $module.Params.ldap_filter
$search_scope = $module.Params.search_scope
$search_base = $module.Params.search_base
$username = $module.Params.username
$password = ConvertTo-SecureString -AsPlainText -Force -String $module.Params.password
$json_depth = $module.Params.json_depth

$module.result = @{
    objects = @()
}

$args_hashtable = @{}

if ($null -ne $filter)
{
    $args_hashtable.Filter = $filter
}

if ($null -ne $identity)
{
    $args_hashtable.Identity = $identity
}

if ($null -ne $includeDeletedObjects)
{
    $args_hashtable.IncludeDeletedObjects = $include_deleted_objects
}

if ($null -ne $properties)
{
    $args_hashtable.Properties = $properties
}

if ($null -ne $server)
{
    $args_hashtable.Server = $server
}

if ($null -ne $ldapFilter)
{
    $args_hashtable.LDAPFilter = $ldap_filter
}

if ($null -ne $searchScope)
{
    $args_hashtable.SearchScope = $search_scope
}

if ($null -ne $searchBase)
{
    $args_hashtable.SearchBase = $search_base
}

if ($null -ne $username -and $null -ne $password)
{
    $args_hashtable.Credential = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $username, $password
}

$result.objects = Get-ADObject @args_hashtable | ForEach-Object {$_ | ConvertTo-Json -Depth $json_depth -Compress}

$module.ExitJson()
