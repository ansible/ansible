using System;

namespace ansible_collections.testns.testcoll.plugins.module_utils.subpkg.subcs
{
    public class NestedUtil
    {
        public static string HelloWorld()
        {
            string res = "Hello from subpkg.subcs";
            return res;
        }
    }
}
