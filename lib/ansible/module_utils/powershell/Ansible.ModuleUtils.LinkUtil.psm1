# Copyright (c) 2017 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

#AnsibleRequires -CSharpUtil Ansible.IO
#AnsibleRequires -CSharpUtil Ansible.Link

Function Load-LinkUtils {
    <#
    .SYNOPSIS
    No-op, as the C# types are automatically loaded.
    #>
    Param ()

    $msg = "Load-LinkUtils is deprecated and no longer needed. this cmdlet will be removed in a future version"
    $result = Get-Variable -Name result -ErrorAction SilentlyContinue
    if ((Get-Command -Name Add-DeprecationWarning -ErrorAction SilentlyContinue) -and $null -ne $result) {
        Add-DeprecationWarning -obj $result.Value -message $msg -version 2.13
    } else {
        $module = Get-Variable -Name module -ErrorAction SilentlyContinue
        if ($null -ne $module -and $module.Value.GetType().FullName -eq "Ansible.Basic.AnsibleModule") {
            $module.Value.Deprecate($msg, "2.13")
        }
    }
}

Function Get-Link {
    <#
    .SYNOPSIS
    Gets information about the link at the path specified. If the object specified by Path is not a link then it will
    return $null.

    .PARAMETER Path
    The path to get the link info for.
    #>
    [CmdletBinding()]
    Param (
        [Parameter(Mandatory=$true)]
        [Alias("link_path")]
        [System.String]$Path
    )

    [Ansible.Link.LinkUtil]::GetLinkInfo($Path)
}

Function Remove-Link {
    <#
    .SYNOPSIS
    Removes the link file or directory specified by Path.

    .PARAMETER Path
    The path to the link to remove.
    #>
    [CmdletBinding(SupportsShouldProcess=$true)]
    Param (
        [Parameter(Mandatory=$true)]
        [Alias("link_path")]
        [System.String]$Path
    )

    Process {
        if ([Ansible.IO.FileSystem]::Exists($Path)) {
            $link_info = Get-Link -Path $Path
            if ($null -ne $link_Info) {
                if ($PSCmdlet.ShouldProcess($Path, "Delete $($link_info.Type)")) {
                    [Ansible.Link.LinkUtil]::DeleteLink($Path)
                }
            }
        }
    }
}

Function New-Link {
    <#
    .SYNOPSIS
    Creates a link at the path specified.

    .PARAMETER Path
    The path to create the link at.

    .PARAMETER TargetPath
    The target of the link to create.

    .PARAMETER Type
    The type of link to create, can be;
        symbolic - A file or directory symbolic link that can span across volumes.
        junction - A directory junction point that must target a dir on the same volume.
        hard - A file hard link that must target a file on the same volume.
    #>
    [CmdletBinding(SupportsShouldProcess=$true)]
    param (
        [Parameter(Mandatory=$true)]
        [Alias("link_path")]
        [System.String]$Path,

        [Parameter(Mandatory=$true)]
        [Alias("link_target")]
        [System.String]$TargetPath,

        [Parameter(Mandatory=$true)]
        [Alias("link_type")]
        [ValidateSet("link", "junction", "hard")]
        [System.String]$Type
    )

    Process {
        switch ($Type) {
            "link" {
                $link_type = [Ansible.Link.LinkType]::SymbolicLink
            }
            "junction" {
                if ([Ansible.IO.FileSystem]::FileExists($TargetPath)) {
                    throw "cannot set the target for a junction point to a file"
                }
                $link_type = [Ansible.Link.LinkType]::JunctionPoint
            }
            "hard" {
                if ([Ansible.IO.FileSystem]::DirectoryExists($TargetPath)) {
                    throw "cannot set the target for a hard link to a directory"
                } elseif (-not ([Ansible.IO.FileSystem]::FileExists($TargetPath))) {
                    throw "link target '$TargetPath' does not exist, cannot create hard link"
                }
                $link_type = [Ansible.Link.LinkType]::HardLink
            }
        }

        if ($PSCmdlet.ShouldProcess($Path, "Create $($link_type.ToString()) targeting $TargetPath")) {
            [Ansible.Link.LinkUtil]::CreateLink($Path, $TargetPath, $link_type)
        }
    }
}

# this line must stay at the bottom to ensure all defined module parts are exported
Export-ModuleMember -Function Get-Link, Load-LinkUtils, New-Link, Remove-Link
