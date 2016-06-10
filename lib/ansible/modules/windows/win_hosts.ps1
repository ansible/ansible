#!powershell
# This file is part of Ansible
#
# Copyright 2015, Iago Garrido <iago086@gmail.com>
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


function CreateHostsEntryObject(
    [string] $ipAddress,
    [string[]] $hostnames,
    <# [string] #> $comment) #HACK: never $null if type is specified
{
    $hostsEntry = New-Object PSObject
    $hostsEntry | Add-Member NoteProperty -Name "IpAddress" `
        -Value $ipAddress

    [System.Collections.ArrayList] $hostnamesList =
        New-Object System.Collections.ArrayList

    $hostsEntry | Add-Member NoteProperty -Name "Hostnames" `
        -Value $hostnamesList

    If ($hostnames -ne $null)
    {
        $hostnames | foreach {
            $hostsEntry.Hostnames.Add($_) | Out-Null
        }
    }

    $hostsEntry | Add-Member NoteProperty -Name "Comment" -Value $comment

    return $hostsEntry
}

function ParseHostsEntry(
    [string] $line)
{
    $hostsEntry = CreateHostsEntryObject

    If ($line.Contains("#") -eq $true)
    {
        If ($line -eq "#")
        {
            $hostsEntry.Comment = [string]::Empty
        }
        Else
        {
            $hostsEntry.Comment = $line.Substring($line.IndexOf("#") + 1)
        }

        $line = $line.Substring(0, $line.IndexOf("#"))
    }

    $line = $line.Trim()

    If ($line.Length -gt 0)
    {
        $hostsEntry.IpAddress = ($line -Split "\s+")[0]

        [string[]] $parsedHostnames = $line.Substring(
            $hostsEntry.IpAddress.Length + 1).Trim() -Split "\s+"

        $parsedHostnames | foreach {
            $hostsEntry.Hostnames.Add($_) | Out-Null
        }
    }

    return $hostsEntry
}

function ParseHostsFile
{
    $hostsEntries = New-Object System.Collections.ArrayList

    [string] $hostsFile = $env:WINDIR + "\System32\drivers\etc\hosts"

    If ((Test-Path $hostsFile) -eq $false)
    {
        Throw "Hosts file does not exist."
    }
    Else
    {
        [string[]] $hostsContent = Get-Content $hostsFile

        $hostsContent | foreach {
            $hostsEntry = ParseHostsEntry $_

            $hostsEntries.Add($hostsEntry) | Out-Null
        }
    }

    # HACK: Return an array (containing the ArrayList) to avoid issue with
    # PowerShell returning $null (when hosts file does not exist)
    return ,$hostsEntries
}

function UpdateHostsFile(
    $hostsEntries = $(Throw "Value cannot be null: hostsEntries"))
{
    [string] $hostsFile = $env:WINDIR + "\System32\drivers\etc\hosts"

    $buffer = New-Object System.Text.StringBuilder

    $hostsEntries | foreach {

        If ([string]::IsNullOrEmpty($_.IpAddress) -eq $false)
        {
            $buffer.Append($_.IpAddress) | Out-Null
            $buffer.Append("`t") | Out-Null
        }

        If ($_.Hostnames -ne $null)
        {
            [bool] $firstHostname = $true

            $_.Hostnames | foreach {
                If ($firstHostname -eq $false)
                {
                    $buffer.Append(" ") | Out-Null
                }
                Else
                {
                    $firstHostname = $false
                }

                $buffer.Append($_) | Out-Null
            }
        }

        If ($_.Comment -ne $null)
        {
            If ([string]::IsNullOrEmpty($_.IpAddress) -eq $false)
            {
                $buffer.Append("`t") | Out-Null
            }

            $buffer.Append("#") | Out-Null
            $buffer.Append($_.Comment) | Out-Null
        }

        $buffer.Append([System.Environment]::NewLine) | Out-Null
    }

    [string] $hostsContent = $buffer.ToString()

    $hostsContent = $hostsContent.Trim()

    Set-Content -Path $hostsFile -Value $hostsContent -Force -Encoding ASCII
}

##################################################################################

$params = Parse-Args $args;

$result = New-Object psobject -Property @{
    win_hosts = New-Object psobject
    changed = $false
}

$ip = Get-AnsibleParam -obj $params -name "ip" -failifempty $true
$hostname = Get-AnsibleParam -obj $params -name "hostname" -failifempty $true
$comment = Get-AnsibleParam -obj $params -name "comment" -default $null
$state = Get-AnsibleParam -obj $params -name "state" -failifempty $true -ValidateSet "present","absent"


try {
    $hostsEntries = ParseHostsFile
    $pendingUpdates = $false

    for ([int] $i = 0; $i -lt $hostsEntries.Count; $i++)
    {
        $hostsEntry = $hostsEntries[$i]

        If ($hostsEntry.Hostnames.Count -eq 0)
        {
            continue
        }

        for ([int] $j = 0; $j -lt $hostsEntry.Hostnames.Count; $j++)
        {
            [string] $parsedHostname = $hostsEntry.Hostnames[$j]

            If ([string]::Compare($hostname, $parsedHostname, $true) -eq 0)
            {
                If ($ip -ne $hostsEntry.IpAddress)
                {
                    If ($state -eq "present")
                    {
                        If ($hostsEntry.Hostnames.Count -gt 1)
                        {
                            $hostsEntry.Hostnames.RemoveAt($j)
                            $j--

                            $newHostsEntry = CreateHostsEntryObject $ip $hostname $comment

                            $hostsEntries.Add($newHostsEntry) | Out-Null

                            $pendingUpdates = $true
                        }
                        Else
                        {
                            $hostsEntry.IpAddress = $ip
                            $hostsEntry.Comment = $comment

                            $pendingUpdates = $true
                        }
                    }
                    ElseIf ($state -eq "absent")
                    {
                        Continue
                    }
                }
                Else
                {
                    If ($state -eq "present")
                    {
                        Exit-Json $result
                    }
                    ElseIf ($state -eq "absent")
                    {
                        $hostsEntry.Hostnames.RemoveAt($j)
                        $j--

                        $pendingUpdates = $true
                    }
                }
            }
        }

        If ($hostsEntry.Hostnames.Count -eq 0)
        {
            $hostsEntries.RemoveAt($i)
            $i--
        }

        If ($pendingUpdates)
        {
            Break
        }
    }

    If ($pendingUpdates)
    {
        UpdateHostsFile $hostsEntries
        $result.changed = $true
    }
    ElseIf ($state -eq "present")
    {
        $newHostsEntry = CreateHostsEntryObject $ip $hostname $comment
        $hostsEntries.Add($newHostsEntry) | Out-Null

        UpdateHostsFile $hostsEntries
        $result.changed = $true
    }
} catch {
    Set-Attr $result "exception" $_.Exception.Message
    Fail-Json $result "error managing hosts"
}

Exit-Json $result
