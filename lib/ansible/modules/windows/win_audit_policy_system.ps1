#!powershell
# Copyright (c) 2017 Noah Sparks <nsparks@outlook.com>
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

$ErrorActionPreference = 'Stop'

$params = Parse-Args -arguments $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$results = @{
    changed = $false
    backup_taken = $false
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
$restore_path = Get-AnsibleParam -obj $params -name "restore_path" -type "str"
$backup_path = Get-AnsibleParam -obj $params -name "backup_path" -type "str"
$category = Get-AnsibleParam -obj $params -name "category" -type "str" -ValidateSet $categories
$subcategory = Get-AnsibleParam -obj $params -name "subcategory" -type "str" -ValidateSet $subcategories
$audit_type = Get-AnsibleParam -obj $params -name "audit_type" -type "str" -ValidateSet 'success', 'failure', 'success and failure', 'none'

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

################################
### Deal with parameter sets ###
################################

$supplied_params = $params.GetEnumerator() | Where-Object {$_.key -notlike "_*"}

#do nothing and continue
If ($backup_path -and $restore_path)
{} 
#if restoreis defined by itself, do nothing and continue
ElseIf ($supplied_params.Key -contains 'restore_path' -and $supplied_params.Key.Count -eq 1)
{}
#warn if restore + other non backup_path params
ElseIf ($supplied_params.Key -contains 'restore_path' -and $supplied_params.Key.Count -gt 1)
{
    Add-Warning -obj $results -message "Restore_path is intended to be used as the only parameter when it is supplied. All other parameters will be ignored"
}
#if backup is defined by itself, set flag and continue
ElseIf ($supplied_params.Key -contains 'backup_path' -and $supplied_params.Key.Count -eq 1)
{
    $backup_only = $true
}
#make sure category and subcategory are valid
Else
{
    If (-Not $category -and -Not $subcategory) {Fail-Json -obj $results -message "You must provide either a Category or Subcategory parameter"}
    If ($category -and $subcategory) {Fail-Json -obj $results -message "Must pick either a specific subcategory or category. You cannot define both"}
}

######################
### Backup/Restore ###
######################

#backup and continue (assuming other params are applied)
If ($backup_path)
{
    #If (Test-Path -Path $backup_path)
    #{
        Try {
            If (-not $check_mode) {
                auditpol /backup /file:$backup_path
                $results.backup_taken = $true
            }
        }
        Catch {
            Fail-Json $results "failed to backup audit policy $($_.exception.message)"
        }
    #}
    #Else {Fail-Json $results "invalid backup path, $backup_path"}

    If ($backup_only = $true)
    {
        $results.changed = $true
        Exit-Json -obj $results
    }
}

#restore and exit
If ($restore_path)
{
    If (Test-Path -Path $restore_path)
    {
        Try {
            If (-not $check_mode) {
                auditpol /restore /file:$restore_path
            }
        }
        Catch {
            Fail-Json $results "failed to restore audit policy $($_.exception.message)"
        }
        $results.changed = $true

        Exit-Json -obj $results #exit here if restore works
    }
    Else {Fail-Json $results "invalid restore path, $restore_path"}
}

#############################################################
### build lists for setting, getting, and comparing rules ###
#############################################################
$SetList = @()
$SetList += '/set'
$GetList = @()
$GetList += '/get','/r'

If ($category) {$SetList += "/category:$category"; $GetList += "/category:$category"}
If ($subcategory) {$SetList += "/subcategory:$subcategory"; $GetList += "/subcategory:$subcategory"}

Switch ($audit_type)
{
    'success and failure' {$SetList += "/success:enable","/failure:enable"; $audit_type_check = $audit_type}
    'failure' {$SetList += "/success:disable","/failure:enable"; $audit_type_check = $audit_type}
    'success' {$SetList += "/success:enable","/failure:disable"; $audit_type_check = $audit_type}
    'none' {$SetList += "/success:disable","/failure:disable"; $audit_type_check = 'No Auditing'}
}


#########################
### check Idempotence ###
#########################

$CurrentRule = Get-AuditPolicy $GetList

#do nothing and continue since change is needed
If ( ($CurrentRule.Values | Where-Object {$_ -ne $audit_type_check}) ) {}
#otherwise all items match so we can exit here
Else {Exit-Json -obj $results}

####################
### Apply Change ###
####################

If (-not $check_mode)
{
    Try {
        auditpol $SetList 2>&1
    }
    Catch {
        $results.current_audit_policy = Get-AuditPolicy $GetList
        #$results.auditpol_command = "auditpol $($SetList -join ' ')"
        Fail-Json $results "Failed to set audit policy - $($_.Exception.Message)"
    }
}

$results.changed = $true
#$results.auditpol_command = "auditpol $($SetList -join ' ')"
$results.current_audit_policy = Get-AuditPolicy $GetList
Exit-Json $results
