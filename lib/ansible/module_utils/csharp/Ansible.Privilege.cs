using Microsoft.Win32.SafeHandles;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;

namespace Ansible.Privilege
{
    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential)]
        public struct LUID
        {
            public UInt32 LowPart;
            public Int32 HighPart;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct LUID_AND_ATTRIBUTES
        {
            public LUID Luid;
            public PrivilegeAttributes Attributes;
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct TOKEN_PRIVILEGES
        {
            public UInt32 PrivilegeCount;
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 1)]
            public LUID_AND_ATTRIBUTES[] Privileges;
        }
    }

    internal class NativeMethods
    {
        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool AdjustTokenPrivileges(
            SafeNativeHandle TokenHandle,
            [MarshalAs(UnmanagedType.Bool)] bool DisableAllPrivileges,
            SafeMemoryBuffer NewState,
            UInt32 BufferLength,
            SafeMemoryBuffer PreviousState,
            out UInt32 ReturnLength);

        [DllImport("kernel32.dll")]
        public static extern bool CloseHandle(
            IntPtr hObject);

        [DllImport("kernel32")]
        public static extern SafeWaitHandle GetCurrentProcess();

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool GetTokenInformation(
            SafeNativeHandle TokenHandle,
            UInt32 TokenInformationClass,
            SafeMemoryBuffer TokenInformation,
            UInt32 TokenInformationLength,
            out UInt32 ReturnLength);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool LookupPrivilegeName(
            string lpSystemName,
            ref NativeHelpers.LUID lpLuid,
            StringBuilder lpName,
            ref UInt32 cchName);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool LookupPrivilegeValue(
            string lpSystemName,
            string lpName,
            out NativeHelpers.LUID lpLuid);

        [DllImport("advapi32.dll", SetLastError = true)]
        public static extern bool OpenProcessToken(
            SafeHandle ProcessHandle,
            TokenAccessLevels DesiredAccess,
            out SafeNativeHandle TokenHandle);
    }

    internal class SafeMemoryBuffer : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeMemoryBuffer() : base(true) { }
        public SafeMemoryBuffer(int cb) : base(true)
        {
            base.SetHandle(Marshal.AllocHGlobal(cb));
        }
        public SafeMemoryBuffer(IntPtr handle) : base(true)
        {
            base.SetHandle(handle);
        }
        protected override bool ReleaseHandle()
        {
            Marshal.FreeHGlobal(handle);
            return true;
        }
    }

    internal class SafeNativeHandle : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeNativeHandle() : base(true) { }
        public SafeNativeHandle(IntPtr handle) : base(true) { this.handle = handle; }

        protected override bool ReleaseHandle()
        {
            return NativeMethods.CloseHandle(handle);
        }
    }

    public class Win32Exception : System.ComponentModel.Win32Exception
    {
        private string _msg;
        public Win32Exception(string message) : this(Marshal.GetLastWin32Error(), message) { }
        public Win32Exception(int errorCode, string message) : base(errorCode)
        {
            _msg = String.Format("{0} ({1}, Win32ErrorCode {2})", message, base.Message, errorCode);
        }
        public override string Message { get { return _msg; } }
        public static explicit operator Win32Exception(string message) { return new Win32Exception(message); }
    }

    [Flags]
    public enum PrivilegeAttributes : uint
    {
        Disabled = 0x00000000,
        EnabledByDefault = 0x00000001,
        Enabled = 0x00000002,
        Removed = 0x00000004,
        UsedForAccess = 0x80000000,
    }

    public class PrivilegeEnabler : IDisposable
    {
        private SafeHandle process;
        private Dictionary<string, bool?> previousState;

        /// <summary>
        /// Temporarily enables the privileges specified and reverts once the class is disposed.
        /// </summary>
        /// <param name="strict">Whether to fail if any privilege failed to be enabled, if false then this will continue silently</param>
        /// <param name="privileges">A list of privileges to enable</param>
        public PrivilegeEnabler(bool strict, params string[] privileges)
        {
            if (privileges.Length > 0)
            {
                process = PrivilegeUtil.GetCurrentProcess();
                Dictionary<string, bool?> newState = new Dictionary<string, bool?>();
                for (int i = 0; i < privileges.Length; i++)
                    newState.Add(privileges[i], true);
                try
                {
                    previousState = PrivilegeUtil.SetTokenPrivileges(process, newState, strict);
                }
                catch (Win32Exception e)
                {
                    throw new Win32Exception(e.NativeErrorCode, String.Format("Failed to enable privilege(s) {0}", String.Join(", ", privileges)));
                }
            }
        }

        public void Dispose()
        {
            // disables any privileges that were enabled by this class
            if (previousState != null)
                PrivilegeUtil.SetTokenPrivileges(process, previousState);
            GC.SuppressFinalize(this);
        }
        ~PrivilegeEnabler() { this.Dispose(); }
    }

    public class PrivilegeUtil
    {
        private static readonly UInt32 TOKEN_PRIVILEGES = 3;

        /// <summary>
        /// Checks if the specific privilege constant is a valid privilege name
        /// </summary>
        /// <param name="name">The privilege constant (Se*Privilege) is valid</param>
        /// <returns>true if valid, else false</returns>
        public static bool CheckPrivilegeName(string name)
        {
            NativeHelpers.LUID luid;
            if (!NativeMethods.LookupPrivilegeValue(null, name, out luid))
            {
                int errCode = Marshal.GetLastWin32Error();
                if (errCode != 1313)  // ERROR_NO_SUCH_PRIVILEGE
                    throw new Win32Exception(errCode, String.Format("LookupPrivilegeValue({0}) failed", name));
                return false;
            }
            else
            {
                return true;
            }
        }

        /// <summary>
        /// Disables the privilege specified
        /// </summary>
        /// <param name="token">The process token to that contains the privilege to disable</param>
        /// <param name="privilege">The privilege constant to disable</param>
        /// <returns>The previous state that can be passed to SetTokenPrivileges to revert the action</returns>
        public static Dictionary<string, bool?> DisablePrivilege(SafeHandle token, string privilege)
        {
            return SetTokenPrivileges(token, new Dictionary<string, bool?>() { { privilege, false } });
        }

        /// <summary>
        /// Disables all the privileges
        /// </summary>
        /// <param name="token">The process token to that contains the privilege to disable</param>
        /// <returns>The previous state that can be passed to SetTokenPrivileges to revert the action</returns>
        public static Dictionary<string, bool?> DisableAllPrivileges(SafeHandle token)
        {
            return AdjustTokenPrivileges(token, null, false);
        }

        /// <summary>
        /// Enables the privilege specified
        /// </summary>
        /// <param name="token">The process token to that contains the privilege to enable</param>
        /// <param name="privilege">The privilege constant to enable</param>
        /// <returns>The previous state that can be passed to SetTokenPrivileges to revert the action</returns>
        public static Dictionary<string, bool?> EnablePrivilege(SafeHandle token, string privilege)
        {
            return SetTokenPrivileges(token, new Dictionary<string, bool?>() { { privilege, true } });
        }

        /// <summary>
        /// Gets the status of all the privileges on the token specified
        /// </summary>
        /// <param name="token">The process token to get the privilege status on</param>
        /// <returns>Dictionary where the key is the privilege constant and the value is the PrivilegeAttributes flags</returns>
        public static Dictionary<String, PrivilegeAttributes> GetAllPrivilegeInfo(SafeHandle token)
        {
            SafeNativeHandle hToken = null;
            if (!NativeMethods.OpenProcessToken(token, TokenAccessLevels.Query, out hToken))
                throw new Win32Exception("OpenProcessToken() failed");

            using (hToken)
            {
                UInt32 tokenLength = 0;
                NativeMethods.GetTokenInformation(hToken, TOKEN_PRIVILEGES, new SafeMemoryBuffer(0), 0, out tokenLength);

                NativeHelpers.LUID_AND_ATTRIBUTES[] privileges;
                using (SafeMemoryBuffer privilegesPtr = new SafeMemoryBuffer((int)tokenLength))
                {
                    if (!NativeMethods.GetTokenInformation(hToken, TOKEN_PRIVILEGES, privilegesPtr, tokenLength, out tokenLength))
                        throw new Win32Exception("GetTokenInformation() for TOKEN_PRIVILEGES failed");

                    NativeHelpers.TOKEN_PRIVILEGES privilegeInfo = (NativeHelpers.TOKEN_PRIVILEGES)Marshal.PtrToStructure(
                        privilegesPtr.DangerousGetHandle(), typeof(NativeHelpers.TOKEN_PRIVILEGES));
                    privileges = new NativeHelpers.LUID_AND_ATTRIBUTES[privilegeInfo.PrivilegeCount];
                    PtrToStructureArray(privileges, IntPtr.Add(privilegesPtr.DangerousGetHandle(), Marshal.SizeOf(privilegeInfo.PrivilegeCount)));
                }

                return privileges.ToDictionary(p => GetPrivilegeName(p.Luid), p => p.Attributes);
            }
        }

        /// <summary>
        /// Get a handle to the current process for use with the methods above
        /// </summary>
        /// <returns>SafeWaitHandle handle of the current process token</returns>
        public static SafeWaitHandle GetCurrentProcess()
        {
            return NativeMethods.GetCurrentProcess();
        }

        /// <summary>
        /// Removes a privilege from the token. This operation is irreversible
        /// </summary>
        /// <param name="token">The process token to that contains the privilege to remove</param>
        /// <param name="privilege">The privilege constant to remove</param>
        public static void RemovePrivilege(SafeHandle token, string privilege)
        {
            SetTokenPrivileges(token, new Dictionary<string, bool?>() { { privilege, null } });
        }

        /// <summary>
        /// Do a bulk set of multiple privileges
        /// </summary>
        /// <param name="token">The process token to use when setting the privilege state</param>
        /// <param name="state">A dictionary that contains the privileges to set, the key is the constant name and the value can be;
        ///     true - enable the privilege
        ///     false - disable the privilege
        ///     null - remove the privilege (this cannot be reversed)
        /// </param>
        /// <param name="strict">When true, will fail if one privilege failed to be set, otherwise it will silently continue</param>
        /// <returns>The previous state that can be passed to SetTokenPrivileges to revert the action</returns>
        public static Dictionary<string, bool?> SetTokenPrivileges(SafeHandle token, IDictionary state, bool strict = true)
        {
            NativeHelpers.LUID_AND_ATTRIBUTES[] privilegeAttr = new NativeHelpers.LUID_AND_ATTRIBUTES[state.Count];
            int i = 0;

            foreach (DictionaryEntry entry in state)
            {
                string key = (string)entry.Key;
                NativeHelpers.LUID luid;
                if (!NativeMethods.LookupPrivilegeValue(null, key, out luid))
                    throw new Win32Exception(String.Format("LookupPrivilegeValue({0}) failed", key));

                PrivilegeAttributes attributes;
                switch ((bool?)entry.Value)
                {
                    case true:
                        attributes = PrivilegeAttributes.Enabled;
                        break;
                    case false:
                        attributes = PrivilegeAttributes.Disabled;
                        break;
                    default:
                        attributes = PrivilegeAttributes.Removed;
                        break;
                }

                privilegeAttr[i].Luid = luid;
                privilegeAttr[i].Attributes = attributes;
                i++;
            }

            return AdjustTokenPrivileges(token, privilegeAttr, strict);
        }

        private static Dictionary<string, bool?> AdjustTokenPrivileges(SafeHandle token, NativeHelpers.LUID_AND_ATTRIBUTES[] newState, bool strict)
        {
            bool disableAllPrivileges;
            SafeMemoryBuffer newStatePtr;
            NativeHelpers.LUID_AND_ATTRIBUTES[] oldStatePrivileges;
            UInt32 returnLength;

            if (newState == null)
            {
                disableAllPrivileges = true;
                newStatePtr = new SafeMemoryBuffer(0);
            }
            else
            {
                disableAllPrivileges = false;

                // Need to manually marshal the bytes requires for newState as the constant size
                // of LUID_AND_ATTRIBUTES is set to 1 and can't be overridden at runtime, TOKEN_PRIVILEGES
                // always contains at least 1 entry so we need to calculate the extra size if there are
                // more than 1 LUID_AND_ATTRIBUTES entry
                int tokenPrivilegesSize = Marshal.SizeOf(typeof(NativeHelpers.TOKEN_PRIVILEGES));
                int luidAttrSize = 0;
                if (newState.Length > 1)
                    luidAttrSize = Marshal.SizeOf(typeof(NativeHelpers.LUID_AND_ATTRIBUTES)) * (newState.Length - 1);
                int totalSize = tokenPrivilegesSize + luidAttrSize;
                byte[] newStateBytes = new byte[totalSize];

                // get the first entry that includes the struct details
                NativeHelpers.TOKEN_PRIVILEGES tokenPrivileges = new NativeHelpers.TOKEN_PRIVILEGES()
                {
                    PrivilegeCount = (UInt32)newState.Length,
                    Privileges = new NativeHelpers.LUID_AND_ATTRIBUTES[1],
                };
                if (newState.Length > 0)
                    tokenPrivileges.Privileges[0] = newState[0];
                int offset = StructureToBytes(tokenPrivileges, newStateBytes, 0);

                // copy the remaining LUID_AND_ATTRIBUTES (if any)
                for (int i = 1; i < newState.Length; i++)
                    offset += StructureToBytes(newState[i], newStateBytes, offset);

                // finally create the pointer to the byte array we just created
                newStatePtr = new SafeMemoryBuffer(newStateBytes.Length);
                Marshal.Copy(newStateBytes, 0, newStatePtr.DangerousGetHandle(), newStateBytes.Length);
            }

            using (newStatePtr)
            {
                SafeNativeHandle hToken;
                if (!NativeMethods.OpenProcessToken(token, TokenAccessLevels.Query | TokenAccessLevels.AdjustPrivileges, out hToken))
                    throw new Win32Exception("OpenProcessToken() failed with Query and AdjustPrivileges");

                using (hToken)
                {
                    if (!NativeMethods.AdjustTokenPrivileges(hToken, disableAllPrivileges, newStatePtr, 0, new SafeMemoryBuffer(0), out returnLength))
                    {
                        int errCode = Marshal.GetLastWin32Error();
                        if (errCode != 122) // ERROR_INSUFFICIENT_BUFFER
                            throw new Win32Exception(errCode, "AdjustTokenPrivileges() failed to get old state size");
                    }

                    using (SafeMemoryBuffer oldStatePtr = new SafeMemoryBuffer((int)returnLength))
                    {
                        bool res = NativeMethods.AdjustTokenPrivileges(hToken, disableAllPrivileges, newStatePtr, returnLength, oldStatePtr, out returnLength);
                        int errCode = Marshal.GetLastWin32Error();

                        // even when res == true, ERROR_NOT_ALL_ASSIGNED may be set as the last error code
                        // fail if we are running with strict, otherwise ignore those privileges
                        if (!res || ((strict && errCode != 0) || (!strict && !(errCode == 0 || errCode == 0x00000514))))
                            throw new Win32Exception(errCode, "AdjustTokenPrivileges() failed");

                        // Marshal the oldStatePtr to the struct
                        NativeHelpers.TOKEN_PRIVILEGES oldState = (NativeHelpers.TOKEN_PRIVILEGES)Marshal.PtrToStructure(
                            oldStatePtr.DangerousGetHandle(), typeof(NativeHelpers.TOKEN_PRIVILEGES));
                        oldStatePrivileges = new NativeHelpers.LUID_AND_ATTRIBUTES[oldState.PrivilegeCount];
                        PtrToStructureArray(oldStatePrivileges, IntPtr.Add(oldStatePtr.DangerousGetHandle(), Marshal.SizeOf(oldState.PrivilegeCount)));
                    }
                }
            }

            return oldStatePrivileges.ToDictionary(p => GetPrivilegeName(p.Luid), p => (bool?)p.Attributes.HasFlag(PrivilegeAttributes.Enabled));
        }

        private static string GetPrivilegeName(NativeHelpers.LUID luid)
        {
            UInt32 nameLen = 0;
            NativeMethods.LookupPrivilegeName(null, ref luid, null, ref nameLen);

            StringBuilder name = new StringBuilder((int)(nameLen + 1));
            if (!NativeMethods.LookupPrivilegeName(null, ref luid, name, ref nameLen))
                throw new Win32Exception("LookupPrivilegeName() failed");

            return name.ToString();
        }

        private static void PtrToStructureArray<T>(T[] array, IntPtr ptr)
        {
            IntPtr ptrOffset = ptr;
            for (int i = 0; i < array.Length; i++, ptrOffset = IntPtr.Add(ptrOffset, Marshal.SizeOf(typeof(T))))
                array[i] = (T)Marshal.PtrToStructure(ptrOffset, typeof(T));
        }

        private static int StructureToBytes<T>(T structure, byte[] array, int offset)
        {
            int size = Marshal.SizeOf(structure);
            using (SafeMemoryBuffer structPtr = new SafeMemoryBuffer(size))
            {
                Marshal.StructureToPtr(structure, structPtr.DangerousGetHandle(), false);
                Marshal.Copy(structPtr.DangerousGetHandle(), array, offset, size);
            }

            return size;
        }
    }
}

