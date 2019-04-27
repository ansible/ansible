#!powershell

# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#AnsibleRequires -CSharpUtil Ansible.Basic
#Requires -Module Ansible.ModuleUtils.AddType

$spec = @{
    options = @{
        name = @{ type = "str"; required = $true }
        type = @{ type = "str"; required = $true; choices = @("domain_password", "domain_certificate", "generic_password", "generic_certificate") }
    }
    supports_check_mode = $true
}

$module = [Ansible.Basic.AnsibleModule]::Create($args, $spec)

$name = $module.Params.name
$type = $module.Params.type

Add-CSharpType -AnsibleModule $module -References @'
using Microsoft.Win32.SafeHandles;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.ConstrainedExecution;
using System.Runtime.InteropServices;
using System.Text;

namespace Ansible.CredentialManager
{
    internal class NativeHelpers
    {
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
        public class CREDENTIAL
        {
            public CredentialFlags Flags;
            public CredentialType Type;
            [MarshalAs(UnmanagedType.LPWStr)] public string TargetName;
            [MarshalAs(UnmanagedType.LPWStr)] public string Comment;
            public FILETIME LastWritten;
            public UInt32 CredentialBlobSize;
            public IntPtr CredentialBlob;
            public CredentialPersist Persist;
            public UInt32 AttributeCount;
            public IntPtr Attributes;
            [MarshalAs(UnmanagedType.LPWStr)] public string TargetAlias;
            [MarshalAs(UnmanagedType.LPWStr)] public string UserName;

            public static explicit operator Credential(CREDENTIAL v)
            {
                byte[] secret = new byte[(int)v.CredentialBlobSize];
                if (v.CredentialBlob != IntPtr.Zero)
                    Marshal.Copy(v.CredentialBlob, secret, 0, secret.Length);

                List<CredentialAttribute> attributes = new List<CredentialAttribute>();
                if (v.AttributeCount > 0)
                {
                    CREDENTIAL_ATTRIBUTE[] rawAttributes = new CREDENTIAL_ATTRIBUTE[v.AttributeCount];
                    Credential.PtrToStructureArray(rawAttributes, v.Attributes);
                    attributes = rawAttributes.Select(x => (CredentialAttribute)x).ToList();
                }

                string userName = v.UserName;
                if (v.Type == CredentialType.DomainCertificate || v.Type == CredentialType.GenericCertificate)
                    userName = Credential.UnmarshalCertificateCredential(userName);

                return new Credential
                {
                    Type = v.Type,
                    TargetName = v.TargetName,
                    Comment = v.Comment,
                    LastWritten = (DateTimeOffset)v.LastWritten,
                    Secret = secret,
                    Persist = v.Persist,
                    Attributes = attributes,
                    TargetAlias = v.TargetAlias,
                    UserName = userName,
                    Loaded = true,
                };
            }
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct CREDENTIAL_ATTRIBUTE
        {
            [MarshalAs(UnmanagedType.LPWStr)] public string Keyword;
            public UInt32 Flags;  // Set to 0 and is reserved
            public UInt32 ValueSize;
            public IntPtr Value;

            public static explicit operator CredentialAttribute(CREDENTIAL_ATTRIBUTE v)
            {
                byte[] value = new byte[v.ValueSize];
                Marshal.Copy(v.Value, value, 0, (int)v.ValueSize);

                return new CredentialAttribute
                {
                    Keyword = v.Keyword,
                    Flags = v.Flags,
                    Value = value,
                };
            }
        }

        [StructLayout(LayoutKind.Sequential)]
        public struct FILETIME
        {
            internal UInt32 dwLowDateTime;
            internal UInt32 dwHighDateTime;

            public static implicit operator long(FILETIME v) { return ((long)v.dwHighDateTime << 32) + v.dwLowDateTime; }
            public static explicit operator DateTimeOffset(FILETIME v) { return DateTimeOffset.FromFileTime(v); }
            public static explicit operator FILETIME(DateTimeOffset v)
            {
                return new FILETIME()
                {
                    dwLowDateTime = (UInt32)v.ToFileTime(),
                    dwHighDateTime = ((UInt32)v.ToFileTime() >> 32),
                };
            }
        }

        [Flags]
        public enum CredentialCreateFlags : uint
        {
            PreserveCredentialBlob = 1,
        }

        [Flags]
        public enum CredentialFlags
        {
            None = 0,
            PromptNow = 2,
            UsernameTarget = 4,
        }

        public enum CredMarshalType : uint
        {
            CertCredential = 1,
            UsernameTargetCredential,
            BinaryBlobCredential,
            UsernameForPackedCredential,
            BinaryBlobForSystem,
        }
    }

