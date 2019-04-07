//AssemblyReference -Name System.Web.Extensions.dll

using System;
using System.Collections.Generic;
using System.Web.Script.Serialization;

namespace Ansible.Test
{
    public class OutputTest
    {
        public static string GetString()
        {
            Dictionary<string, object> obj = new Dictionary<string, object>();
            obj["a"] = "a";
            obj["b"] = 1;
            return ToJson(obj);
        }

        private static string ToJson(object obj)
        {
            JavaScriptSerializer jss = new JavaScriptSerializer();
            return jss.Serialize(obj);
        }
    }
}

