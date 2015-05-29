# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2014, and others
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# Helper function to parse Ansible JSON arguments from a file passed as
# the single argument to the module
# Example: $params = Parse-Args $args
Function Parse-Args($arguments)
{
    $parameters = New-Object psobject;
    If ($arguments.Length -gt 0)
    {
        $parameters = Get-Content $arguments[0] | ConvertFrom-Json;
    }
    $parameters;
}

# Helper function to set an "attribute" on a psobject instance in powershell.
# This is a convenience to make adding Members to the object easier and
# slightly more pythonic
# Example: Set-Attr $result "changed" $true
Function Set-Attr($obj, $name, $value)
{
    # If the provided $obj is undefined, define one to be nice
    If (-not $obj.GetType)
    {
        $obj = New-Object psobject
    }

    $obj | Add-Member -Force -MemberType NoteProperty -Name $name -Value $value
}

# Helper function to convert a powershell object to JSON to echo it, exiting
# the script
# Example: Exit-Json $result
Function Exit-Json($obj)
{
    # If the provided $obj is undefined, define one to be nice
    If (-not $obj.GetType)
    {
        $obj = New-Object psobject
    }

    echo $obj | ConvertTo-Json -Depth 99
    Exit
}

# Helper function to add the "msg" property and "failed" property, convert the
# powershell object to JSON and echo it, exiting the script
# Example: Fail-Json $result "This is the failure message"
Function Fail-Json($obj, $message = $null)
{
    # If we weren't given 2 args, and the only arg was a string, create a new
    # psobject and use the arg as the failure message
    If ($message -eq $null -and $obj.GetType().Name -eq "String")
    {
        $message = $obj
        $obj = New-Object psobject
    }
    # If the first args is undefined or not an object, make it an object
    ElseIf (-not $obj.GetType -or $obj.GetType().Name -ne "PSCustomObject")
    {
        $obj = New-Object psobject
    }

    Set-Attr $obj "msg" $message
    Set-Attr $obj "failed" $true
    echo $obj | ConvertTo-Json -Depth 99
    Exit 1
}

# Helper function to get an "attribute" from a psobject instance in powershell.
# This is a convenience to make getting Members from an object easier and
# slightly more pythonic
# Example: $attr = Get-Attr $response "code" -default "1"
#Note that if you use the failifempty option, you do need to specify resultobject as well.
Function Get-Attr($obj, $name, $default = $null,$resultobj, $failifempty=$false, $emptyattributefailmessage)
{
    # Check if the provided Member $name exists in $obj and return it or the
    # default
    If ($obj.$name.GetType)
    {
        $obj.$name
    }
    Elseif($failifempty -eq $false)
    {
        $default
    }
    else
    {
        if (!$emptyattributefailmessage) {$emptyattributefailmessage = "Missing required argument: $name"}
        Fail-Json -obj $resultobj -message $emptyattributefailmessage
    }
    return
}

# Helper filter/pipeline function to convert a value to boolean following current
# Ansible practices
# Example: $is_true = "true" | ConvertTo-Bool
Function ConvertTo-Bool
{
    param(
        [parameter(valuefrompipeline=$true)]
        $obj
    )

    $boolean_strings = "yes", "on", "1", "true", 1
    $obj_string = [string]$obj

    if (($obj.GetType().Name -eq "Boolean" -and $obj) -or $boolean_strings -contains $obj_string.ToLower())
    {
        $true
    }
    Else
    {
        $false
    }
    return
}

# Helper function to calculate a hash of a file in a way which powershell 3 
# and above can handle:
Function Get-FileChecksum($path)
{
    $hash = ""
    If (Test-Path -PathType Leaf $path)
    {
        $sp = new-object -TypeName System.Security.Cryptography.SHA1CryptoServiceProvider;
        $fp = [System.IO.File]::Open($path, [System.IO.Filemode]::Open, [System.IO.FileAccess]::Read);
        $hash = [System.BitConverter]::ToString($sp.ComputeHash($fp)).Replace("-", "").ToLower();
        $fp.Dispose();
    }
    ElseIf (Test-Path -PathType Container $path)
    {
        $hash= "3";
    }
    Else
    {
        $hash = "1";
    }
    return $hash
}