    internal class NativeMethods
    {
        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool CredDeleteW(
            [MarshalAs(UnmanagedType.LPWStr)] string TargetName,
            CredentialType Type,
            UInt32 Flags);

        [DllImport("advapi32.dll")]
        public static extern void CredFree(
            IntPtr Buffer);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool CredMarshalCredentialW(
            NativeHelpers.CredMarshalType CredType,
            SafeMemoryBuffer Credential,
            out SafeCredentialBuffer MarshaledCredential);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool CredReadW(
            [MarshalAs(UnmanagedType.LPWStr)] string TargetName,
            CredentialType Type,
            UInt32 Flags,
            out SafeCredentialBuffer Credential);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool CredUnmarshalCredentialW(
            [MarshalAs(UnmanagedType.LPWStr)] string MarshaledCredential,
            out NativeHelpers.CredMarshalType CredType,
            out SafeCredentialBuffer Credential);

        [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern bool CredWriteW(
            NativeHelpers.CREDENTIAL Credential,
            NativeHelpers.CredentialCreateFlags Flags);
    }

    internal class SafeCredentialBuffer : SafeHandleZeroOrMinusOneIsInvalid
    {
        public SafeCredentialBuffer() : base(true) { }

        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            NativeMethods.CredFree(handle);
            return true;
        }
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
        [ReliabilityContract(Consistency.WillNotCorruptState, Cer.MayFail)]
        protected override bool ReleaseHandle()
        {
            Marshal.FreeHGlobal(handle);
            return true;
        }
    }

    public class Win32Exception : System.ComponentModel.Win32Exception
    {
        private string _exception_msg;
        public Win32Exception(string message) : this(Marshal.GetLastWin32Error(), message) { }
        public Win32Exception(int errorCode, string message) : base(errorCode)
        {
            _exception_msg = String.Format("{0} - {1} (Win32 Error Code {2}: 0x{3})", message, base.Message, errorCode, errorCode.ToString("X8"));
        }
        public override string Message { get { return _exception_msg; } }
        public static explicit operator Win32Exception(string message) { return new Win32Exception(message); }
    }

    public enum CredentialPersist
    {
        Session = 1,
        LocalMachine = 2,
        Enterprise = 3,
    }

    public enum CredentialType
    {
        Generic = 1,
        DomainPassword = 2,
        DomainCertificate = 3,
        DomainVisiblePassword = 4,
        GenericCertificate = 5,
        DomainExtended = 6,
        Maximum = 7,
        MaximumEx = 1007,
    }

    public class CredentialAttribute
    {
        public string Keyword;
        public UInt32 Flags;
        public byte[] Value;
    }

    public class Credential
    {
        public CredentialType Type;
        public string TargetName;
        public string Comment;
        public DateTimeOffset LastWritten;
        public byte[] Secret;
        public CredentialPersist Persist;
        public List<CredentialAttribute> Attributes = new List<CredentialAttribute>();
        public string TargetAlias;
        public string UserName;

        // Used to track whether the credential has been loaded into the store or not
        public bool Loaded { get; internal set; }

        public void Delete()
        {
            if (!Loaded)
                return;

            if (!NativeMethods.CredDeleteW(TargetName, Type, 0))
                throw new Win32Exception(String.Format("CredDeleteW({0}) failed", TargetName));
            Loaded = false;
        }

