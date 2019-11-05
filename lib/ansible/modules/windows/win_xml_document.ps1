#!powershell

# Copyright: (c) 2019, Micah Hunsberger (@mhunsber)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.Backup

Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'

function Get-IndexOfElement($XmlElement)
{
    $parentNode = $XmlElement.ParentNode
    if ($parentNode -is [xml])
    {
        return 1 # document node is index 1
    }
    [System.Xml.XmlElement]$parent = [System.Xml.XmlElement]$parentNode
    $index = 1
    foreach($candidate in $parent.ChildNodes)
    {
        if(($candidate -is [System.Xml.XmlElement]) -and ($candidate.Name -eq $XmlElement.Name))
        {
            if ($candidate -eq $XmlElement)
            {
                return $index
            }
            $index++
        }
    }
    throw "Element not found within parent!"
}

function Get-NodeXPath($XmlNode)
{
    # follow parent objects to the owner document
    $sb = New-Object -TypeName System.Text.StringBuilder
    while ($null -ne $XmlNode)
    {
        switch($XmlNode.NodeType)
        {
            'Attribute' {
                $sb.Insert(0, "/@$($XmlNode.Name)") | Out-Null
                $XmlNode = $XmlNode.OwnerElement
                break
            }
            'Element' {
                $index = Get-IndexOfElement -XmlElement $XmlNode
                $sb.Insert(0, "/$($XmlNode.Name)[$index]") | Out-Null
                $XmlNode = $XmlNode.ParentNode
            }
            'Document' {
                return $sb.ToString()
            }
            default {
                throw "Node Type <$($XmlNode.NodeType)> is unsupported!"
            }
        }
    }
    throw "Xml was not a member of a parent document!"
}

function Get-Namespace([string]$elementname, [string]$Default = '')
{
    if ($elementname.Contains(':'))
    {
        $prefix = $elementname.Split(':')[0]
        if ($namespace_manager.HasNamespace($prefix))
        {
            return $namespace_manager.LookupNamespace($prefix)
        }
        else
        {
            $module.FailJson("Unknown namespace prefix $prefix for element $elementname!")
        }
    }
    return $Default
}

function Get-XMLTextWriter($OutputStream)
{
    $encoding = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false # no BOM
    $xmlTextWriter = New-Object -TypeName System.Xml.XmlTextWriter -ArgumentList $OutputStream, $encoding
    if ($indent)
    {
        $xmlTextWriter.Formatting = [System.Xml.Formatting]::Indented
        $xmlTextWriter.Indentation = $indent_spaces
    }
    else
    {
        $xmlTextWriter.Formatting = [System.Xml.Formatting]::None
    }
    return $xmlTextWriter
}

function Save-XMLDocument([bool]$Backup = $false, [switch]$AsString)
{
    if ($Backup)
    {
        $backup_file =  Backup-File -path $xml_file
    }
    if ($AsString)
    {
        $ms = New-Object -TypeName System.IO.MemoryStream
        $writer = Get-XMLTextWriter -OutputStream $ms
    }
    else
    {
        $writer = Get-XMLTextWriter -OutputStream $xml_file
    }
    try
    {
        $xml_doc.Save($writer)
        # Add carriage return/line feed at the end to keep git happy
        $writer.WriteWhitespace("`r`n")
    }
    finally
    {
        $writer.Close()
    }
    if ($AsString)
    {
        return [System.Text.Encoding]::UTF8.GetString($ms.ToArray())
    }
    elseif ($Backup)
    {
        return $backup_file
    }
}

function Get-XPathNodeType([string]$NodeSelector)
{
    if ($NodeSelector.EndsWith('text()'))
    {
        return [System.Xml.XmlNodeType]::Text
    }
    if ($NodeSelector.EndsWith('comment()'))
    {
        return [System.Xml.XmlNodeType]::Comment
    }
    if ($NodeSelector.Trim('/').StartsWith('@'))
    {
        return [System.Xml.XmlNodeType]::Attribute
    }
    else
    {
        return [System.Xml.XmlNodeType]::Element
    }
}

