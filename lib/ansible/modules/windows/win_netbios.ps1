#!powershell

# Copyright: (c) 2019, Thomas Moore (@tmmruk) <hi@tmmr.uk>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic

$spec = @{
    options = @{
        state = @{ type = "str"; choices = "enabled", "disabled", "default"; required = $true }
        adapter_names = @{ type = "list"; required = $false }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$state = $module.Params.state
$adapter_names = $module.Params.adapter_names

switch ( $state )
{
    'default'{ $netbiosoption = 0 }
    enabled { $netbiosoption = 1 }
    disabled { $netbiosoption = 2 }
}

if(-not $adapter_names)
{
    # Target all network adapters on the system
    $target_adapters_config = Get-CimInstance -Class Win32_NetworkAdapterConfiguration | Where-Object {$_.IPEnabled -eq $true}
}
else
{
    $target_adapters = Get-CimInstance -Class Win32_NetworkAdapter | Where-Object NetConnectionId -in $adapter_names | Select-Object MacAddress,NetConnectionId
    $target_adapters_config = Get-CimInstance -Class Win32_NetworkAdapterConfiguration | Where-Object MacAddress -in $target_adapters.MacAddress
    if(($target_adapters_config | Measure-Object).Count -ne $adapter_names.Count)
    {
        $module.FailJson("Not all of the target adapter names could be found on the system. No configuration changes have been made. $adapter_names")
    }
}

foreach($adapter in $target_adapters_config)
{

    if($adapter.TcpipNetbiosOptions -ne $netbiosoption)
    {
        if(-not $module.CheckMode)
        {
            $result = Invoke-CimMethod -InputObject $adapter -MethodName SetTcpipNetbios -Arguments @{TcpipNetbiosOptions=$netbiosoption}
            switch ( $result.ReturnValue )
            {
                0 { <#Success no reboot#> }
                1 { $module.Result.reboot_required = $true }
                100 { $module.Warn("DHCP not enabled on adapter $($adapter.MacAddress). Unable to set default. Try using disabled or enabled options instead.") }
                default { $module.FailJson("An error occurred while setting TcpipNetbios options on adapter $($adapter.MacAddress). Return code $($result.ReturnValue).") }
            }
        }
        $module.Result.changed = $true
    }


}

$module.ExitJson()
