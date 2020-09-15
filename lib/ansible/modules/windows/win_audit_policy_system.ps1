#!powershell

# Copyright: (c) 2017, Noah Sparks <nsparks@outlook.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.CommandUtil

$ErrorActionPreference = 'Stop'

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$results = @{
    changed = $false
}

######################################
### populate sets for -validateset ###
######################################
$categories_rc = run-command -command 'auditpol /list /category /r'
$subcategories_rc = run-command -command 'auditpol /list /subcategory:* /r'

If ($categories_rc.item('rc') -eq 0)
{
    $categories = ConvertFrom-Csv $categories_rc.item('stdout') | Select-Object -expand Category*
}
Else
{
    Fail-Json -obj $results -message "Failed to retrive audit policy categories. Please make sure the auditpol command is functional on
    the system and that the account ansible is running under is able to retrieve them. $($_.Exception.Message)"
}

If ($subcategories_rc.item('rc') -eq 0)
{
    $subcategories = ConvertFrom-Csv $subcategories_rc.item('stdout') | Select-Object -expand Category* |
    Where-Object {$_ -notin $categories}
}
Else
{
    Fail-Json -obj $results -message "Failed to retrive audit policy subcategories. Please make sure the auditpol command is functional on
    the system and that the account ansible is running under is able to retrieve them. $($_.Exception.Message)"
}

######################
### ansible params ###
######################
$category = Get-AnsibleParam -obj $params -name "category" -type "str" -ValidateSet $categories
$subcategory = Get-AnsibleParam -obj $params -name "subcategory" -type "str" -ValidateSet $subcategories
$audit_type = Get-AnsibleParam -obj $params -name "audit_type" -type "list" -failifempty -

########################
### Start Processing ###
########################
Function Get-AuditPolicy ($GetString) {
    $auditpolcsv = Run-Command -command $GetString
    If ($auditpolcsv.item('rc') -eq 0)
    {
        $Obj = ConvertFrom-CSV $auditpolcsv.item('stdout') | Select-Object @{n='subcategory';e={$_.Subcategory.ToLower()}},
        @{n='audit_type';e={$_."Inclusion Setting".ToLower()}}
    }
    Else {
        return $auditpolcsv.item('stderr')
    }

    $HT = @{}
    Foreach ( $Item in $Obj )
    {
        $HT.Add($Item.subcategory,$Item.audit_type)
    }
    $HT
}

################
### Validate ###
################

#make sure category and subcategory are valid
If (-Not $category -and -Not $subcategory) {Fail-Json -obj $results -message "You must provide either a Category or Subcategory parameter"}
If ($category -and $subcategory) {Fail-Json -obj $results -message "Must pick either a specific subcategory or category. You cannot define both"}


$possible_audit_types = 'success','failure','none'
$audit_type | ForEach-Object {
    If ($_ -notin $possible_audit_types)
    {
        Fail-Json -obj $result -message "$_ is not a valid audit_type. Please choose from $($possible_audit_types -join ',')"
    }
}

#############################################################
### build lists for setting, getting, and comparing rules ###
#############################################################
$audit_type_string = $audit_type -join ' and '

$SetString = 'auditpol /set'
$GetString = 'auditpol /get /r'

If ($category) {$SetString = "$SetString /category:`"$category`""; $GetString = "$GetString /category:`"$category`""}
If ($subcategory) {$SetString= "$SetString /subcategory:`"$subcategory`""; $GetString = "$GetString /subcategory:`"$subcategory`""}


Switch ($audit_type_string)
{
    'success and failure' {$SetString = "$SetString /success:enable /failure:enable"; $audit_type_check = $audit_type_string}
    'failure' {$SetString = "$SetString /success:disable /failure:enable"; $audit_type_check = $audit_type_string}
    'success' {$SetString = "$SetString /success:enable /failure:disable"; $audit_type_check = $audit_type_string}
    'none' {$SetString = "$SetString /success:disable /failure:disable"; $audit_type_check = 'No Auditing'}
    default {Fail-Json -obj $result -message "It seems you have specified an invalid combination of items for audit_type. Please review documentation"}
}

#########################
### check Idempotence ###
#########################

$CurrentRule = Get-AuditPolicy $GetString

#exit if the audit_type is already set properly for the category
If (-not ($CurrentRule.Values | Where-Object {$_ -ne $audit_type_check}) )
{
    $results.current_audit_policy = Get-AuditPolicy $GetString
    Exit-Json -obj $results
}

####################
### Apply Change ###
####################

If (-not $check_mode)
{
    $ApplyPolicy = Run-Command -command $SetString

    If ($ApplyPolicy.Item('rc') -ne 0)
    {
        $results.current_audit_policy = Get-AuditPolicy $GetString
        Fail-Json $results "Failed to set audit policy - $($_.Exception.Message)"
    }
}

$results.changed = $true
$results.current_audit_policy = Get-AuditPolicy $GetString
Exit-Json $results
