#!powershell

# Copyright: (c) 2017, Liran Nisanov <lirannis@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#Requires -Module Ansible.ModuleUtils.Legacy

########

Function Remove-Pagefile($path, $whatif)
{
    Get-CIMInstance Win32_PageFileSetting | Where-Object { $_.Name -eq $path } | Remove-CIMInstance -WhatIf:$whatif
}

Function Get-Pagefile($path)
{
    Get-CIMInstance Win32_PageFileSetting | Where-Object { $_.Name -eq $path }
}

########

$params = Parse-Args $args -supports_check_mode $true
$check_mode = Get-AnsibleParam -obj $params -name '_ansible_check_mode' -type 'bool' -default $false

$automatic = Get-AnsibleParam -obj $params -name "automatic" -type "bool"
$drive = Get-AnsibleParam -obj $params -name "drive" -type "str"
$fullPath = $drive + ":\pagefile.sys"
$initialSize = Get-AnsibleParam -obj $params -name "initial_size" -type "int"
$maximumSize = Get-AnsibleParam -obj $params -name "maximum_size" -type "int"
$override =  Get-AnsibleParam -obj $params -name "override" -type "bool" -default $true
$removeAll = Get-AnsibleParam -obj $params -name "remove_all" -type "bool" -default $false
$state = Get-AnsibleParam -obj $params -name "state" -type "str" -default "query" -validateset "present","absent","query"
$systemManaged = Get-AnsibleParam -obj $params -name "system_managed" -type "bool" -default $false
$testPath = Get-AnsibleParam -obj $params -name "test_path" -type "bool" -default $true

$result = @{
    changed = $false
}

if ($removeAll) {
    $currentPageFiles = Get-CIMInstance Win32_PageFileSetting
    if ($null -ne $currentPageFiles) {
        $currentPageFiles | Remove-CIMInstance -WhatIf:$check_mode > $null
        $result.changed = $true
    }
}

if ($null -ne $automatic) {
    # change autmoatic managed pagefile
    try {
        $computerSystem = Get-CIMInstance -Class win32_computersystem
    } catch {
        Fail-Json $result "Failed to query WMI computer system object $($_.Exception.Message)"
    }
    if ($computerSystem.AutomaticManagedPagefile -ne $automatic) {
        if (-not $check_mode) {
            try {
            	$computerSystem | Set-CimInstance -Property @{automaticmanagedpagefile="$automatic"} > $null
            } catch {
                Fail-Json $result "Failed to set AutomaticManagedPagefile $($_.Exception.Message)"
            }
        }
        $result.changed = $true
    }
}

