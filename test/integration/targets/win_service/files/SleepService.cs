using System.ComponentModel;
using System.Diagnostics;
using System.Management;
using System.ServiceProcess;

namespace SleepService
{
    public class SleepService : ServiceBase
    {
        private IContainer components = null;
        private string[] serviceArgs;
        private string displayName;

        public SleepService(string[] args)
        {
            CanPauseAndContinue = true;
            CanShutdown = true;
            CanStop = true;
            AutoLog = false;
            serviceArgs = args;
            InitializeComponent();

            string eventSource = "Ansible Test";
            if (!EventLog.SourceExists(eventSource))
                EventLog.CreateEventSource(eventSource, "Application");
            EventLog.Source = eventSource;
            EventLog.Log = "Application";
        }

        private string GetServiceName()
        {
            using (ManagementObjectCollection.ManagementObjectEnumerator enumerator = new ManagementObjectSearcher(string.Format("SELECT * FROM Win32_Service WHERE ProcessId = {0}", (object)Process.GetCurrentProcess().Id)).Get().GetEnumerator())
            {
                if (enumerator.MoveNext())
                    return enumerator.Current["Name"].ToString();
            }
            return ServiceName;
        }

        protected override void OnContinue()
        {
            EventLog.WriteEntry(string.Format("{0} OnContinue", displayName));
        }

        protected override void OnCustomCommand(int command)
        {
            EventLog.WriteEntry(string.Format("{0} OnCustomCommand {1}", displayName, command.ToString()));
        }

        protected override void OnPause()
        {
            EventLog.WriteEntry(string.Format("{0} OnPause", displayName));
        }

        protected override void OnStart(string[] args)
        {
            displayName = this.GetServiceName();
            EventLog.WriteEntry(string.Format("{0} OnStart Args:\n{1}", displayName, string.Join("\n", serviceArgs)));
        }

        protected override void OnShutdown()
        {
            EventLog.WriteEntry(string.Format("{0} OnShutdown", displayName));
        }

        protected override void OnStop()
        {
            EventLog.WriteEntry(string.Format("{0} OnStop", displayName));
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing && components != null)
                components.Dispose();
            base.Dispose(disposing);
        }

        private void InitializeComponent()
        {
            components = new Container();
            ServiceName = nameof(SleepService);
        }
    }
}

