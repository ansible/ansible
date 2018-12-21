#!powershell

# Copyright: (c) 2016, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Based on: http://powershellblogger.com/2016/01/create-shortcuts-lnk-or-url-files-with-powershell/

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

$spec = @{
    options = @{
        src = @{ type='str' }
        dest = @{ type='path'; required=$true }
        state = @{ type='str'; default='present'; choices=@( 'absent', 'present' ) }
        arguments = @{ type='str'; aliases=@( 'args' ) }
        directory = @{ type='path' }
        hotkey = @{ type='str' }
        icon = @{ type='path' }
        description = @{ type='str' }
        windowstyle = @{ type='str'; choices=@( 'maximized', 'minimized', 'normal' ) }
        run_as_admin = @{ type='bool'; default=$false }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$src = $module.Params.src
$dest = $module.Params.dest
$state = $module.Params.state
$arguments = $module.Params.arguments  # NOTE: Variable $args is a special variable
$directory = $module.Params.directory
$hotkey = $module.Params.hotkey
$icon = $module.Params.icon
$description = $module.Params.description
$windowstyle = $module.Params.windowstyle
$run_as_admin = $module.Params.run_as_admin

# Expand environment variables on non-path types
if ($null -ne $src) {
    $src = [System.Environment]::ExpandEnvironmentVariables($src)
}
if ($null -ne $arguments) {
    $arguments = [System.Environment]::ExpandEnvironmentVariables($arguments)
}
if ($null -ne $description) {
    $description = [System.Environment]::ExpandEnvironmentVariables($description)
}

$module.Result.changed = $false
$module.Result.dest = $dest
$module.Result.state = $state

# TODO: look at consolidating other COM actions into the C# class for future compatibility
Add-CSharpType -AnsibleModule $module -References @'
using System;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Text;

namespace Ansible.Shortcut
{
    [ComImport()]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    [Guid("000214F9-0000-0000-C000-000000000046")]
    internal interface IShellLinkW
    {
        // We only care about GetPath and GetIDList, omit the other methods for now
        void GetPath(StringBuilder pszFile, int cch, IntPtr pfd, UInt32 fFlags);
        void GetIDList(out IntPtr ppidl);
    }

    [ComImport()]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    [Guid("45E2b4AE-B1C3-11D0-B92F-00A0C90312E1")]
    internal interface IShellLinkDataList
    {
        void AddDataBlock(IntPtr pDataBlock);
        void CopyDataBlock(uint dwSig, out IntPtr ppDataBlock);
        void RemoveDataBlock(uint dwSig);
        void GetFlags(out ShellLinkFlags dwFlags);
        void SetFlags(ShellLinkFlags dwFlags);
    }

    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct SHFILEINFO
        {
            public IntPtr hIcon;
            public int iIcon;
            public UInt32 dwAttributes;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 260)] public char[] szDisplayName;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 80)] public char[] szTypeName;
        }
    }

    internal class NativeMethods
    {
        [DllImport("shell32.dll")]
        public static extern void ILFree(
            IntPtr pidl);

        [DllImport("shell32.dll")]
        public static extern IntPtr SHGetFileInfoW(
            IntPtr pszPath,
            UInt32 dwFileAttributes,
            ref NativeHelpers.SHFILEINFO psfi,
            int sbFileInfo,
            UInt32 uFlags);

        [DllImport("shell32.dll")]
        public static extern int SHParseDisplayName(
            [MarshalAs(UnmanagedType.LPWStr)] string pszName,
            IntPtr pbc,
            out IntPtr ppidl,
            UInt32 sfagoIn,
            out UInt32 psfgaoOut);
    }

    [System.Flags]
    public enum ShellLinkFlags : uint
    {
        Default = 0x00000000,
        HasIdList = 0x00000001,
        HasLinkInfo = 0x00000002,
        HasName = 0x00000004,
        HasRelPath = 0x00000008,
        HasWorkingDir = 0x00000010,
        HasArgs = 0x00000020,
        HasIconLocation = 0x00000040,
        Unicode = 0x00000080,
        ForceNoLinkInfo = 0x00000100,
        HasExpSz = 0x00000200,
        RunInSeparate = 0x00000400,
        HasLogo3Id = 0x00000800,
        HasDarwinId = 0x00001000,
        RunAsUser = 0x00002000,
        HasExpIconSz = 0x00004000,
        NoPidlAlias = 0x00008000,
        ForceUncName = 0x00010000,
        RunWithShimLayer = 0x00020000,
        ForceNoLinkTrack = 0x00040000,
        EnableTargetMetadata = 0x00080000,
        DisableLinkPathTracking = 0x00100000,
        DisableKnownFolderRelativeTracking = 0x00200000,
        NoKfAlias = 0x00400000,
        AllowLinkToLink = 0x00800000,
        UnAliasOnSave = 0x01000000,
        PreferEnvironmentPath = 0x02000000,
        KeepLocalIdListForUncTarget = 0x04000000,
        PersistVolumeIdToRelative = 0x08000000,
        Valid = 0x0FFFF7FF,
        Reserved = 0x80000000
    }

    public class ShellLink
    {
        private static Guid CLSID_ShellLink = new Guid("00021401-0000-0000-C000-000000000046");

        public static ShellLinkFlags GetFlags(string path)
        {
            IShellLinkW link = InitialiseObj(path);
            ShellLinkFlags dwFlags;
            ((IShellLinkDataList)link).GetFlags(out dwFlags);
            return dwFlags;
        }

        public static void SetFlags(string path, ShellLinkFlags flags)
        {
            IShellLinkW link = InitialiseObj(path);
            ((IShellLinkDataList)link).SetFlags(flags);
            ((IPersistFile)link).Save(null, false);
        }

        public static string GetTargetPath(string path)
        {
            IShellLinkW link = InitialiseObj(path);

            StringBuilder pathSb = new StringBuilder(260);
            link.GetPath(pathSb, pathSb.Capacity, IntPtr.Zero, 0);
            string linkPath = pathSb.ToString();

            // If the path wasn't set, try and get the path from the ItemIDList
            ShellLinkFlags flags = GetFlags(path);
            if (String.IsNullOrEmpty(linkPath) && ((uint)flags & (uint)ShellLinkFlags.HasIdList) == (uint)ShellLinkFlags.HasIdList)
            {
                IntPtr idList = IntPtr.Zero;
                try
                {
                    link.GetIDList(out idList);
                    linkPath = GetDisplayNameFromPidl(idList);
                }
                finally
                {
                    NativeMethods.ILFree(idList);
                }
            }
            return linkPath;
        }

        public static string GetDisplayNameFromPath(string path)
        {
            UInt32 sfgaoOut;
            IntPtr pidl = IntPtr.Zero;
            try
            {
                int res = NativeMethods.SHParseDisplayName(path, IntPtr.Zero, out pidl, 0, out sfgaoOut);
                Marshal.ThrowExceptionForHR(res);
                return GetDisplayNameFromPidl(pidl);
            }
            finally
            {
                NativeMethods.ILFree(pidl);
            }
        }

        private static string GetDisplayNameFromPidl(IntPtr pidl)
        {
            NativeHelpers.SHFILEINFO shFileInfo = new NativeHelpers.SHFILEINFO();
            UInt32 uFlags = 0x000000208;  // SHGFI_DISPLAYNAME | SHGFI_PIDL
            NativeMethods.SHGetFileInfoW(pidl, 0, ref shFileInfo, Marshal.SizeOf(typeof(NativeHelpers.SHFILEINFO)), uFlags);
            return new string(shFileInfo.szDisplayName).TrimEnd('\0');
        }

        private static IShellLinkW InitialiseObj(string path)
        {
            IShellLinkW link = Activator.CreateInstance(Type.GetTypeFromCLSID(CLSID_ShellLink)) as IShellLinkW;
            ((IPersistFile)link).Load(path, 0);
            return link;
        }
    }
}
'@