if ($state -eq "absent") {
    # Remove pagefile
    if ($null -ne (Get-Pagefile $fullPath))
    {
        try {
            Remove-Pagefile $fullPath -whatif:$check_mode
        } catch {
            Fail-Json $result "Failed to remove pagefile $($_.Exception.Message)"
        }
        $result.changed = $true
    }
} elseif ($state -eq "present") {
    # Remove current pagefile
    if ($override) {
        if ($null -ne (Get-Pagefile $fullPath))
        {
            try {
                Remove-Pagefile $fullPath -whatif:$check_mode
            } catch {
                Fail-Json $result "Failed to remove current pagefile $($_.Exception.Message)"
            }
            $result.changed = $true
        }
    }

    # Make sure drive is accessible
    if (($test_path) -and (-not (Test-Path "${drive}:"))) {
        Fail-Json $result "Unable to access '${drive}:' drive"
    }

    $curPagefile = Get-Pagefile $fullPath

    # Set pagefile
    if ($null -eq $curPagefile) {
        try {
            $pagefile = New-CIMInstance -Class Win32_PageFileSetting -Arguments @{name = $fullPath;} -WhatIf:$check_mode
        } catch {
            Fail-Json $result "Failed to create pagefile $($_.Exception.Message)"
        }
        if (-not ($systemManaged -or $check_mode)) {
            try {
                $pagefile | Set-CimInstance -Property @{ InitialSize = $initialSize; MaximumSize = $maximumSize}
            } catch {
                $originalExceptionMessage = $($_.Exception.Message)
                # Try workaround before failing
                try {
                    Remove-Pagefile $fullPath -whatif:$check_mode
                } catch {
                    Fail-Json $result "Failed to remove pagefile before workaround $($_.Exception.Message) Original exception: $originalExceptionMessage"
                }
                try {
                    $pagingFilesValues = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management").PagingFiles
                } catch {
                    Fail-Json $result "Failed to get pagefile settings from the registry for workaround $($_.Exception.Message) Original exception: $originalExceptionMessage"
                }
                $pagingFilesValues += "$fullPath $initialSize $maximumSize"
                try {
                    Set-ItemProperty -LiteralPath "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" "PagingFiles" $pagingFilesValues
                } catch {
                    Fail-Json $result "Failed to set pagefile settings to the registry for workaround $($_.Exception.Message) Original exception: $originalExceptionMessage"
                }
            }
        }
        $result.changed = $true
    }else
    {
        $CurPageFileSystemManaged = (Get-CimInstance -ClassName win32_Pagefile -Property 'System' -Filter "name='$($fullPath.Replace('\','\\'))'").System
        if ((-not $check_mode) -and
            -not ($systemManaged -or $CurPageFileSystemManaged) -and
            (   ($curPagefile.InitialSize -ne $initialSize) -or
                ($curPagefile.maximumSize -ne $maximumSize)))
        {
            $curPagefile.InitialSize = $initialSize
            $curPagefile.MaximumSize = $maximumSize
            try {
                $curPagefile.Put() | out-null
            } catch {
                $originalExceptionMessage = $($_.Exception.Message)
                # Try workaround before failing
                try {
                    Remove-Pagefile $fullPath -whatif:$check_mode
                } catch {
                    Fail-Json $result "Failed to remove pagefile before workaround $($_.Exception.Message) Original exception: $originalExceptionMessage"
                }
                try {
                    $pagingFilesValues = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management").PagingFiles
                } catch {
                    Fail-Json $result "Failed to get pagefile settings from the registry for workaround $($_.Exception.Message) Original exception: $originalExceptionMessage"
                }
                $pagingFilesValues += "$fullPath $initialSize $maximumSize"
                try {
                    Set-ItemProperty -LiteralPath "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" -Name "PagingFiles" -Value $pagingFilesValues
                } catch {
                    Fail-Json $result "Failed to set pagefile settings to the registry for workaround $($_.Exception.Message) Original exception: $originalExceptionMessage"
                }
            }
            $result.changed = $true
        }
    }
} elseif ($state -eq "query") {
    $result.pagefiles = @()

    if ($null -eq $drive) {
        try {
            $pagefiles = Get-CIMInstance Win32_PageFileSetting
        } catch {
            Fail-Json $result "Failed to query all pagefiles $($_.Exception.Message)"
        }
    } else {
        try {
            $pagefiles = Get-Pagefile $fullPath
        } catch {
            Fail-Json $result "Failed to query specific pagefile $($_.Exception.Message)"
        }
    }

    # Get all pagefiles
    foreach ($currentPagefile in $pagefiles) {
        $currentPagefileObject = @{
            name = $currentPagefile.Name
            initial_size = $currentPagefile.InitialSize
            maximum_size = $currentPagefile.MaximumSize
            caption = $currentPagefile.Caption
            description = $currentPagefile.Description
        }
        $result.pagefiles += ,$currentPagefileObject
    }

    # Get automatic managed pagefile state
    try {
        $result.automatic_managed_pagefiles = (Get-CIMInstance -Class win32_computersystem).AutomaticManagedPagefile
    } catch {
        Fail-Json $result "Failed to query automatic managed pagefile state $($_.Exception.Message)"
    }
}
Exit-Json $result