function Get-XPathPredicateTokens([string]$Predicate)
{
    function Get-TokenType ([string]$Value)
    {
        if ($Value.StartsWith('@'))
        {
            return 'attribute'
        }
        elseif ($Value.StartsWith('"') -or $Value.StartsWith("'"))
        {
            return 'string'
        }
        elseif ($Value -eq 'text()')
        {
            return 'text'
        }
        elseif ($Value.EndsWith(')'))
        {
            return 'function'
        }
        elseif ('and', 'or' -contains $Value)
        {
            return 'control'
        }
        elseif ($value -eq '=')
        {
            return 'equality'
        }
        elseif ('<', '>', '<=', '>=' -contains $Value)
        {
            return 'inequality'
        }
        elseif ([double]::TryParse($Value, [ref]$null))
        {
            return 'number'
        }
        else
        {
            throw "cannot determine token type for token ($Value)!"
            return $null
        }
    }
    function Add-Token ($Token)
    {
        $Token.value = ([string]($Token.value)).Trim()
        if ($Token.type -eq '')
        {
            $Token.type = Get-TokenType -Value $Token.value
        }
        if ($Token.type -eq 'string')
        {
            if ($Token.value.StartsWith('"'))
            {
                $token.value = $Token.value.Trim('"')
            }
            elseif ($Token.value.StartsWith("'"))
            {
                $token.value = $Token.value.Trim("'")
            }
        }
        elseif ($Token.type -eq 'attribute')
        {
            $Token.value = $Token.Value.Trim('@')
        }
        $tokens.Add($Token) | Out-Null
    }
    function Get-NewToken
    {
        return @{
            value = ''
            type = ''
        }
    }
    $tokens = New-Object -TypeName System.Collections.ArrayList
    $lastQuote = ''
    $token = Get-NewToken
    for($i = 0; $i -lt $Predicate.Length; $i++)
    {
        $char = $Predicate[$i]
        if ($char -eq $lastQuote) # end of string
        {
            $lastQuote = ''
            $token.value += $char
            $token.type = 'string'
            Add-Token -Token $token
            $token = Get-NewToken
        }
        elseif ($lastQuote -ne '') # in a quoted value
        {
            $token.value += $char
        }
        elseif ($char -eq "'" -or $char -eq '"') # start a quoted value
        {
            $lastQuote = $char
            $token.value = $char
            $token.type = 'string'
        }
        elseif ('=', '>', '<' -contains $char) # comparison
        {
            Add-Token -Token $token
            $token = Get-NewToken
            $comparer = $char
            $type = 'equality'
            if ('>', '<' -contains $char)
            {
                $type = 'inequality'
                # need to check the next one (would be invalid predicate if no next character)
                if ($Predicate[$i + 1] -eq '=')
                {
                    $comparer += '='
                    $i++ # already tokenized it
                }
            }
            Add-Token -Token @{type=$type; value=$comparer}
            $token = Get-NewToken
        }
        elseif ($char -eq ' ' -and $token.value -ne '')
        {
            Add-Token -Token $token
            $token = Get-NewToken
        }
        else
        {
            $token.value += $char
        }
    }
    if ($token.value -ne '')
    {
        Add-Token -Token $token
    }
    return $tokens
}

function Get-XPathPredicateValues([string]$Predicate)
{
    $tokens = Get-XPathPredicateTokens -Predicate $Predicate
    $attributes = @()
    $text = @{
        action = 'none'
        value = ''
    }

    for($i = 0; $i -lt $tokens.Length; $i++)
    {
        if ($i -eq $tokens.Length - 1)
        {
            $nextToken = @{ type=''; value=''}
        }
        else
        {
            $nextToken = $tokens[$i + 1]
        }
        $token = $tokens[$i]
        switch($token.type)
        {
            'text' {
                if($nextToken.type -eq 'equality')
                {
                    $text.action = 'set'
                    $text.value = $tokens[$i + 2].value # it better be there
                    $i = $i + 2 # skip them because we've used them
                }
                else
                {
                    $text.action = 'present'
                }
                break;
            }
            'attribute' {
                $attr = @{
                    action = 'present'
                    name = $token.value
                    value = ''
                }
                if($nextToken.type -eq 'equality')
                {
                    $attr.action = 'set'
                    $attr.value = $tokens[$i + 2].value # it better be there
                    $i = $i + 2 # skip them because we've used them
                }
                $attributes += $attr
                break;
            }
            'control' {
                if ($token.value -eq 'or')
                {
                    $module.FailJson("Cannot create nonexistent node from predicate [$Predicate] because it contains an OR control value!")
                }
                break;
            }
            'inequality' {
                $module.FailJson("Cannot create nonexistent node from predicate [$Predicate] because it contains an inequality!")
                break;
            }
            'function' {
                throw "dont know what to do with predicate function $($token.value)!"
            }
            'equality' {
                throw "something is wrong, encountered equality operator when this should have been skipped."
                break;
            }
            'number' {
                # if we have gotten here and it is a number, it must be a positional argument
                # so we can ingore it because it means the element doesn't exist at that position
                # which either means there are no elements (create it) or none at that position (add it to the end)
                break;
            }
            'string' {
                # also don't know how we got here
                throw "something is wrong, encounted string token when this shold have been skipped."
                break;
            }
        }
    }
    return @{
        attributes = $attributes
        text = $text
    }
}

