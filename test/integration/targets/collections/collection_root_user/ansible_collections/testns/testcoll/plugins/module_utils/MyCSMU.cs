using System;

using AnsibleCollections.testns.testcoll.AnotherCSMU;

namespace AnsibleCollections.testns.testcoll.MyCSMU
{
    public class CustomThing
    {
        public static string HelloWorld()
        {
            string res = AnotherThing.CallMe();
            return String.Format("Hello from user_mu collection-hosted MyCSMU, also {0}", res);
        }
    }
}