# Convert from window style name to window style id
$windowstyles = @{
    normal = 1
    maximized = 3
    minimized = 7
}

# Convert from window style id to window style name
$windowstyleids = @( "", "normal", "", "maximized", "", "", "", "minimized" )

If ($state -eq "absent") {
    If (Test-Path -Path $dest) {
        # If the shortcut exists, try to remove it
        Try {
            Remove-Item -Path $dest -WhatIf:$module.CheckMode
        } Catch {
            # Report removal failure
            $module.FailJson("Failed to remove shortcut '$dest'. ($($_.Exception.Message))", $_)
        }
        # Report removal success
        $module.Result.changed = $true
    } Else {
        # Nothing to report, everything is fine already
    }
} ElseIf ($state -eq "present") {
    # Create an in-memory object based on the existing shortcut (if any)
    $Shell = New-Object -ComObject ("WScript.Shell")
    $ShortCut = $Shell.CreateShortcut($dest)

    # Compare existing values with new values, report as changed if required

    If ($null -ne $src) {
        # Windows translates executables to absolute path, so do we
        If (Get-Command -Name $src -Type Application -ErrorAction SilentlyContinue) {
            $src = (Get-Command -Name $src -Type Application).Definition
        }
        If (-not (Test-Path -Path $src -IsValid)) {
            If (-not (Split-Path -Path $src -IsAbsolute)) {
                $module.FailJson("Source '$src' is not found in PATH and not a valid or absolute path.")
            }
        }
    }

    # Determine if we have a WshShortcut or WshUrlShortcut by checking the Arguments property
    # A WshUrlShortcut objects only consists of a TargetPath property

    $file_shortcut = $false
    If (Get-Member -InputObject $ShortCut -Name Arguments) {
        # File ShortCut, compare multiple properties
        $file_shortcut = $true

        $target_path = $ShortCut.TargetPath
        If (($null -ne $src) -and ($ShortCut.TargetPath -ne $src)) {
            if ((Test-Path -Path $dest) -and (-not $ShortCut.TargetPath)) {
                # If the shortcut already exists but not on the COM object, we
                # are dealing with a shell path like 'shell:RecycleBinFolder'.
                $expanded_src = [Ansible.Shortcut.ShellLink]::GetDisplayNameFromPath($src)
                $actual_src = [Ansible.Shortcut.ShellLink]::GetTargetPath($dest)
                if ($expanded_src -ne $actual_src) {
                    $module.Result.changed = $true
                    $ShortCut.TargetPath = $src
                }
            } else {
                $module.Result.changed = $true
                $ShortCut.TargetPath = $src
            }
            $target_path = $src
        }

        # This is a full-featured application shortcut !
        If (($null -ne $arguments) -and ($ShortCut.Arguments -ne $arguments)) {
            $module.Result.changed = $true
            $ShortCut.Arguments = $arguments
        }
        $module.Result.args = $ShortCut.Arguments

        If (($null -ne $directory) -and ($ShortCut.WorkingDirectory -ne $directory)) {
            $module.Result.changed = $true
            $ShortCut.WorkingDirectory = $directory
        }
        $module.Result.directory = $ShortCut.WorkingDirectory

        # FIXME: Not all values are accepted here ! Improve docs too.
        If (($null -ne $hotkey) -and ($ShortCut.Hotkey -ne $hotkey)) {
            $module.Result.changed = $true
            $ShortCut.Hotkey = $hotkey
        }
        $module.Result.hotkey = $ShortCut.Hotkey

        If (($null -ne $icon) -and ($ShortCut.IconLocation -ne $icon)) {
            $module.Result.changed = $true
            $ShortCut.IconLocation = $icon
        }
        $module.Result.icon = $ShortCut.IconLocation

        If (($null -ne $description) -and ($ShortCut.Description -ne $description)) {
            $module.Result.changed = $true
            $ShortCut.Description = $description
        }
        $module.Result.description = $ShortCut.Description

        If (($null -ne $windowstyle) -and ($ShortCut.WindowStyle -ne $windowstyles.$windowstyle)) {
            $module.Result.changed = $true
            $ShortCut.WindowStyle = $windowstyles.$windowstyle
        }
        $module.Result.windowstyle = $windowstyleids[$ShortCut.WindowStyle]
    } else {
        # URL Shortcut, just compare the TargetPath
        if (($null -ne $src) -and ($ShortCut.TargetPath -ne $src)) {
            $module.Result.changed = $true
            $ShortCut.TargetPath = $src
        }
        $target_path = $ShortCut.TargetPath
    }
    $module.Result.src = $target_path

    If (($module.Result.changed -eq $true) -and ($module.CheckMode -ne $true)) {
        Try {
            $ShortCut.Save()
        } Catch {
            $module.FailJson("Failed to create shortcut '$dest'. ($($_.Exception.Message))", $_)
        }
    }

    if ((Test-Path -Path $dest) -and $file_shortcut) {
        # Only control the run_as_admin flag if using a File Shortcut
        $flags = [Ansible.Shortcut.ShellLink]::GetFlags($dest)
        if ($run_as_admin -and (-not $flags.HasFlag([Ansible.Shortcut.ShellLinkFlags]::RunAsUser))) {
            [Ansible.Shortcut.ShellLink]::SetFlags($dest, ($flags -bor [Ansible.Shortcut.ShellLinkFlags]::RunAsUser))
            $module.Result.changed = $true
        } elseif (-not $run_as_admin -and ($flags.HasFlag([Ansible.Shortcut.ShellLinkFlags]::RunAsUser))) {
            [Ansible.Shortcut.ShellLink]::SetFlags($dest, ($flags -bxor [Ansible.Shortcut.ShellLinkFlags]::RunAsUser))
            $module.Result.changed = $true
        }
    }
}

$module.ExitJson()
