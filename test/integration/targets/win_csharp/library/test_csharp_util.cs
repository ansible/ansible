#!csharp

//AssemblyReference -Name System.Web.Extensions.dll

using System;
using System.Collections.Generic;
using System.Management.Automation;
using System.Management.Automation.Runspaces;
using System.Security.Principal;
using System.Web.Script.Serialization;
using Ansible.Test;

// TODO: swap over to using new Basic wrapper once implemented

namespace Ansible.Module
{
    public class WinCSharp
    {
        public static void Main(string[] args)
        {
            Dictionary<string, object> result = new Dictionary<string, object>();
            result["changed"] = false;
            result["sid"] = Principal.GetCurrentPrincipalSid();
            WriteLine(ToJson(result));
            Exit(0);
        }

        private static void Exit(int rc)
        {
            ScriptBlock.Create("Set-Variable -Name LASTEXITCODE -Value $args[0] -Scope Global; exit $args[0]").Invoke(rc);
        }

        private static void WriteLine(string line)
        {
            ScriptBlock.Create("Set-Variable -Name _ansible_output -Value $args[0] -Scope Global").Invoke(line);
        }

        private static string ToJson(object obj)
        {
            JavaScriptSerializer jss = new JavaScriptSerializer();
            jss.MaxJsonLength = int.MaxValue;
            jss.RecursionLimit = int.MaxValue;
            return jss.Serialize(obj);
        }
    }
}