function Split-XPath([string]$XPath)
{
    $info = @{
        parentPath = ''
        childPath = ''
        childName = ''
        namespace = ''
        childType = ''
        conditions = @{}
    }
    $pivot = $XPath.LastIndexOf('/')
    if ($pivot -lt 0)
    {
        $info.childPath = $Xpath
    }
    elseif ($pivot -eq $Xpath.Length - 1)
    {
        $info.parentPath = $Xpath
    }
    else
    {
        $info.parentPath = $XPath.Substring(0, $pivot)
        $info.childPath = $XPath.Substring($pivot + 1)
    }
    $info.childType = Get-XPathNodeType -NodeSelector $info.childPath
    switch($info.childType)
    {
        'Text' {
            break;
        }
        'Comment' {
            break;
        }
        'Attribute' {
            $info.childName = $info.childPath.Substring(1)
            break;
        }
        'Element' {
            $info.childName = $info.childPath
            break;
        }
    }
    # are there any conditions?
    if($info.childPath.Contains('[') -and $info.childPath.Contains(']'))
    {
        $predicateStart = $info.childPath.IndexOf('[')
        $predicateEnd = $info.childPath.LastIndexOf(']')
        $predicateString = $info.childPath.Substring($predicateStart + 1, $predicateEnd - $predicateStart - 1)
        $info.conditions = Get-XPathPredicateValues -Predicate $predicateString
        $info.childName = $info.childName.Substring(0, $predicateStart)
    }
    $info.namespace = Get-Namespace -elementname $info.childName
    return $info
}

function Exit-Module
{
    if ($module.DiffMode)
    {
        $module.Diff.after = Save-XMLDocument -AsString
    }
    if ($xml_string)
    {
        $module.Result.xmlstring = Save-XMLDocument -AsString
    }
    elseif (-not $module.CheckMode -and $module.Result.changed)
    {
        $backup_file = Save-XMLDocument -Backup $backup
        if ($backup)
        {
            $module.Result.backup_file = $backup_file
        }
    }
    $module.ExitJson()
}
function Set-NodeValues($NodeList, [string]$Value)
{
    foreach($node in $NodeList)
    {
        if ('Attribute', 'Text', 'Comment' -contains $node.NodeType)
        {
            if ($node.Value -ne $Value)
            {
                $module.Result.changed = $true
                $node.Value = $Value
            }
        }
        else
        {
            # assume we want to set value as a text node for the element
            $current_text = Get-ElementText -XmlElement $node
            if ($current_text -ne $Value)
            {
                # remove text nodes
                $module.Result.changed = $true
                $textNodes = $node.ChildNodes | Where-Object { $_.NodeType -eq 'Text' }
                foreach ($textNode in $textNodes)
                {
                    $node.RemoveChild($textNode) | Out-Null
                }
                if ($Value -ne '')
                {
                    # add it back
                    $node.AppendChild($xml_doc.CreateTextNode($Value)) | Out-Null
                }
            }
        }
    }
}

