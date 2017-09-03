using System;
// This has been compiled to an exe and uploaded to S3 bucket for argv test

namespace PrintArgv
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine(string.Join(System.Environment.NewLine, args));
        }
    }
}
