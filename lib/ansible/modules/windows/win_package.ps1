#!powershell

# Copyright: (c) 2014, Trond Hindenes <trond@hindenes.com>, and others
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# AccessToken should be removed once the username/password options are gone
#AnsibleRequires -CSharpUtil Ansible.AccessToken

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType
#Requires -Module Ansible.ModuleUtils.ArgvParser
#Requires -Module Ansible.ModuleUtils.CommandUtil
#Requires -Module Ansible.ModuleUtils.WebRequest

Function Import-PInvokeCode {
    param (
        [Object]
        $Module
    )
        Add-CSharpType -AnsibleModule $Module -References @'
using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Security.Principal;
using System.Text;

//AssemblyReference -Type System.Security.Principal.IdentityReference -CLR Core

namespace Ansible.WinPackage
{
    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential)]
        public struct PACKAGE_VERSION
        {
            public UInt16 Revision;
            public UInt16 Build;
            public UInt16 Minor;
            public UInt16 Major;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public struct PACKAGE_ID
        {
            public UInt32 reserved;
            public MsixArchitecture processorArchitecture;
            public PACKAGE_VERSION version;
            public string name;
            public string publisher;
            public string resourceId;
            public string publisherId;
        }
    }

    internal class NativeMethods
    {
        [DllImport("Ole32.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 GetClassFile(
            [MarshalAs(UnmanagedType.LPWStr)] string szFilename,
            ref Guid pclsid);

        [DllImport("Msi.dll")]
        public static extern UInt32 MsiCloseHandle(
            IntPtr hAny);

        [DllImport("Msi.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 MsiEnumPatchesExW(
            [MarshalAs(UnmanagedType.LPWStr)] string szProductCode,
            [MarshalAs(UnmanagedType.LPWStr)] string szUserSid,
            InstallContext dwContext,
            PatchState dwFilter,
            UInt32 dwIndex,
            StringBuilder szPatchCode,
            StringBuilder szTargetProductCode,
            out InstallContext pdwTargetProductContext,
            StringBuilder szTargetUserSid,
            ref UInt32 pcchTargetUserSid);

        [DllImport("Msi.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 MsiGetPatchInfoExW(
            [MarshalAs(UnmanagedType.LPWStr)] string szPatchCode,
            [MarshalAs(UnmanagedType.LPWStr)] string szProductCode,
            [MarshalAs(UnmanagedType.LPWStr)] string szUserSid,
            InstallContext dwContext,
            [MarshalAs(UnmanagedType.LPWStr)] string szProperty,
            StringBuilder lpValue,
            ref UInt32 pcchValue);

        [DllImport("Msi.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 MsiGetPropertyW(
            SafeMsiHandle hInstall,
            [MarshalAs(UnmanagedType.LPWStr)] string szName,
            StringBuilder szValueBuf,
            ref UInt32 pcchValueBuf);

        [DllImport("Msi.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 MsiGetSummaryInformationW(
            IntPtr hDatabase,
            [MarshalAs(UnmanagedType.LPWStr)] string szDatabasePath,
            UInt32 uiUpdateCount,
            out SafeMsiHandle phSummaryInfo);

        [DllImport("Msi.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 MsiOpenPackageW(
            [MarshalAs(UnmanagedType.LPWStr)] string szPackagePath,
            out SafeMsiHandle hProduct);

        [DllImport("Msi.dll", CharSet = CharSet.Unicode)]
        public static extern InstallState MsiQueryProductStateW(
            [MarshalAs(UnmanagedType.LPWStr)] string szProduct);

        [DllImport("Msi.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 MsiSummaryInfoGetPropertyW(
            SafeHandle hSummaryInfo,
            UInt32 uiProperty,
            out UInt32 puiDataType,
            out Int32 piValue,
            ref System.Runtime.InteropServices.ComTypes.FILETIME pftValue,
            StringBuilder szValueBuf,
            ref UInt32 pcchValueBuf);

        [DllImport("Kernel32.dll", CharSet = CharSet.Unicode)]
        public static extern UInt32 PackageFullNameFromId(
            NativeHelpers.PACKAGE_ID packageId,
            ref UInt32 packageFamilyNameLength,
            StringBuilder packageFamilyName);
    }

    [Flags]
    public enum InstallContext : uint
    {
        None = 0x00000000,
        UserManaged = 0x00000001,
        UserUnmanaged = 0x00000002,
        Machine = 0x00000004,
        AllUserManaged = 0x00000008,
        All = UserManaged | UserUnmanaged | Machine,
    }

    public enum InstallState : int
    {
        NotUsed = -7,
        BadConfig = -6,
        Incomplete = -5,
        SourceAbsent = -4,
        MoreData = -3,
        InvalidArg = -2,
        Unknown = -1,
        Broken = 0,
        Advertised = 1,
        Absent = 2,
        Local = 3,
        Source = 4,
        Default = 5,
    }

    public enum MsixArchitecture : uint
    {
        X86 = 0,
        Arm = 5,
        X64 = 9,
        Neutral = 11,
        Arm64 = 12,
    }

    [Flags]
    public enum PatchState : uint
    {
        Invalid = 0x00000000,
        Applied = 0x00000001,
        Superseded = 0x00000002,
        Obsoleted = 0x00000004,
        Registered = 0x00000008,
        All = Applied | Superseded | Obsoleted | Registered,
    }

    public class SafeMsiHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeMsiHandle() : base(true) { }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            UInt32 res = NativeMethods.MsiCloseHandle(handle);
            return res == 0;
        }
    }

    public class PatchInfo
    {
        public string PatchCode;
        public string ProductCode;
        public InstallContext Context;
        public SecurityIdentifier UserSid;
    }

    public class MsixHelper
    {
        public static string GetPackageFullName(string identity, string version, string publisher,
            MsixArchitecture architecture, string resourceId)
        {
            string[] versionSplit = version.Split(new char[] {'.'}, 4);
            NativeHelpers.PACKAGE_ID id = new NativeHelpers.PACKAGE_ID()
            {
                processorArchitecture = architecture,
                version = new NativeHelpers.PACKAGE_VERSION()
                {
                    Revision = Convert.ToUInt16(versionSplit.Length > 3 ? versionSplit[3] : "0"),
                    Build = Convert.ToUInt16(versionSplit.Length > 2 ? versionSplit[2] : "0"),
                    Minor = Convert.ToUInt16(versionSplit.Length > 1 ? versionSplit[1] : "0"),
                    Major = Convert.ToUInt16(versionSplit[0]),
                },
                name = identity,
                publisher = publisher,
                resourceId = resourceId,
            };

            UInt32 fullNameLength = 0;
            UInt32 res = NativeMethods.PackageFullNameFromId(id, ref fullNameLength, null);
            if (res != 122)  // ERROR_INSUFFICIENT_BUFFER
                throw new Win32Exception((int)res);

            StringBuilder fullName = new StringBuilder((int)fullNameLength);
            res = NativeMethods.PackageFullNameFromId(id, ref fullNameLength, fullName);
            if (res != 0)
                throw new Win32Exception((int)res);

            return fullName.ToString();
        }
    }

    public class MsiHelper
    {
        public static UInt32 SUMMARY_PID_TEMPLATE = 7;
        public static UInt32 SUMMARY_PID_REVNUMBER = 9;

        private static Guid MSI_CLSID = new Guid("000c1084-0000-0000-c000-000000000046");
        private static Guid MSP_CLSID = new Guid("000c1086-0000-0000-c000-000000000046");

        public static IEnumerable<PatchInfo> EnumPatches(string productCode, string userSid, InstallContext context,
            PatchState filter)
        {
            // PowerShell -> .NET, $null for a string parameter becomes an empty string, make sure we convert back.
            productCode = String.IsNullOrEmpty(productCode) ? null : productCode;
            userSid = String.IsNullOrEmpty(userSid) ? null : userSid;

            UInt32 idx = 0;
            while (true)
            {
                StringBuilder targetPatchCode = new StringBuilder(39);
                StringBuilder targetProductCode = new StringBuilder(39);
                InstallContext targetContext;
                StringBuilder targetUserSid = new StringBuilder(0);
                UInt32 targetUserSidLength = 0;

                UInt32 res = NativeMethods.MsiEnumPatchesExW(productCode, userSid, context, filter, idx,
                    targetPatchCode, targetProductCode, out targetContext, targetUserSid, ref targetUserSidLength);

                SecurityIdentifier sid = null;
                if (res == 0x000000EA)  // ERROR_MORE_DATA
                {
                    targetUserSidLength++;
                    targetUserSid.EnsureCapacity((int)targetUserSidLength);

                    res = NativeMethods.MsiEnumPatchesExW(productCode, userSid, context, filter, idx,
                        targetPatchCode, targetProductCode, out targetContext, targetUserSid, ref targetUserSidLength);

                    sid = new SecurityIdentifier(targetUserSid.ToString());
                }

                if (res == 0x00000103)  // ERROR_NO_MORE_ITEMS
                    break;
                else if (res != 0)
                    throw new Win32Exception((int)res);

                yield return new PatchInfo()
                {
                    PatchCode = targetPatchCode.ToString(),
                    ProductCode = targetProductCode.ToString(),
                    Context = targetContext,
                    UserSid = sid,
                };
                idx++;
            }
        }

        public static string GetPatchInfo(string patchCode, string productCode, string userSid, InstallContext context,
            string property)
        {
            // PowerShell -> .NET, $null for a string parameter becomes an empty string, make sure we convert back.
            userSid = String.IsNullOrEmpty(userSid) ? null : userSid;

            StringBuilder buffer = new StringBuilder(0);
            UInt32 bufferLength = 0;
            NativeMethods.MsiGetPatchInfoExW(patchCode, productCode, userSid, context, property, buffer,
                ref bufferLength);

            bufferLength++;
            buffer.EnsureCapacity((int)bufferLength);

            UInt32 res = NativeMethods.MsiGetPatchInfoExW(patchCode, productCode, userSid, context, property, buffer,
                ref bufferLength);
            if (res != 0)
                throw new Win32Exception((int)res);

            return buffer.ToString();
        }

        public static string GetProperty(SafeMsiHandle productHandle, string property)
        {
            StringBuilder buffer = new StringBuilder(0);
            UInt32 bufferLength = 0;
            NativeMethods.MsiGetPropertyW(productHandle, property, buffer, ref bufferLength);

            // Make sure we include the null byte char at the end.
            bufferLength += 1;
            buffer.EnsureCapacity((int)bufferLength);

            UInt32 res = NativeMethods.MsiGetPropertyW(productHandle, property, buffer, ref bufferLength);
            if (res != 0)
                throw new Win32Exception((int)res);

            return buffer.ToString();
        }

        public static SafeMsiHandle GetSummaryHandle(string databasePath)
        {
            SafeMsiHandle summaryInfo = null;
            UInt32 res = NativeMethods.MsiGetSummaryInformationW(IntPtr.Zero, databasePath, 0, out summaryInfo);
            if (res != 0)
                throw new Win32Exception((int)res);

            return summaryInfo;
        }

        public static string GetSummaryPropertyString(SafeMsiHandle summaryHandle, UInt32 propertyId)
        {
            UInt32 dataType = 0;
            Int32 intPropValue = 0;
            System.Runtime.InteropServices.ComTypes.FILETIME propertyFiletime =
                new System.Runtime.InteropServices.ComTypes.FILETIME();
            StringBuilder buffer = new StringBuilder(0);
            UInt32 bufferLength = 0;

            NativeMethods.MsiSummaryInfoGetPropertyW(summaryHandle, propertyId, out dataType, out intPropValue,
                ref propertyFiletime, buffer, ref bufferLength);

            // Make sure we include the null byte char at the end.
            bufferLength += 1;
            buffer.EnsureCapacity((int)bufferLength);

            UInt32 res = NativeMethods.MsiSummaryInfoGetPropertyW(summaryHandle, propertyId, out dataType,
                out intPropValue, ref propertyFiletime, buffer, ref bufferLength);
            if (res != 0)
                throw new Win32Exception((int)res);

            return buffer.ToString();
        }

        public static bool IsMsi(string filename)
        {
            return GetClsid(filename) == MSI_CLSID;
        }

        public static bool IsMsp(string filename)
        {
            return GetClsid(filename) == MSP_CLSID;
        }

        public static SafeMsiHandle OpenPackage(string packagePath)
        {
            SafeMsiHandle packageHandle = null;
            UInt32 res = NativeMethods.MsiOpenPackageW(packagePath, out packageHandle);
            if (res != 0)
                throw new Win32Exception((int)res);

            return packageHandle;
        }

        public static InstallState QueryProductState(string productCode)
        {
            return NativeMethods.MsiQueryProductStateW(productCode);
        }

        private static Guid GetClsid(string filename)
        {
            Guid clsid = Guid.Empty;
            NativeMethods.GetClassFile(filename, ref clsid);

            return clsid;
        }
    }
}
'@
}

Function Add-SystemReadAce {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [String]
        $Path
    )

    # Don't set the System ACE if the path is a UNC path as the SID won't be valid.
    if (([Uri]$Path).IsUnc) {
        return
    }

    $acl = Get-Acl -LiteralPath $Path
    $ace = New-Object -TypeName System.Security.AccessControl.FileSystemAccessRule -ArgumentList @(
        (New-Object -TypeName System.Security.Principal.SecurityIdentifier -ArgumentList ('S-1-5-18')),
        [System.Security.AccessControl.FileSystemRights]::Read,
        [System.Security.AccessControl.AccessControlType]::Allow
    )
    $acl.AddAccessRule($ace)
    $acl | Set-Acl -LiteralPath $path
}

Function Copy-ItemWithCredential {
    [CmdletBinding(SupportsShouldProcess=$false)]
    param (
        [String]
        $Path,

        [String]
        $Destination,

        [PSCredential]
        $Credential
    )

    $filename = Split-Path -Path $Path -Leaf
    $targetPath = Join-Path -Path $Destination -ChildPath $filename

    # New-PSDrive with -Credentials seems to have lots of issues, just impersonate a NewCredentials token and copy the
    # file locally. NewCredentials will ensure the outbound auth to the UNC path is with the new credentials specified.

    $domain = [NullString]::Value
    $username = $Credential.UserName
    if ($username.Contains('\')) {
        $userSplit = $username.Split('\', 2)
        $domain = $userSplit[0]
        $username = $userSplit[1]
    }

    $impersonated = $false
    $token = [Ansible.AccessToken.TokenUtil]::LogonUser(
        $username, $domain, $Credential.GetNetworkCredential().Password,
        [Ansible.AccessToken.LogonType]::NewCredentials, [Ansible.AccessToken.LogonProvider]::WinNT50
    )
    try {
        [Ansible.AccessToken.TokenUtil]::ImpersonateToken($token)
        $impersonated = $true

        Copy-Item -LiteralPath $Path -Destination $targetPath
    } finally {
        if ($impersonated) {
            [Ansible.AccessToken.TokenUtil]::RevertToSelf()
        }
        $token.Dispose()
    }

    $targetPath
}

Function Get-UrlFile {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [Object]
        $Module,

        [Parameter(Mandatory=$true)]
        [String]
        $Url
    )

    Invoke-WithWebRequest -Module $module -Request (Get-AnsibleWebRequest -Url $Url -Module $module) -Script {
        Param ([System.Net.WebResponse]$Response, [System.IO.Stream]$Stream)

        $tempPath = Join-Path -Path $module.Tmpdir -ChildPath $Response.ResponseUri.Segments[-1]
        $fs = [System.IO.File]::Create($tempPath)
        try {
            $Stream.CopyTo($fs)
            $fs.Flush()
        } finally {
            $fs.Dispose()
        }

        $tempPath
    }
}

Function Format-PackageStatus {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [AllowEmptyString()]
        [String]
        $Id,

        [Parameter(Mandatory=$true)]
        [String]
        $Provider,

        [Switch]
        $Installed,

        [Switch]
        $Skip,

        [Switch]
        $SkipFileForRemove,

        [Hashtable]
        $ExtraInfo = @{}
    )

    @{
        Id = $Id
        Installed = $Installed.IsPresent
        Provider = $Provider
        Skip = $Skip.IsPresent
        SkipFileForRemove = $SkipFileForRemove.IsPresent
        ExtraInfo = $ExtraInfo
    }
}

Function Get-InstalledStatus {
    [CmdletBinding()]
    param (
        [String]
        $Path,

        [String]
        $Id,

        [String]
        $Provider,

        [String]
        $CreatesPath,

        [String]
        $CreatesService,

        [String]
        $CreatesVersion
    )

    if ($Path) {
        if ($Provider -eq 'auto') {
            foreach ($info in $providerInfo.GetEnumerator()) {
                if ((&$info.Value.FileSupported -Path $Path)) {
                    $Provider = $info.Key
                    break
                }
            }
        }

        $status = &$providerInfo."$Provider".Test -Path $Path -Id $Id
    } else {
        if ($Provider -eq 'auto') {
            $providerList = [String[]]$providerInfo.Keys
        } else {
            $providerList = @($Provider)
        }

        foreach ($name in $providerList) {
            $status = &$providerInfo."$name".Test -Id $Id

            # If the package was installed for the provider (or was the last provider available).
            if ($status.Installed -or $providerList[-1] -eq $name) {
                break
            }
        }
    }

    if ($CreatesPath) {
        $exists = Test-Path -LiteralPath $CreatesPath
        $status.Installed = $exists

        if ($CreatesVersion) {
            if (Test-Path -LiteralPath $CreatesPath -PathType Leaf) {
                $versionRaw = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($CreatesPath)
                $existingVersion = New-Object -TypeName System.Version -ArgumentList @(
                    $versionRaw.FileMajorPart, $versionRaw.FileMinorPart, $versionRaw.FileBuildPart,
                    $versionRaw.FilePrivatePart
                )
                $status.Installed = $CreatesVersion -eq $existingVersion
            } else {
                throw "creates_path must be a file not a directory when creates_version is set"
            }
        }
    }

    if ($CreatesService) {
        $serviceInfo = Get-Service -Name $CreatesService -ErrorAction SilentlyContinue
        $status.Installed = $null -ne $serviceInfo
    }

    Format-PackageStatus @status
}

Function Invoke-Executable {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [Object]
        $Module,

        [Parameter(Mandatory=$true)]
        [String]
        $Command,

        [Int32[]]
        $ReturnCodes,

        [String]
        $LogPath,

        [String]
        $WorkingDirectory,

        [String]
        $ConsoleOutputEncoding
    )

    $commandArgs = @{
        command = $Command
    }
    if ($WorkingDirectory) {
        $commandArgs.working_directory = $WorkingDirectory
    }
    if ($ConsoleOutputEncoding) {
        $commandArgs.output_encoding_override = $ConsoleOutputEncoding
    }

    $result = Run-Command @commandArgs

    $module.Result.rc = $result.rc
    if ($ReturnCodes -notcontains $result.rc) {
        $module.Result.stdout = $result.stdout
        $module.Result.stderr = $result.stderr
        if ($LogPath -and (Test-Path -LiteralPath $LogPath)) {
            $module.Result.log = (Get-Content -LiteralPath $LogPath | Out-String)
        }

        $module.FailJson("unexpected rc from '$($commandArgs.command)': see rc, stdout, and stderr for more details")
    } else {
        $module.Result.failed = $false
    }

    if ($result.rc -eq 3010) {
        $module.Result.reboot_required = $true
    }
}

Function Invoke-Msiexec {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [Object]
        $Module,

        [Parameter(Mandatory=$true)]
        [String[]]
        $Actions,

        [String]
        $Arguments,

        [Int32[]]
        $ReturnCodes,

        [String]
        $LogPath,

        [String]
        $WorkingDirectory
    )

    $tempFile = $null
    try {
        if (-not $LogPath) {
            $tempFile = Join-Path -Path $module.Tmpdir -ChildPath "msiexec.log"
            $LogPath = $tempFile
        }

        $cmd = [System.Collections.Generic.List[String]]@("$env:SystemRoot\System32\msiexec.exe")
        $cmd.AddRange([System.Collections.Generic.List[String]]$Actions)
        $cmd.AddRange([System.Collections.Generic.List[String]]@(
            '/L*V', $LogPath, '/qn', '/norestart'
        ))

        $invokeParams = @{
            Module = $Module
            Command = (Argv-ToString -arguments $cmd)
            ReturnCodes = $ReturnCodes
            LogPath = $LogPath
            WorkingDirectory = $WorkingDirectory

            # Msiexec is not a console application but in the case of a fatal error it does still send messages back
            # over the stdout pipe. These messages are UTF-16 encoded so we override the default UTF-8.
            ConsoleOutputEncoding = 'Unicode'
        }
        if ($Arguments) {
            $invokeParams.Command += " $Arguments"
        }
        Invoke-Executable @invokeParams
    } finally {
        if ($tempFile -and (Test-Path -LiteralPath $tempFile)) {
            Remove-Item -LiteralPath $tempFile -Force
        }
    }
}

