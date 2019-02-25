#!powershell

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy
#Requires -Module Ansible.ModuleUtils.Backup

Set-StrictMode -Version 2

function Copy-Xml($dest, $src, $xmlorig) {
    if ($src.get_NodeType() -eq "Text") {
        $dest.set_InnerText($src.get_InnerText())
    }

    if ($src.get_HasAttributes()) {
        foreach ($attr in $src.get_Attributes()) {
            $dest.SetAttribute($attr.get_Name(), $attr.get_Value())
        }
    }

    if ($src.get_HasChildNodes()) {
        foreach ($childnode in $src.get_ChildNodes()) {
            if ($childnode.get_NodeType() -eq "Element") {
                $newnode = $xmlorig.CreateElement($childnode.get_Name(), $xmlorig.get_DocumentElement().get_NamespaceURI())
                Copy-Xml $newnode $childnode $xmlorig
                $dest.AppendChild($newnode) | Out-Null
            } elseif ($childnode.get_NodeType() -eq "Text") {
                $dest.set_InnerText($childnode.get_InnerText())
            }
        }
    }
}

function Compare-XmlDocs($actual, $expected) {
    if ($actual.get_Name() -ne $expected.get_Name()) {
        throw "Actual name not same as expected: actual=" + $actual.get_Name() + ", expected=" + $expected.get_Name()
    }
    ##attributes...

    if (($actual.get_NodeType() -eq "Element") -and ($expected.get_NodeType() -eq "Element")) {
        if ($actual.get_HasAttributes() -and $expected.get_HasAttributes()) {
            if ($actual.get_Attributes().Count -ne $expected.get_Attributes().Count) {
                throw "attribute mismatch for actual=" + $actual.get_Name()
            }
            for ($i=0;$i -lt $expected.get_Attributes().Count; $i =$i+1) {
                if ($expected.get_Attributes()[$i].get_Name() -ne $actual.get_Attributes()[$i].get_Name()) {
                    throw "attribute name mismatch for actual=" + $actual.get_Name()
                }
                if ($expected.get_Attributes()[$i].get_Value() -ne $actual.get_Attributes()[$i].get_Value()) {
                    throw "attribute value mismatch for actual=" + $actual.get_Name()
                }
            }
        }

        if (($actual.get_HasAttributes() -and !$expected.get_HasAttributes()) -or (!$actual.get_HasAttributes() -and $expected.get_HasAttributes())) {
            throw "attribute presence mismatch for actual=" + $actual.get_Name()
        }
    }

    ##children
    if ($expected.get_ChildNodes().Count -ne $actual.get_ChildNodes().Count)  {
        throw "child node mismatch. for actual=" + $actual.get_Name()
    }

    for ($i=0;$i -lt $expected.get_ChildNodes().Count; $i =$i+1) {
        if (-not $actual.get_ChildNodes()[$i]) {
            throw "actual missing child nodes. for actual=" + $actual.get_Name()
        }
        Compare-XmlDocs $expected.get_ChildNodes()[$i] $actual.get_ChildNodes()[$i]
    }

    if ($expected.get_InnerText()) {
        if ($expected.get_InnerText() -ne $actual.get_InnerText()) {
           throw "inner text mismatch for actual=" + $actual.get_Name()
        }
    }
    elseif ($actual.get_InnerText()) {
        throw "actual has inner text but expected does not for actual=" + $actual.get_Name()
    }
}

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name "_ansible_check_mode" -type "bool" -default $false

$debug_level = Get-AnsibleParam -obj $params -name "_ansible_verbosity" -type "int"
$debug = $debug_level -gt 2

$dest = Get-AnsibleParam $params "path" -type "path" -FailIfEmpty $true -aliases "dest", "file"
$fragment = Get-AnsibleParam $params "fragment" -type "str" -FailIfEmpty $true -aliases "xmlstring"
$xpath = Get-AnsibleParam $params "xpath" -type "str" -FailIfEmpty $true
$backup = Get-AnsibleParam $params "backup" -type "bool" -default $false
$type = Get-AnsibleParam $params "type" -type "str" -Default "element" -ValidateSet "element", "attribute", "text"
$attribute = Get-AnsibleParam $params "attribute" -type "str" -FailIfEmpty ($type -eq "attribute")
$state = Get-AnsibleParam $params "state" -type "str" -Default "present"

$result = @{
    changed = $false
}

If (-Not (Test-Path -Path $dest -PathType Leaf)){
    Fail-Json $result "Specified path $dest does not exist or is not a file."
}

