# Copyright (c) 2020 Ansible Project
# # Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

Function Get-PSUtilSpec {
    <#
    .SYNOPSIS
    Shared util spec test
    #>
    @{
        options = @{
          option1 = @{ type = 'str'; required = $true; aliases = 'alias1' }
        }
    }
}

Export-ModuleMember -Function Get-PSUtilSpec
