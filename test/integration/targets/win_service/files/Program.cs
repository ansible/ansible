using System.ServiceProcess;

namespace SleepService
{
    internal static class Program
    {
        private static void Main(string[] args)
        {
            ServiceBase.Run(new ServiceBase[1]
            {
                (ServiceBase) new SleepService(args)
            });
        }
    }
}