$providerInfo = [Ordered]@{
    msi = @{
        FileSupported = {
            param ([String]$Path)

            [Ansible.WInPackage.MsiHelper]::IsMsi($Path)
        }

        Test = {
            param ([String]$Path, [String]$Id)

            if ($Path) {
                $msiHandle = [Ansible.WinPackage.MsiHelper]::OpenPackage($Path)
                try {
                    $Id = [Ansible.WinPackage.MsiHelper]::GetProperty($msiHandle, 'ProductCode')
                } finally {
                    $msiHandle.Dispose()
                }
            }

            $installState = [Ansible.WinPackage.MsiHelper]::QueryProductState($Id)

            @{
                Provider = 'msi'
                Id = $Id
                Installed = $installState -eq [Ansible.WinPackage.InstallState]::Default
                SkipFileForRemove = $true
            }
        }

        Set = {
            param (
                [String]
                $Arguments,

                [Int32[]]
                $ReturnCodes,

                [String]
                $Id,

                [String]
                $LogPath,

                [Object]
                $Module,

                [String]
                $Path,

                [String]
                $State,

                [String]
                $WorkingDirectory
            )

            if ($state -eq 'present') {
                $actions = @('/i', $Path)

                # $Module.Tmpdir only gives rights to the current user but msiexec (as SYSTEM) needs access.
                Add-SystemReadAce -Path $Path
            } else {
                $actions = @('/x', $Id)
            }

            $invokeParams = @{
                Module = $Module
                Actions = $actions
                Arguments = $Arguments
                ReturnCodes = $ReturnCodes
                LogPath = $LogPath
                WorkingDirectory = $WorkingDirectory
            }
            Invoke-Msiexec @invokeParams
        }
    }

    msix = @{
        FileSupported = {
            param ([String]$Path)

            $extension = [System.IO.Path]::GetExtension($Path)

            $extension -in @('.appx', '.appxbundle', '.msix', '.msixbundle')
        }

        Test = {
            param ([String]$Path, [String]$Id)

            $package = $null

            if ($Path) {
                # Cannot find a native way to get the package info from the actual path so we need to inspect the XML
                # manually.
                $null = Add-Type -AssemblyName System.IO.Compression
                $null = Add-Type -AssemblyName System.IO.Compression.FileSystem

                $archive = [System.IO.Compression.ZipFile]::Open($Path, [System.IO.Compression.ZipArchiveMode]::Read,
                    [System.Text.Encoding]::UTF8)
                try {
                    $manifestEntry = $archive.Entries | Where-Object {
                        $_.FullName -in @('AppxManifest.xml', 'AppxMetadata/AppxBundleManifest.xml')
                    }
                    $manifestStream = New-Object -TypeName System.IO.StreamReader -ArgumentList $manifestEntry.Open()
                    try {
                        $manifest = [xml]$manifestStream.ReadToEnd()
                    } finally {
                        $manifestStream.Dispose()
                    }
                } finally {
                    $archive.Dispose()
                }

                if ($manifestEntry.Name -eq 'AppxBundleManifest.xml') {
                    # https://docs.microsoft.com/en-us/uwp/schemas/bundlemanifestschema/element-identity
                    $name = $manifest.Bundle.Identity.Name
                    $publisher = $manifest.Bundle.Identity.Publisher

                    $Ids = foreach ($p in $manifest.Bundle.Packages.Package) {
                        $version = $p.Version

                        $architecture = 'neutral'
                        if ($p.HasAttribute('Architecture')) {
                            $architecture = $p.Architecture
                        }

                        $resourceId = ''
                        if ($p.HasAttribute('ResourceId')) {
                            $resourceId = $p.ResourceId
                        }

                        [Ansible.WinPackage.MsixHelper]::GetPackageFullName($name, $version, $publisher, $architecture,
                            $resourceId)
                    }
                } else {
                    # https://docs.microsoft.com/en-us/uwp/schemas/appxpackage/uapmanifestschema/element-identity
                    $name = $manifest.Package.Identity.Name
                    $version = $manifest.Package.Identity.Version
                    $publisher = $manifest.Package.Identity.Publisher

                    $architecture = 'neutral'
                    if ($manifest.Package.Identity.HasAttribute('ProcessorArchitecture')) {
                        $architecture = $manifest.Package.Identity.ProcessorArchitecture
                    }

                    $resourceId = ''
                    if ($manifest.Package.Identity.HasAttribute('ResourceId')) {
                        $resourceId = $manifest.$identityParent.Identity.ResourceId
                    }

                    $Ids = @(,[Ansible.WinPackage.MsixHelper]::GetPackageFullName($name, $version, $publisher,
                        $architecture, $resourceId)
                    )
                }
            } else {
                $package = Get-AppxPackage -Name $Id -ErrorAction SilentlyContinue
                $Ids = @($Id)
            }

            # In the case when a file is specified or the user has set the full name and not the name, scan again for
            # PackageFullName.
            if ($null -eq $package) {
                $package = Get-AppxPackage | Where-Object { $_.PackageFullName -in $Ids }
            }

            # Make sure the Id is set to the PackageFullName so state=absent works.
            if ($package) {
                $Id = $package.PackageFullName
            }

            @{
                Provider = 'msix'
                Id = $Id
                Installed = $null -ne $package
            }
        }

        Set = {
            param (
                [String]
                $Id,

                [Object]
                $Module,

                [String]
                $Path,

                [String]
                $State
            )
            $originalProgress = $ProgressPreference
            try {
                $ProgressPreference = 'SilentlyContinue'
                if ($State -eq 'present') {
                    # Add-AppxPackage does not support a -LiteralPath parameter and it chokes on wildcard characters.
                    # We need to escape those characters when calling the cmdlet.
                    Add-AppxPackage -Path ([WildcardPattern]::Escape($Path))
                } else {
                    Remove-AppxPackage -Package $Id
                }
            } catch {
                # Replicate the same return values as the other providers.
                $module.Result.rc = $_.Exception.HResult
                $module.Result.stdout = ""
                $module.Result.stderr = $_.Exception.Message

                $msg = "unexpected status from $($_.InvocationInfo.InvocationName): see rc and stderr for more details"
                $module.FailJson($msg, $_)
            } finally {
                $ProgressPreference = $originalProgress
            }

            # Just set to 0 to align with other providers
            $module.Result.rc = 0

            # It looks like the reboot checks are an insider feature so we can't do a check for that today.
            # https://docs.microsoft.com/en-us/windows/msix/packaging-tool/support-restart
        }
    }

    msp = @{
        FileSupported = {
            param ([String]$Path)

            [Ansible.WInPackage.MsiHelper]::IsMsp($Path)
        }

        Test = {
            param ([String]$Path, [String]$Id)

            $productCodes = [System.Collections.Generic.List[System.String]]@()
            if ($Path) {
                $summaryInfo = [Ansible.WinPackage.MsiHelper]::GetSummaryHandle($Path)
                try {
                    $productCodesRaw = [Ansible.WinPackage.MsiHelper]::GetSummaryPropertyString(
                        $summaryInfo, [Ansible.WinPackage.MsiHelper]::SUMMARY_PID_TEMPLATE
                    )

                    # Filter out product codes that are not installed on the host.
                    foreach ($code in ($productCodesRaw -split ';')) {
                        $productState = [Ansible.WinPackage.MsiHelper]::QueryProductState($code)
                        if ($productState -eq [Ansible.WinPackage.InstallState]::Default) {
                            $productCodes.Add($code)
                        }
                    }

                    if ($productCodes.Count -eq 0) {
                        throw "The specified patch does not apply to any installed MSI packages."
                    }

                    # The first guid in the REVNUMBER is the patch code, the subsequent values are obsoleted patches
                    # which we don't care about.
                    $Id = [Ansible.WinPackage.MsiHelper]::GetSummaryPropertyString($summaryInfo,
                        [Ansible.WinPackage.MsiHelper]::SUMMARY_PID_REVNUMBER).Substring(0, 38)
                } finally {
                    $summaryInfo.Dispose()
                }
            } else {
                foreach ($patch in ([Ansible.WinPackage.MsiHelper]::EnumPatches($null, $null, 'All', 'All'))) {
                    if ($patch.PatchCode -eq $Id) {
                        # We append "{guid}:{context}" so the check below checks the proper context, the context
                        # is then stripped out there.
                        $ProductCodes.Add("$($patch.ProductCode):$($patch.Context)")
                    }
                }
            }

            # Filter the product list even further to only ones that are applied and not obsolete.
            $skipCodes = [System.Collections.Generic.List[System.String]]@()
            $productCodes = @(@(foreach ($product in $productCodes) {
                if ($product.Length -eq 38) {  # Guid length with braces is 38
                    $contextList = @('UserManaged', 'UserUnmanaged', 'Machine')
                } else {
                    # We already know the context and was appended to the product guid with ';context'
                    $productInfo = $product.Split(':', 2)
                    $product = $productInfo[0]
                    $contextList = @($productInfo[1])
                }

                foreach ($context in $contextList) {
                    try {
                        # GetPatchInfo('State') returns a string that is a number of an enum value.
                        $state = [Ansible.WinPackage.PatchState][UInt32]([Ansible.WinPackage.MsiHelper]::GetPatchInfo(
                            $Id, $product, $null, $context, 'State'
                        ))
                    } catch [System.ComponentModel.Win32Exception] {
                        if ($_.Exception.NativeErrorCode -in @(0x00000645, 0x0000066F)) {
                            # ERROR_UNKNOWN_PRODUCT can be raised if the product is not installed in the context
                            # specified, just try the next one.
                            # ERROR_UNKNOWN_PATCH can be raised if the patch is not installed but the product is.
                            continue
                        }
                        throw
                    }

                    if ($state -eq [Ansible.WinPackage.PatchState]::Applied) {
                        # The patch is applied to the product code, output the code for the outer list to capture.
                        $product
                    } elseif ($state.ToString() -in @('Obsoleted', 'Superseded')) {
                        # If the patch is obsoleted or suprseded we cannot install or remove but consider it equal to
                        # state=absent and present so we skip the set step.
                        $skipCodes.Add($product)
                    }
                }
            }) | Select-Object -Unique)

            @{
                Provider = 'msp'
                Id = $Id
                Installed = $productCodes.Length -gt 0
                Skip = $skipCodes.Length -eq $productCodes.Length
                SkipFileForRemove = $true
                ExtraInfo = @{
                    ProductCodes = $productCodes
                }
            }
        }

        Set = {
            param (
                [String]
                $Arguments,

                [Int32[]]
                $ReturnCodes,

                [String]
                $Id,

                [String]
                $LogPath,

                [Object]
                $Module,

                [String]
                $Path,

                [String]
                $State,

                [String]
                $WorkingDirectory,

                [String[]]
                $ProductCodes
            )

            $tempLink = $null
            try {
                $actions = @(if ($state -eq 'present') {
                    # $Module.Tmpdir only gives rights to the current user but msiexec (as SYSTEM) needs access.
                    Add-SystemReadAce -Path $Path

                    # MsiApplyPatchW fails if the path contains a ';', we need to use a temporary symlink instead.
                    # https://docs.microsoft.com/en-us/windows/win32/api/msi/nf-msi-msiapplypatchw
                    if ($Path.Contains(';')) {
                        $tempLink = Join-Path -Path $env:TEMP -ChildPath "win_package-$([System.IO.Path]::GetRandomFileName()).msp"
                        $res = Run-Command -command (Argv-ToString -arguments @("cmd.exe", "/c", "mklink", $tempLink, $Path))
                        if ($res.rc -ne 0) {
                            $Module.Result.rc = $res.rc
                            $Module.Result.stdout = $res.stdout
                            $Module.Result.stderr = $res.stderr

                            $Module.FailJson("Failed to create temporary symlink '$tempLink' -> '$Path' for msiexec patch install as path contains semicolon")
                        }
                        $Path = $tempLink
                    }

                    ,@('/update', $Path)
                } else {
                    foreach ($code in $ProductCodes) {
                        ,@('/uninstall', $Id, '/package', $code)
                    }
                })

                $invokeParams = @{
                    Arguments = $Arguments
                    Module = $Module
                    ReturnCodes = $ReturnCodes
                    LogPath = $LogPath
                    WorkingDirectory = $WorkingDirectory
                }
                foreach ($action in $actions) {
                    Invoke-Msiexec -Actions $action @invokeParams
                }
            } finally {
                if ($tempLink -and (Test-Path -LiteralPath $tempLink)) {
                    Remove-Item -LiteralPath $tempLink -Force
                }
            }
        }
    }

    # Should always be last as the FileSupported is a catch all.
    registry = @{
        FileSupported = { $true }

        Test = {
            param ([String]$Id)

            $status = @{
                Provider = 'registry'
                Id = $Id
                Installed = $false
                ExtraInfo = @{
                    RegistryPath = $null
                }
            }

            if ($Id) {
                :regLoop foreach ($hive in @("HKLM", "HKCU")) {  # Search machine wide and user specific.
                    foreach ($key in @("SOFTWARE", "SOFTWARE\Wow6432Node")) {  # Search the 32 and 64-bit locations.
                        $regPath = "$($hive):\$key\Microsoft\Windows\CurrentVersion\Uninstall\$Id"
                        if (Test-Path -LiteralPath $regPath) {
                            $status.Installed = $true
                            $status.ExtraInfo.RegistryPath = $regPath
                            break regLoop
                        }
                    }
                }
            }

            $status
        }

        Set = {
            param (
                [String]
                $Arguments,

                [Int32[]]
                $ReturnCodes,

                [Object]
                $Module,

                [String]
                $Path,

                [String]
                $State,

                [String]
                $WorkingDirectory,

                [String]
                $RegistryPath
            )

            $invokeParams = @{
                Module = $Module
                ReturnCodes = $ReturnCodes
                WorkingDirectory = $WorkingDirectory
            }

            if ($Path) {
                $invokeParams.Command = Argv-ToString -arguments @($Path)
            } else {
                $registryProperties = Get-ItemProperty -LiteralPath $RegistryPath

                if ('QuietUninstallString' -in $registryProperties.PSObject.Properties.Name) {
                    $command = $registryProperties.QuietUninstallString
                } elseif ('UninstallString' -in $registryProperties.PSObject.Properties.Name) {
                    $command = $registryProperties.UninstallString
                } else {
                    $module.FailJson("Failed to find registry uninstall string at registry path '$RegistryPath'")
                }

                # If the uninstall string starts with '%', we need to expand the env vars.
                if ($command.StartsWith('%') -or $command.StartsWith('"%')) {
                    $command = [System.Environment]::ExpandEnvironmentVariables($command)
                }

                # If the command is not quoted and contains spaces we need to see if it needs to be manually quoted for the executable.
                if (-not $command.StartsWith('"') -and $command.Contains(' ')) {
                    $rawArguments = [System.Collections.Generic.List[String]]@()

                    $executable = New-Object -TypeName System.Text.StringBuilder
                    foreach ($cmd in ([Ansible.Process.ProcessUtil]::ParseCommandLine($command))) {
                        if ($rawArguments.Count -eq 0) {
                            # Still haven't found the path, append the arg to the executable path and see if it exists.
                            $null = $executable.Append($cmd)
                            $exe = $executable.ToString()
                            if (Test-Path -LiteralPath $exe -PathType Leaf) {
                                $rawArguments.Add($exe)
                            } else {
                                $null = $executable.Append(" ")  # The arg had a space and we need to preserve that.
                            }
                        } else {
                            $rawArguments.Add($cmd)
                        }
                    }

                    # If we still couldn't find a file just use the command literally and hope WIndows can handle it,
                    # otherwise recombind the args which will also quote whatever is needed.
                    if ($rawArguments.Count -gt 0) {
                        $command = Argv-ToString -arguments $rawArguments
                    }
                }

                $invokeParams.Command = $command
            }

            if ($Arguments) {
                $invokeParams.Command += " $Arguments"
            }

            Invoke-Executable @invokeParams
        }
    }
}

