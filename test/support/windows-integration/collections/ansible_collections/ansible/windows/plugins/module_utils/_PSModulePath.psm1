# Copyright: (c) 2024, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This module_util is for internal use only. It is not intended to be used by
# collections outside of ansible.windows.

using namespace System.IO
using namespace System.Collections.Generic

Function Get-WinPSModulePath {
    <#
    .SYNOPSIS
    Gets a PSModulePath that can be used to spawn Windows PowerShell from PowerShell 7.

    If spawning powershell.exe from within pwsh.exe we need to strip out the
    PSModulePath entries that point to the v7 modules. This ensures that
    WinPS doesn't try and load incompatible modules. The logic here is from
    PowerShell itself.
    https://github.com/PowerShell/PowerShell/blob/e7bf5621bf8c3dfe7c4bdc69f83178077ec7bd5d/
    src/System.Management.Automation/engine/Modules/ModuleIntrinsics.cs#L1300-L1349
    #>
    [OutputType([string])]
    param ()

    $excludePaths = [HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)

    [Environment+SpecialFolder]::MyDocuments, [Environment+SpecialFolder]::ProgramFiles | ForEach-Object -Process {
        $basePath = [Environment]::GetFolderPath($_)
        if ($basePath) {
            $null = $excludePaths.Add("$basePath\PowerShell\Modules")
        }
    }

    $psHomePath = "$($PSHome.Replace("\syswow64\", "\system32\"), [StringComparison]::OrdinalIgnoreCase))\Modules"
    $null = $excludePaths.Add($psHomePath)

    # These values are from the pwsh.exe.config file but there is no public API
    # to retrieve them. We may want to add these to the exclude list in the
    # future but it'll be rare for people to set these.
    # PowerShellConfig.Instance.GetModulePath(ConfigScope.AllUsers)
    # PowerShellConfig.Instance.GetModulePath(ConfigScope.CurrentUser)

    $newPath = @(
        $env:PSModulePath.Split([Path]::PathSeparator, [StringSplitOptions]'RemoveEmptyEntries, TrimEntries') | Where-Object {
            if ($excludePaths.Contains($_)) {
                return $false
            }

            # Check that we haven't inherited any other Pwsh 7.x PSHome
            # directories.
            $entryDir = [Path]::GetDirectoryName($_)
            $pwshDll = [Path]::Combine($entryDir, "pwsh.dll")
            return -not (Test-Path -LiteralPath $pwshDll)
        }
    )

    $newPath -join ([Path]::PathSeparator)
}

Export-ModuleMember -Function Get-WinPSModulePath
