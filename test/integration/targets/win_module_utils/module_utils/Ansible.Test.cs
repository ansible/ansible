//AssemblyReference -Name System.Web.Extensions.dll -CLR Framework

using System;
using System.Collections.Generic;
#if CORECLR
using System.Text.Json;
#else
using System.Web.Script.Serialization;
#endif

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
#if CORECLR
            return JsonSerializer.Serialize(obj);
#else
            JavaScriptSerializer jss = new JavaScriptSerializer();
            return jss.Serialize(obj);
#endif
        }
    }
}