$spec = @{
    options = @{
        arguments = @{ type = "raw" }
        expected_return_code = @{ type = "list"; elements = "int"; default = @(0, 3010) }
        path = @{ type = "str"}
        chdir = @{ type = "path" }
        product_id = @{
            type = "str"
            aliases = @("productid")
            deprecated_aliases = @(
                @{ name = "productid"; version = "2.14" }
            )
        }
        state = @{
            type = "str"
            default = "present"
            choices = "absent", "present"
            aliases = @(,"ensure")
            deprecated_aliases = @(
                ,@{ name = "ensure"; version = "2.14" }
            )
        }
        username = @{ type = "str"; aliases = @(,"user_name"); removed_in_version = "2.14" }
        password = @{ type = "str"; no_log = $true; aliases = @(,"user_password"); removed_in_version = "2.14" }
        creates_path = @{ type = "path" }
        creates_version = @{ type = "str" }
        creates_service = @{ type = "str" }
        log_path = @{ type = "path" }
        provider = @{ type = "str"; default = "auto"; choices = $providerInfo.Keys + "auto" }
    }
    required_by = @{
        creates_version = "creates_path"
    }
    required_if = @(
        @("state", "present", @("path")),
        @("state", "absent", @("path", "product_id"), $true)
    )
    required_together = @(,@("username", "password"))
    supports_check_mode = $true
}
$spec = Merge-WebRequestSpec -ModuleSpec $spec

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$arguments = $module.Params.arguments
$expectedReturnCode = $module.Params.expected_return_code
$path = $module.Params.path
$chdir = $module.Params.chdir
$productId = $module.Params.product_id
$state = $module.Params.state
$username = $module.Params.username
$password = $module.Params.password
$createsPath = $module.Params.creates_path
$createsVersion = $module.Params.creates_version
$createsService = $module.Params.creates_service
$logPath = $module.Params.log_path
$provider = $module.Params.provider

