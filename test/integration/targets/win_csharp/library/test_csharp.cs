#!csharp

//AssemblyReference -Name System.Web.Extensions.dll -CLR Framework

using System;
using System.Collections;
using System.Collections.Generic;
using System.Management.Automation;
using System.Management.Automation.Runspaces;
using System.Security.Principal;
#if !CORECLR
using System.Web.Script.Serialization;
#endif

// TODO: swap over to using new Basic wrapper once implemented

namespace Ansible.Module
{
    public class WinCSharp
    {
        public static void Main(string[] args)
        {
            Hashtable input = GetParams();
            Dictionary<string, object> result = new Dictionary<string, object>();
            string action = (string)input["action"];
            result["changed"] = true;
            result["action"] = action;

            SecurityIdentifier sid = WindowsIdentity.GetCurrent().User;
            result["sid"] = sid.ToString();
            result["username"] = ((NTAccount)sid.Translate(typeof(NTAccount))).ToString();

            if (action == "normal")
            {
                result["failed"] = false;
                WriteLine(ToJson(result));
                Exit(0);
            }
            else if (action == "fail")
            {
                result["failed"] = true;
                result["msg"] = "failure";
                WriteLine(ToJson(result));
                Exit(1);
            }
            else if (action == "exception")
                throw new Exception("exception thrown");
            else if (action == "exception_in_function")
                ThrowException();

            result["failed"] = true;
            result["msg"] = "we should never have reached here";
            WriteLine(ToJson(result));
            Exit(1);
        }

        private static void ThrowException()
        {
            throw new ArgumentException("exception in function");
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

        public static Hashtable GetParams()
        {
            PSObject rawArgs = ScriptBlock.Create("$complex_args").Invoke()[0];
            return rawArgs.BaseObject as Hashtable;
        }
    }
}

