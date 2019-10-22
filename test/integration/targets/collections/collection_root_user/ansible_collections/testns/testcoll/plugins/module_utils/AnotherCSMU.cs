using System;

namespace ansible_collections.testns.testcoll.plugins.module_utils.AnotherCSMU
{
    public class AnotherThing
    {
        public static string CallMe()
        {
            return "Hello from nested user-collection-hosted AnotherCSMU";
        }
    }
}