$module.Result.reboot_required = $false

if ($null -ne $arguments) {
    # convert a list to a string and escape the values
    if ($arguments -is [array]) {
        $arguments = Argv-ToString -arguments $arguments
    }
}

$credential = $null
if ($null -ne $username) {
    $secPassword = ConvertTo-SecureString -String $password -AsPlainText -Force
    $credential = New-Object -TypeName PSCredential -ArgumentList $username, $secPassword
}

# This must be set after the module spec so the validate-modules sanity-test can get the arg spec.
Import-PInvokeCode -Module $module

$pathType = $null
if ($path -and $path.StartsWith('http', [System.StringComparison]::InvariantCultureIgnoreCase)) {
    $pathType = 'url'
} elseif ($path -and ($path.StartsWith('\\') -or $path.StartsWith('//') -and $username)) {
    $pathType = 'unc'
}

$tempFile = $null
try {
    $getParams = @{
        Id = $productId
        Provider = $provider
        CreatesPath = $createsPath
        CreatesVersion = $createsVersion
        CreatesService = $createsService
    }

    # If the path is a URL or UNC with credentials and no ID is set then create a temp copy for idempotency checks.
    if ($pathType -and -not $Id) {
        $tempFile = switch ($pathType) {
            url { Get-UrlFile -Module $module -Url $path }
            unc { Copy-ItemWithCredential -Path $path -Destination $module.Tmpdir -Credential $credential }
        }
        $path = $tempFile
        $getParams.Path = $path
    } elseif ($path -and -not $pathType) {
        if (-not (Test-Path -LiteralPath $path)) {
            $module.FailJson("the file at the path '$path' cannot be reached")
        }
        $getParams.Path = $path
    }

    $packageStatus = Get-InstalledStatus @getParams

    $changed = -not $packageStatus.Skip -and (($state -eq 'present') -ne $packageStatus.Installed)
    $module.Result.rc = 0  # Make sure rc is always set
    if ($changed -and -not $module.CheckMode) {
        # Make sure we get a temp copy of the file if the provider requires it and we haven't already done so.
        if ($pathType -and -not $tempFile -and ($state -eq 'present' -or -not $packageStatus.SkipFileForRemove)) {
            $tempFile = switch ($pathType) {
                url { Get-UrlFile -Module $module -Url $path }
                unc { Copy-ItemWithCredential -Path $path -Destination $module.Tmpdir -Credential $credential }
            }
            $path = $tempFile
        }

        $setParams = @{
            Arguments = $arguments
            ReturnCodes = $expectedReturnCode
            Id = $packageStatus.Id
            LogPath = $logPath
            Module = $module
            Path = $path
            State = $state
            WorkingDirectory = $chdir
        }
        $setParams += $packageStatus.ExtraInfo
        &$providerInfo."$($packageStatus.Provider)".Set @setParams
    }
    $module.Result.changed = $changed
} finally {
    if ($tempFile -and (Test-Path -LiteralPath $tempFile)) {
        Remove-Item -LiteralPath $tempFile -Force
    }
}

$module.ExitJson()