function Add-NodeAtXPath($Document, [string]$XPath)
{
    $matches = $Document.SelectNodes($XPath, $namespace_manager)
    if ($matches.Count -gt 0)
    {
        return $matches
    }
    $xpath_parts = Split-XPath -XPath $XPath
    if ($xpath_parts.parentPath.EndsWith('/'))
    {
        # there is a double-slash preceding the element we wish to create.
        # This is unsupported because we cannot know at what depth to create the element.
        $module.FailJson("cannot create element(s) at $XPath because a descendent path was used instead of a child.")
    }
    if ($xpath_parts.childPath.Contains('::'))
    {
        # cannot create elements based on Axes
        $module.FailJson("cannot create element(s) at $XPath because an axis was used at a non-existent path.")
    }

    $parent_nodes = Add-NodeAtXPath -Document $Document -XPath $xpath_parts.parentPath
    $nodes = @()
    # since it didn't match before, we can blindly add now
    foreach($node in $parent_nodes)
    {
        $module.Result.changed = $true
        switch ($xpath_parts.childType)
        {
            'Text' {
                $nodes += $node.AppendChild($Document.CreateTextNode(''))
                break
            }
            'Comment' {
                $nodes += $node.AppendChild($Document.CreateComment(''))
                break
            }
            'Attribute' {
                # attributes are not subject to the default namespace
                $nodes += $node.Attributes.Append($Document.CreateAttribute($xpath_parts.childName, $xpath_parts.namespace))
                break
            }
            'Element' {
                if($xpath_parts.namespace -ne '')
                {
                    $element = $Document.CreateElement($xpath_parts.childName, $xpath_parts.namespace)
                }
                else
                {
                    $element = $Document.CreateElement($xpath_parts.childName, $node.NamespaceURI)
                }
                if ($xpath_parts.conditions.Count -gt 0)
                {
                    if ($xpath_parts.conditions.text.action -ne 'none')
                    {
                        $element.AppendChild($Document.CreateTextNode($xpath_parts.conditions.text.value)) | Out-Null
                    }
                    foreach($attribute in $xpath_parts.conditions.attributes)
                    {
                        $attributeNode = $Document.CreateAttribute($attribute.name, $xpath_parts.namespace)
                        if($attribute.action -eq 'set')
                        {
                            $attributeNode.Value = $attribute.value
                        }
                        $element.Attributes.Append($attributeNode) | Out-Null
                    }
                }
                $nodes += $node.AppendChild($element)
                break
            }
            default {
                throw "impossible error!"
            }
        }
    }
    return $nodes
}

function Get-ElementAttributes($XmlElement)
{
    $attrs = @{}
    foreach($attr in $XmlElement.Attributes)
    {
        $key = $attr.Name
        $attrs.$key = $attr.Value
    }
    return $attrs
}

function Get-ElementText($XmlElement)
{
    $text = ''
    # cannot directly query '#text' directly in PowerShell strict mode
    if ($XmlElement.PSObject.Properties.Name -contains '#text')
    {
        $text = $XmlElement.'#text'
    }
    return $text
}

function ConvertTo-Node($document, $child, $defaultNamespace)
{
    if ($child -is [string])
    {
        return $document.CreateElement($child, (Get-Namespace -elementname $child -Default $defaultNamespace))
    }
    elseif ($child -is [hashtable])
    {
        if ($child.Count -gt 1)
        {
            $module.FailJson("Cannot create children from hashes with more than one key")
        }
        foreach($prop in $child.GetEnumerator())
        {
            $element = $document.CreateElement($prop.Name, (Get-Namespace -elementname $prop.Name -Default $defaultNamespace))
            if ($prop.Value -is [string])
            {
                $element.InnerText = $prop.Value
            }
            elseif ($prop.Value -is [hashtable])
            {
                foreach($item in $prop.Value.GetEnumerator())
                {
                    if ($item.Value -is [string])
                    {
                        # attributes are not subject to the default namespace
                        $attributeNode = $document.CreateAttribute($item.Name, (Get-Namespace -elementname $item.Name))
                        $attributeNode.Value = $item.Value
                        $element.Attributes.Append($attributeNode) | Out-Null
                    }
                    elseif ($item.Value -is [array])
                    {
                        foreach($newChild in $item.Value)
                        {
                            $element.AppendChild((ConvertTo-Node -document $document -child $newChild -defaultNamespace $element.NamespaceURI)) | Out-Null
                        }
                    }
                }
            }
            return $element
        }
    }
    else
    {
        $module.FailJson("Invalid child type of $($child.GetType()). Children must be strings or hashes")
    }
}

function ConvertTo-NodeList($document, $children, $defaultNamespace = '')
{
    if ($null -eq $children)
    {
        return @()
    }

    return @($children | Foreach-Object { ConvertTo-Node -document $document -child $_ -defaultNamespace $defaultNamespace})
}

function Test-NodeEqual($A, $B)
{
    if ($A.NodeType -ne $B.NodeType) { return $false }
    if ($A.Name -ne $B.Name) { return $false }
    if ($A.OuterXml -ne $B.OuterXML) { return $false }
    return $true
}

