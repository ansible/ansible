#!powershell
# This file is part of Ansible
#
# Copyright 2016, Red Hat Inc
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# WANT_JSON
# POWERSHELL_COMMON

########


Set-StrictMode -Version Latest

function Get-IniFile {
    param (
        [parameter(mandatory=$true, position=0, valuefrompipelinebypropertyname=$true, valuefrompipeline=$true)][string]$FilePath
    )

        $ini = New-Object System.Collections.Specialized.OrderedDictionary
        $currentSection = New-Object System.Collections.Specialized.OrderedDictionary
        $curSectionName = "default"

        switch -regex (gc $FilePath)
        {
            "^\[(?<Section>.*)\]"
            {
                        $ini.Add($curSectionName, $currentSection)
                        
                        $curSectionName = $Matches['Section'].trim()
                        $currentSection = New-Object System.Collections.Specialized.OrderedDictionary   
            }
                "(?<Key>.*)\=(?<Value>.*)"
                {
                        # add to current section Hash Set
                        $currentSection.Add($Matches['Key'].trim(), $Matches['Value'].trim())
                }
                "^$"
                {
                        # ignore blank line
                }
                default
                {
                        throw "Unidentified: $_"  # should not happen
                }
        }
        if ($ini.Keys -notcontains $curSectionName) { $ini.Add($curSectionName, $currentSection) }
        
        return $ini
}

function Out-IniFile{
    param (
        [parameter(mandatory=$true, position=0, valuefrompipelinebypropertyname=$true, valuefrompipeline=$true)][System.Collections.Specialized.OrderedDictionary]$ini,
                [parameter(mandatory=$false,position=1, valuefrompipelinebypropertyname=$true, valuefrompipeline=$false)][String]$FilePath
    )
        
        $output = ""
        ForEach ($section in $ini.GetEnumerator())
        {
                if ($section.Name -ne "default") 
                { 
                        # insert a blank line after a section
                        $sep = @{$true="";$false="`r`n"}[[String]::IsNullOrWhiteSpace($output)]
                        $output += "$sep[$($section.Name)]`r`n" 
                }
                ForEach ($entry in $section.Value.GetEnumerator())
                {
                        $sep = @{$true="";$false="="}[$entry.Name -eq ";"]
                        $output += "$($entry.Name)$sep$($entry.Value)`r`n"
                }
                
        }
        
        $output = $output.TrimEnd("`r`n")
        if ([String]::IsNullOrEmpty($FilePath))
        {
                return $output
        }
        else
        {
                $output | Out-File -FilePath $FilePath -Encoding:ASCII
        }
}

$params = Parse-Args $args;

$result = New-Object psobject @{
    changed = $false
};

$category = Get-Attr $params "category" -failifempty $true
$key = Get-Attr $params "key" -failifempty $true
$value = Get-Attr $params "value" -failifempty $true
$sepath = "$home\sec_edit_dump.inf"

If ((Get-WmiObject Win32_ComputerSystem).PartOfDomain) {
    Fail-Json $result "This host is joined to a Domain Controller, you'll need to modify GPO directly instead of secedit"
}

SecEdit.exe /export /cfg $sepath /quiet

$ini = Get-IniFile -FilePath $sepath

Try {
    $current_value = $ini.$category.$key
}
Catch {
    If ($_.Exception.Message -like "*$category cannot be found*"){
        $valid_categories = $ini.GETENUMERATOR() | % { $_.key + ',' } 
        Fail-Json $result "The category you specified, $category, is not valid. Valid categories for this system are $valid_categories."
    }
    ElseIf ($_.Exception.Message -like "*$key*"){
        $valid_keys = $ini.$category.GETENUMERATOR() | % { $_.key + ',' } 
        Fail-Json $result "The key you specified, $key, is not valid. Valid keys for the category '$category' are: $valid_keys."
    }
    Else {
        Fail-Json $result $_.Exception.Message
    }
}

If ($current_value -eq $value) {
    $result.msg = "Key Already Set"
    $result.category = $category
    $result.key = $key
    $result.value = $value
}
Else {
    $ini.$category.$key = $value
    $ini | Out-IniFile -FilePath "$home\updated_inf"
    SecEdit.exe /configure /db "$home\temp_db.sdb" /cfg "$home\updated_inf" /quiet 
    $result.changed = $true
    $result.msg = "Key updated"
    $result.category = $category
    $result.key = $key
    $result.value = $value
}

# Secedit doesnt error out when you try to configure it with bad values, even with /validate.
# The secedit behavior is to simply ignore invalid values and proceed anyways
# Here we are re exporting secedit to deterimine if the value 'stuck'
# If it is updated, then we're good to go. If it wasn't updated then we know
# that the supplied value was improper

SecEdit.exe /export /cfg $sepath /quiet

$updated_ini = Get-IniFile -FilePath $sepath

Try {
    $updated_value = $updated_ini.$category.$key
    If ($updated_value -ne $value){
        Fail-Json $result "The value you supplied '$value' was not accepted by SecEdit. Ensure it is a valid value and try again. The original value of '$current_value' has been kept in tact" 
    }
}
Catch [System.Management.Automation.PropertyNotFoundException] {
    # Keys are removed if value was empty or whitespace. Expected behavior.
    # Rethrow exception if value wasn't empty or whitespace.
    If (![String]::IsNullOrWhiteSpace($value)) {
        throw
    }
}

rm $home\updated_inf 
rm $home\temp_db.sdb 
rm $home\sec_edit_dump.inf

Exit-Json $result
