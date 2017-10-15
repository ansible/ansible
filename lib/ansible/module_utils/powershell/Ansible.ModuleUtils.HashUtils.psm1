# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

Function Convert-HashToString
{
    <#
    Convert a hash into a variable length string of KEY=VALUE seperated by spaces

    Input:
    {
        key1: value1,
        key2: value2
    }

    Output:
    "key1=value1 key2=value2"
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$hash
    )

    return ($hash.GetEnumerator() | % { "$($_.Key)=$($_.Value)" }) -join " "
}

Function Convert-ArrayToHash
{
    <#
    Converts an array with key=value elements into a hashtable

    Input:
    ["key1=value1", "key2=value2"]

    Output:
    {
        key1: value1,
        key2: value2
    }
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [array]$array
    )

    $hash = @{}

    foreach ($element in $array)
    {
        $hash = $hash + (ConvertFrom-StringData $element)
    }
    return $hash
}