function Add-NodeChildren($Node, $Children)
{
    foreach($child in $Children)
    {
        $Node.AppendChild($child) | out-null
        $module.Result.changed = $true
    }
}
function Set-NodeChildren($Node, $Children)
{
    $replace = $false
    if ($Node.ChildNodes.Count -eq $Children.Count)
    {
        for($i = 0; $i -lt $Node.ChildNodes.Count; $i++)
        {
            $child_node = $Node.ChildNodes[$i]
            $child_to_set = $Children[$i]
            if (-not (Test-NodeEqual -A $child_node -B $child_to_set))
            {
                $replace = $true
                break
            }
        }
    }
    else
    {
        $replace = $true
    }
    if ($replace)
    {
        $child = $node.FirstChild
        while($null -ne $child)
        {
            $Node.RemoveChild($child) | Out-Null
            $child = $node.FirstChild
        }
        foreach($child in $Children)
        {
            $Node.AppendChild($child) | Out-Null
        }
        $module.Result.changed = $true
    }
}

$spec = @{
    options = @{
        path = @{ type='path'; aliases=@('dest','file') }
        xmlstring = @{ type='str' }
        xpath = @{ type='str' }
        state = @{ type='str'; default='present'; choices=@('absent', 'present'); aliases=@('ensure') }
        value = @{ type='str' }
        add_children = @{ type='list' }
        set_children = @{ type= 'list' }
        count = @{ type='bool'; default = $false }
        print_match = @{ type = 'bool'; default = $false }
        indent = @{ type = 'bool'; default = $true }
        indent_spaces = @{ type = 'int'; default = 2 }
        content = @{ type= 'str'; choices=@('attribute','text') }
        backup = @{ type='bool'; default = $false }
        insertbefore = @{ type='bool'; default=$false }
        insertafter = @{ type='bool'; default=$false }
        namespaces = @{ type = 'dict'; default = @{} }
    }
    required_by = @{
        add_children='xpath'
        content='xpath'
        set_children='xpath'
        value='xpath'
    }
    required_if = @(
        @('count', $true, @('xpath')),
        @('print_match', $true, @('xpath')),
        @('insertbefore', $true, @('xpath')),
        @('insertafter', $true, @('xpath'))
    )
    required_one_of = @(
        @('path', 'xmlstring'),
        @('add_children','content','count','print_match','set_children','value')
    )
    mutually_exclusive = @(
        @('add_children','content','count','print_match','set_children','value'),
        @('path','xmlstring'),
        @('insertbefore','insertafter')
    )
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$xml_file = $module.Params.path
$xml_string = $module.Params.xmlstring
$xpath = $module.Params.xpath
$state = $module.Params.state
$value = $module.Params.value
$set_children = $module.Params.set_children
$add_children = $module.Params.add_children
$indent = $module.Params.indent
$indent_spaces = $module.Params.indent_spaces
$content = $module.Params.content
$print_match = $module.Params.print_match
$count = $module.Params.count
$backup = $module.Params.backup
$insertbefore = $module.Params.insertbefore
$insertafter = $module.Params.insertafter
$namespaces = $module.Params.namespaces

# check if the file exists
if ($null -eq $xml_string -and -not (Test-Path -Path $xml_file -PathType Leaf))
{
    $module.FailJson("The target xml source $xml_file does not exist.")
}

# load the xml document
$xml_doc = New-Object -TypeName System.Xml.XmlDocument
$xml_doc.XmlResolver = $null
if($xml_string)
{
    $xml_doc.LoadXml($xml_string)
}
elseif (Test-Path -LiteralPath $xml_file -PathType Leaf)
{
    $xml_doc.Load($xml_file)
}

$namespace_manager = New-Object -TypeName System.Xml.XmlNamespaceManager -ArgumentList $xml_doc.NameTable
$namespace = $xml_doc.DocumentElement.NamespaceURI
$local_name = $xml_doc.DocumentElement.LocalName
$namespace_manager.AddNamespace($xml_doc.$local_name.SchemaInfo.Prefix, $namespace)
foreach($ns in $namespaces.GetEnumerator())
{
    $namespace_manager.AddNamespace($ns.Key, $ns.Value)
}

# validate xpath expression and get matches
if ($null -ne $xpath)
{
    try
    {
        $xpath_expression = [System.Xml.XPath.XPathExpression]::Compile($xpath)
        if ($xpath_expression.ReturnType -ne 'NodeSet')
        {
            $module.FailJson("provided xpath expression must return a NodeSet, not $($xpath_expression.ReturnType)!")
        }
        $matched_nodes = $xml_doc.SelectNodes($xpath, $namespace_manager)
    }
    catch [System.Xml.XPath.XPathException]
    {
        $module.FailJson("Provided xpath expression failed to compile: $($_.Exception.Message)")
    }
}

$module.Result.actions = @{
    actions = @{
        xpath = $xpath
        namespaces = $namespace_manager -as [string[]]
        $state = $state
    }
}
$module.Result.changed = $false

if ($module.DiffMode)
{
    $module.Diff.before = Save-XMLDocument -AsString
}

if ($print_match)
{
    $module.Result.matches = @($matched_nodes | ForEach-Object { Get-NodeXPath -XmlNode $_ })
    Exit-Module
}

if ($count)
{
    $module.Result.count = $matched_nodes.Count
    Exit-Module
}

if ($content -eq 'attribute')
{
    if ($matched_nodes.Count -eq 0)
    {
        $module.FailJson("xpath $xpath does not match any nodes!")
    }
    $module.Result.matches = @($matched_nodes | ForEach-Object { @{ $_.Name = (Get-ElementAttributes -Xml $_) } })
    Exit-Module
}
elseif ($content -eq 'text')
{
    if ($matched_nodes.Count -eq 0)
    {
        $module.FailJson("xpath $xpath does not match any nodes!")
    }
    $module.Result.matches = @($matched_nodes | ForEach-Object { @{ $_.Name = (Get-ElementText -Xml $_) } })
    Exit-Module
}

if ($state -eq 'absent')
{
    foreach($node in $matched_nodes)
    {
        if ($node.NodeType -eq 'Attribute')
        {
            $node.OwnerElement.RemoveAttributeNode($node) | Out-Null
        }
        else
        {
            $node.get_parentNode().RemoveChild($node) | Out-Null
        }
        $module.Result.changed = $true
    }

    Exit-Module
}
else # state -eq 'present'
{
    if ($set_children)
    {
        if ($matched_nodes.Count -eq 0)
        {
            $module.FailJson("xpath $xpath does not match any nodes!")
        }
        # if it is a namespaced search, all matched nodes should be of the same namespace
        $parent_namespace = $matched_nodes[0].NamespaceURI
        $children = ConvertTo-NodeList -document $xml_doc -children $set_children -defaultNamespace $parent_namespace

        foreach($node in $matched_nodes)
        {
            Set-NodeChildren -Node $node -Children $children
        }

        Exit-Module
    }

    if ($add_children)
    {
        if ($matched_nodes.Count -eq 0)
        {
            $module.FailJson("xpath $xpath does not match any nodes!")
        }
        # if it is a namespaced search, all matched nodes should be of the same namespace
        $parent_namespace = $matched_nodes[0].NamespaceURI
        $children = ConvertTo-NodeList -document $xml_doc -children $add_children -defaultNamespace $parent_namespace

        if ($insertBefore)
        {
            $node = $matched_nodes[0]
            foreach($child in $children)
            {
                $module.Result.changed = $true
                $node.ParentNode.InsertBefore($child, $node) | Out-Null
            }
        }
        elseif ($insertafter)
        {
            $node = $matched_nodes[$matched_nodes.Count - 1]
            foreach($child in $children)
            {
                $module.Result.changed = $true
                $node = $node.ParentNode.InsertAfter($child, $node)
            }
        }
        else
        {
            foreach($node in $matched_nodes)
            {
                Add-NodeChildren -Node $node -Children $children
            }
        }

        Exit-Module
    }

    if ($null -ne $xpath)
    {
        $nodes_to_set = Add-NodeAtXPath -Document $xml_doc -XPath $xpath
        # if value is None we are done because the nodes are present
        if ($null -ne $value)
        {
            Set-NodeValues -NodeList $nodes_to_set -Value $value
        }

        Exit-Module
    }

    # must just want to reformat the document?
    if ($xml_string)
    {
        $before = $xml_string
    }
    else
    {
        $before = [System.IO.File]::ReadAllText($xml_file)
    }
    if ($module.DiffMode)
    {
        # we should show the difference in formatting
        $module.Diff.before = $before
    }
    $now = Save-XMLDocument -AsString
    if ($before -ne $now)
    {
        $module.Result.changed = $true
    }

    Exit-Module
}