        public void Write(bool preserveExisting)
        {
            string userName = UserName;
            // Convert the certificate thumbprint to the string expected
            if (Type == CredentialType.DomainCertificate || Type == CredentialType.GenericCertificate)
                userName = Credential.MarshalCertificateCredential(userName);

            NativeHelpers.CREDENTIAL credential = new NativeHelpers.CREDENTIAL
            {
                Flags = NativeHelpers.CredentialFlags.None,
                Type = Type,
                TargetName = TargetName,
                Comment = Comment,
                LastWritten = new NativeHelpers.FILETIME(),
                CredentialBlobSize = (UInt32)(Secret == null ? 0 : Secret.Length),
                CredentialBlob = IntPtr.Zero, // Must be allocated and freed outside of this to ensure no memory leaks
                Persist = Persist,
                AttributeCount = (UInt32)(Attributes.Count),
                Attributes = IntPtr.Zero, // Attributes must be allocated and freed outside of this to ensure no memory leaks
                TargetAlias = TargetAlias,
                UserName = userName,
            };

            using (SafeMemoryBuffer credentialBlob = new SafeMemoryBuffer((int)credential.CredentialBlobSize))
            {
                if (Secret != null)
                    Marshal.Copy(Secret, 0, credentialBlob.DangerousGetHandle(), Secret.Length);
                credential.CredentialBlob = credentialBlob.DangerousGetHandle();

                // Store the CREDENTIAL_ATTRIBUTE value in a safe memory buffer and make sure we dispose in all cases
                List<SafeMemoryBuffer> attributeBuffers = new List<SafeMemoryBuffer>();
                try
                {
                    int attributeLength = Attributes.Sum(a => Marshal.SizeOf(typeof(NativeHelpers.CREDENTIAL_ATTRIBUTE)));
                    byte[] attributeBytes = new byte[attributeLength];
                    int offset = 0;
                    foreach (CredentialAttribute attribute in Attributes)
                    {
                        SafeMemoryBuffer attributeBuffer = new SafeMemoryBuffer(attribute.Value.Length);
                        attributeBuffers.Add(attributeBuffer);
                        if (attribute.Value != null)
                            Marshal.Copy(attribute.Value, 0, attributeBuffer.DangerousGetHandle(), attribute.Value.Length);

                        NativeHelpers.CREDENTIAL_ATTRIBUTE credentialAttribute = new NativeHelpers.CREDENTIAL_ATTRIBUTE
                        {
                            Keyword = attribute.Keyword,
                            Flags = attribute.Flags,
                            ValueSize = (UInt32)(attribute.Value == null ? 0 : attribute.Value.Length),
                            Value = attributeBuffer.DangerousGetHandle(),
                        };
                        int attributeStructLength = Marshal.SizeOf(typeof(NativeHelpers.CREDENTIAL_ATTRIBUTE));

                        byte[] attrBytes = new byte[attributeStructLength];
                        using (SafeMemoryBuffer tempBuffer = new SafeMemoryBuffer(attributeStructLength))
                        {
                            Marshal.StructureToPtr(credentialAttribute, tempBuffer.DangerousGetHandle(), false);
                            Marshal.Copy(tempBuffer.DangerousGetHandle(), attrBytes, 0, attributeStructLength);
                        }
                        Buffer.BlockCopy(attrBytes, 0, attributeBytes, offset, attributeStructLength);
                        offset += attributeStructLength;
                    }

                    using (SafeMemoryBuffer attributes = new SafeMemoryBuffer(attributeBytes.Length))
                    {
                        if (attributeBytes.Length != 0)
                            Marshal.Copy(attributeBytes, 0, attributes.DangerousGetHandle(), attributeBytes.Length);
                        credential.Attributes = attributes.DangerousGetHandle();

                        NativeHelpers.CredentialCreateFlags createFlags = 0;
                        if (preserveExisting)
                            createFlags |= NativeHelpers.CredentialCreateFlags.PreserveCredentialBlob;

                        if (!NativeMethods.CredWriteW(credential, createFlags))
                            throw new Win32Exception(String.Format("CredWriteW({0}) failed", TargetName));
                    }
                }
                finally
                {
                    foreach (SafeMemoryBuffer attributeBuffer in attributeBuffers)
                        attributeBuffer.Dispose();
                }
            }
            Loaded = true;
        }

        public static Credential GetCredential(string target, CredentialType type)
        {
            SafeCredentialBuffer buffer;
            if (!NativeMethods.CredReadW(target, type, 0, out buffer))
            {
                int lastErr = Marshal.GetLastWin32Error();

                // Not running with CredSSP or Become so cannot manage the user's credentials
                if (lastErr == 0x00000520) // ERROR_NO_SUCH_LOGON_SESSION
                    throw new InvalidOperationException("Failed to access the user's credential store, run the module with become or CredSSP");
                else if (lastErr == 0x00000490)  // ERROR_NOT_FOUND
                    return null;
                throw new Win32Exception(lastErr, "CredEnumerateW() failed");
            }

            using (buffer)
            {
                NativeHelpers.CREDENTIAL credential = (NativeHelpers.CREDENTIAL)Marshal.PtrToStructure(
                    buffer.DangerousGetHandle(), typeof(NativeHelpers.CREDENTIAL));
                return (Credential)credential;
            }
        }

