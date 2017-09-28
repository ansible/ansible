#!powershell
# Copyright (c) 2017 Noah Sparks <nsparks@outlook.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = 'Stop'

$params = Parse-Args -arguments $args -supports_check_mode $true

$results = @{
    changed = $false
}

#populate sets for -validateset
Try {
    $categories = (auditpol /list /category 2>&1).trim() | Where-Object {$_ -ne'Category/Subcategory'}
    $subcategories = ((auditpol /list /subcategory:* 2>&1 | Select-String "^\s+.*$").matches.value).trim()
}
Catch {
    Fail-Json -obj $results -message "Failed to retrive audit policy categories. Please make sure the auditpol command is functional on
    the system and that the account ansible is running under is able to retrieve them. $($_.Exception.Message)"
}

#ansible params
$category = Get-AnsibleParam -obj $params -name "category" -type "str" -ValidateSet $categories
$subcategory = Get-AnsibleParam -obj $params -name "subcategory" -type "str" -ValidateSet $subcategories

########################
### Start Processing ###
########################
Function Get-AuditPolicy ($GetList) {
    Try {
        $auditpolcsv = auditpol $GetList *>&1
        $Obj = ConvertFrom-CSV $auditpolcsv | Select-Object @{n='subcategory';e={$_.Subcategory.ToLower()}},
        #@{n='subcategory_guid';e={$_."Subcategory GUID"}},
        @{n='audit_type';e={$_."Inclusion Setting".ToLower()}}
    }
    Catch {
        Return "$_"
    }

    $HT = @{}
    Foreach ( $Item in $Obj )
    {
        $HT.Add($Item.subcategory,$Item.audit_type)
    }
    $HT
}

#################
### Fail Fast ###
#################

If (-Not $category -and -Not $subcategory) {Fail-Json -obj $results -message "You must provide either a Category or Subcategory parameter"}
If ($category -and $subcategory) {Fail-Json -obj $results -message "Must pick either a specific subcategory or category. You cannot define both"}

#############################################################
### build lists for setting, getting, and comparing rules ###
#############################################################
$GetList = @()
$GetList += '/get','/r'

If ($category) {$GetList += "/category:$category"}
If ($subcategory) {$GetList += "/subcategory:$subcategory"}

$CurrentRule = Get-AuditPolicy $GetList

$results.current_audit_policy = $CurrentRule
Exit-Json -obj $results
