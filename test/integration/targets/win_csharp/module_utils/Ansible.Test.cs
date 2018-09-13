//AssemblyReference -Name System.DirectoryServices.AccountManagement.dll

using System;
using System.DirectoryServices.AccountManagement;

namespace Ansible.Test
{
    public class Principal
    {
        public static string GetCurrentPrincipalSid()
        {
            return UserPrincipal.Current.Sid.Value;
        }
    }
}