        public static string MarshalCertificateCredential(string thumbprint)
        {
            // CredWriteW requires the UserName field to be the value of CredMarshalCredentialW() when writting a
            // certificate auth. This converts the UserName property to the format required.

            // While CERT_CREDENTIAL_INFO is the correct structure, we manually marshal the data in order to
            // support different cert hash lengths in the future.
            // https://docs.microsoft.com/en-us/windows/desktop/api/wincred/ns-wincred-_cert_credential_info
            int hexLength = thumbprint.Length;
            byte[] credInfo = new byte[sizeof(UInt32) + (hexLength / 2)];

            // First field is cbSize which is a UInt32 value denoting the size of the total structure
            Array.Copy(BitConverter.GetBytes((UInt32)credInfo.Length), credInfo, sizeof(UInt32));

            // Now copy the byte representation of the thumbprint to the rest of the struct bytes
            for (int i = 0; i < hexLength; i += 2)
                credInfo[sizeof(UInt32) + (i / 2)] = Convert.ToByte(thumbprint.Substring(i, 2), 16);

            IntPtr pCredInfo = Marshal.AllocHGlobal(credInfo.Length);
            Marshal.Copy(credInfo, 0, pCredInfo, credInfo.Length);
            SafeMemoryBuffer pCredential = new SafeMemoryBuffer(pCredInfo);

            NativeHelpers.CredMarshalType marshalType = NativeHelpers.CredMarshalType.CertCredential;
            using (pCredential)
            {
                SafeCredentialBuffer marshaledCredential;
                if (!NativeMethods.CredMarshalCredentialW(marshalType, pCredential, out marshaledCredential))
                    throw new Win32Exception("CredMarshalCredentialW() failed");
                using (marshaledCredential)
                    return Marshal.PtrToStringUni(marshaledCredential.DangerousGetHandle());
            }
        }

        public static string UnmarshalCertificateCredential(string value)
        {
            NativeHelpers.CredMarshalType credType;
            SafeCredentialBuffer pCredInfo;
            if (!NativeMethods.CredUnmarshalCredentialW(value, out credType, out pCredInfo))
                throw new Win32Exception("CredUnmarshalCredentialW() failed");

            using (pCredInfo)
            {
                if (credType != NativeHelpers.CredMarshalType.CertCredential)
                    throw new InvalidOperationException(String.Format("Expected unmarshalled cred type of CertCredential, received {0}", credType));

                byte[] structSizeBytes = new byte[sizeof(UInt32)];
                Marshal.Copy(pCredInfo.DangerousGetHandle(), structSizeBytes, 0, sizeof(UInt32));
                UInt32 structSize = BitConverter.ToUInt32(structSizeBytes, 0);

                byte[] certInfoBytes = new byte[structSize];
                Marshal.Copy(pCredInfo.DangerousGetHandle(), certInfoBytes, 0, certInfoBytes.Length);

                StringBuilder hex = new StringBuilder((certInfoBytes.Length - sizeof(UInt32)) * 2);
                for (int i = 4; i < certInfoBytes.Length; i++)
                    hex.AppendFormat("{0:x2}", certInfoBytes[i]);

                return hex.ToString().ToUpperInvariant();
            }
        }

        internal static void PtrToStructureArray<T>(T[] array, IntPtr ptr)
        {
            IntPtr ptrOffset = ptr;
            for (int i = 0; i < array.Length; i++, ptrOffset = IntPtr.Add(ptrOffset, Marshal.SizeOf(typeof(T))))
                array[i] = (T)Marshal.PtrToStructure(ptrOffset, typeof(T));
        }
    }
}
'@

$type = switch ($type) {
    "domain_password" { [Ansible.CredentialManager.CredentialType]::DomainPassword }
    "domain_certificate" { [Ansible.CredentialManager.CredentialType]::DomainCertificate }
    "generic_password" { [Ansible.CredentialManager.CredentialType]::Generic }
    "generic_certificate" { [Ansible.CredentialManager.CredentialType]::GenericCertificate }
}

$credential = [Ansible.CredentialManager.Credential]::GetCredential($name, $type)
if ($null -ne $credential) {
    $module.Result.exists = $true
    $module.Result.alias = $credential.TargetAlias
    $module.Result.attributes = [System.Collections.ArrayList]@()
    $module.Result.comment = $credential.Comment
    $module.Result.name = $credential.TargetName
    $module.Result.persistence = $credential.Persist.ToString()
    $module.Result.type = $credential.Type.ToString()
    $module.Result.username = $credential.UserName

    if ($null -ne $credential.Secret) {
        $module.Result.secret = [System.Convert]::ToBase64String($credential.Secret)
    } else {
        $module.Result.secret = $null
    }

    foreach ($attribute in $credential.Attributes) {
        $attribute_info = @{
            name = $attribute.Keyword
        }
        if ($null -ne $attribute.Value) {
            $attribute_info.data = [System.Convert]::ToBase64String($attribute.Value)
        } else {
            $attribute_info.data = $null
        }
        $module.Result.attributes.Add($attribute_info) > $null
    }
} else {
    $module.Result.exists = $false
}

$module.ExitJson()