$xmlorig = New-Object -TypeName System.Xml.XmlDocument
$xmlorig.XmlResolver = $null
Try {
    $xmlorig.Load($dest)
}
Catch {
    Fail-Json $result "Failed to parse file at '$dest' as an XML document: $($_.Exception.Message)"
}

$namespaceMgr = New-Object System.Xml.XmlNamespaceManager $xmlorig.NameTable
$namespace = $xmlorig.DocumentElement.NamespaceURI
$localname = $xmlorig.DocumentElement.LocalName

$namespaceMgr.AddNamespace($xmlorig.$localname.SchemaInfo.Prefix, $namespace)

if ($type -eq "element") {
    $xmlchild = $null
    Try {
        $xmlchild = [xml]$fragment
    } Catch {
        Fail-Json $result "Failed to parse fragment as XML: $($_.Exception.Message)"
    }

    $child = $xmlorig.CreateElement($xmlchild.get_DocumentElement().get_Name(), $xmlorig.get_DocumentElement().get_NamespaceURI())
    Copy-Xml $child $xmlchild.DocumentElement $xmlorig

    $node = $xmlorig.SelectSingleNode($xpath, $namespaceMgr)
    if ($node.get_NodeType() -eq "Document") {
        $node = $node.get_DocumentElement()
    }
    $elements = $node.get_ChildNodes()
    [bool]$present = $false
    [bool]$changed = $false
    if ($elements.get_Count()) {
        if ($debug) {
            $err = @()
            $result.err = {$err}.Invoke()
        }
        foreach ($element in $elements) {
            try {
                Compare-XmlDocs $child $element
                $present = $true
                break
            } catch {
                if ($debug) {
                    $result.err.Add($_.Exception.ToString())
                }
            }
        }
        if (!$present -and ($state -eq "present")) {
            [void]$node.AppendChild($child)
            $result.msg = "xml added"
            $changed = $true
        } elseif ($present -and ($state -eq "absent")) {
            [void]$node.RemoveChild($element)
            $result.msg = "xml removed"
            $changed = $true
        }
    } else {
        if ($state -eq "present") {
            [void]$node.AppendChild($child)
            $result.msg = "xml added"
            $changed = $true
        }
    }

    if ($changed) {
        if ($backup) {
            $result.backup_file = Backup-File -path $dest -WhatIf:$check_mode
            # Ensure backward compatibility (deprecate in future)
            $result.backup = $result.backup_file
        }
        if (-not $check_mode) {
            $xmlorig.Save($dest)
        }
        $result.changed = $true
    } else {
        $result.msg = "not changed"
    }
} elseif ($type -eq "text") {
    $node = $xmlorig.SelectSingleNode($xpath, $namespaceMgr)
    [bool]$add = ($node.get_InnerText() -ne $fragment)
    if ($add) {
        if ($backup) {
            $result.backup_file = Backup-File -path $dest -WhatIf:$check_mode
            # Ensure backward compatibility (deprecate in future)
            $result.backup = $result.backup_file
        }
        $node.set_InnerText($fragment)
        if (-not $check_mode) {
            $xmlorig.Save($dest)
        }
        $result.changed = $true
        $result.msg = "text changed"
    } else {
        $result.msg = "not changed"
    }
} elseif ($type -eq "attribute") {
    $node = $xmlorig.SelectSingleNode($xpath, $namespaceMgr)
    [bool]$add = !$node.HasAttribute($attribute) -Or ($node.$attribute -ne $fragment)
    if ($add -And ($state -eq "present")) {
        if ($backup) {
            $result.backup_file = Backup-File -path $dest -WhatIf:$check_mode
            # Ensure backward compatibility (deprecate in future)
            $result.backup = $result.backup_file
        }
        if (!$node.HasAttribute($attribute)) {
            $node.SetAttributeNode($attribute, $xmlorig.get_DocumentElement().get_NamespaceURI())
        }
        $node.SetAttribute($attribute, $fragment)
        if (-not $check_mode) {
            $xmlorig.Save($dest)
        }
        $result.changed = $true
        $result.msg = "text changed"
    } elseif (!$add -And ($state -eq "absent")) {
        if ($backup) {
            $result.backup_file = Backup-File -path $dest -WhatIf:$check_mode
            # Ensure backward compatibility (deprecate in future)
            $result.backup = $result.backup_file
        }
        $node.RemoveAttribute($attribute)
        if (-not $check_mode) {
            $xmlorig.Save($dest)
        }
        $result.changed = $true
        $result.msg = "text changed"
    } else {
        $result.msg = "not changed"
    }
}

Exit-Json $result
