# Copyright (c) 2017 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

$process_util = @"
using Microsoft.Win32.SafeHandles;
using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

namespace Ansible
{
    [StructLayout(LayoutKind.Sequential)]
    public class SECURITY_ATTRIBUTES
    {
        public int nLength;
        public IntPtr lpSecurityDescriptor;
        public bool bInheritHandle = false;
        public SECURITY_ATTRIBUTES()
        {
            nLength = Marshal.SizeOf(this);
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    public class STARTUPINFO
    {
        public Int32 cb;
        public IntPtr lpReserved;
        public IntPtr lpDesktop;
        public IntPtr lpTitle;
        public Int32 dwX;
        public Int32 dwY;
        public Int32 dwXSize;
        public Int32 dwYSize;
        public Int32 dwXCountChars;
        public Int32 dwYCountChars;
        public Int32 dwFillAttribute;
        public Int32 dwFlags;
        public Int16 wShowWindow;
        public Int16 cbReserved2;
        public IntPtr lpReserved2;
        public SafeFileHandle hStdInput;
        public SafeFileHandle hStdOutput;
        public SafeFileHandle hStdError;
        public STARTUPINFO()
        {
            cb = Marshal.SizeOf(this);
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    public class STARTUPINFOEX
    {
        public STARTUPINFO startupInfo;
        public IntPtr lpAttributeList;
        public STARTUPINFOEX()
        {
            startupInfo = new STARTUPINFO();
            startupInfo.cb = Marshal.SizeOf(this);
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION
    {
        public IntPtr hProcess;
        public IntPtr hThread;
        public int dwProcessId;
        public int dwThreadId;
    }

    [Flags]
    public enum StartupInfoFlags : uint
    {
        USESTDHANDLES = 0x00000100
    }

    public enum HandleFlags : uint
    {
        None = 0,
        INHERIT = 1
    }

    class NativeWaitHandle : WaitHandle
    {
        public NativeWaitHandle(IntPtr handle)
        {
            this.SafeWaitHandle = new SafeWaitHandle(handle, false);
        }
    }

    public class Win32Exception : System.ComponentModel.Win32Exception
    {
        private string _msg;

        public Win32Exception(string message) : this(Marshal.GetLastWin32Error(), message) { }

        public Win32Exception(int errorCode, string message) : base(errorCode)
        {
            _msg = String.Format("{0} ({1}, Win32ErrorCode {2})", message, base.Message, errorCode);
        }

        public override string Message { get { return _msg; } }
        public static explicit operator Win32Exception(string message) { return new Win32Exception(message); }
    }

    public class CommandUtil
    {
        private static UInt32 CREATE_UNICODE_ENVIRONMENT = 0x000000400;
        private static UInt32 EXTENDED_STARTUPINFO_PRESENT = 0x00080000;

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode, BestFitMapping = false)]
        public static extern bool CreateProcess(
            [MarshalAs(UnmanagedType.LPWStr)]
                string lpApplicationName,
            StringBuilder lpCommandLine,
            IntPtr lpProcessAttributes,
            IntPtr lpThreadAttributes,
            bool bInheritHandles,
            uint dwCreationFlags,
            IntPtr lpEnvironment,
            [MarshalAs(UnmanagedType.LPWStr)]
                string lpCurrentDirectory,
            STARTUPINFOEX lpStartupInfo,
            out PROCESS_INFORMATION lpProcessInformation);

        [DllImport("kernel32.dll")]
        public static extern bool CreatePipe(
            out SafeFileHandle hReadPipe,
            out SafeFileHandle hWritePipe,
            SECURITY_ATTRIBUTES lpPipeAttributes,
            uint nSize);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool SetHandleInformation(
            SafeFileHandle hObject,
            HandleFlags dwMask,
            int dwFlags);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool GetExitCodeProcess(
            IntPtr hProcess,
            out uint lpExitCode);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
        public static extern uint SearchPath(
            string lpPath,
            string lpFileName,
            string lpExtension,
            int nBufferLength,
            [MarshalAs (UnmanagedType.LPTStr)]
                StringBuilder lpBuffer,
            out IntPtr lpFilePart);

        [DllImport("shell32.dll", SetLastError = true)]
        static extern IntPtr CommandLineToArgvW(
            [MarshalAs(UnmanagedType.LPWStr)]
                string lpCmdLine,
            out int pNumArgs);

        public static string[] ParseCommandLine(string lpCommandLine)
        {
            int numArgs;
            IntPtr ret = CommandLineToArgvW(lpCommandLine, out numArgs);

            if (ret == IntPtr.Zero)
                throw new Win32Exception("Error parsing command line");

            IntPtr[] strptrs = new IntPtr[numArgs];
            Marshal.Copy(ret, strptrs, 0, numArgs);
            string[] cmdlineParts = strptrs.Select(s => Marshal.PtrToStringUni(s)).ToArray();

            Marshal.FreeHGlobal(ret);

            return cmdlineParts;
        }

        public static string SearchPath(string lpFileName)
        {
            StringBuilder sbOut = new StringBuilder(1024);
            IntPtr filePartOut;

            if (SearchPath(null, lpFileName, null, sbOut.Capacity, sbOut, out filePartOut) == 0)
                throw new FileNotFoundException(String.Format("Could not locate the following executable {0}", lpFileName));

            return sbOut.ToString();
        }

        public class CommandResult
        {
            public string StandardOut { get; internal set; }
            public string StandardError { get; internal set; }
            public uint ExitCode { get; internal set; }
        }

        public static CommandResult RunCommand(string lpApplicationName, string lpCommandLine, string lpCurrentDirectory, string stdinInput, IDictionary environment)
        {
            UInt32 startup_flags = CREATE_UNICODE_ENVIRONMENT | EXTENDED_STARTUPINFO_PRESENT;
            STARTUPINFOEX si = new STARTUPINFOEX();
            si.startupInfo.dwFlags = (int)StartupInfoFlags.USESTDHANDLES;

            SECURITY_ATTRIBUTES pipesec = new SECURITY_ATTRIBUTES();
            pipesec.bInheritHandle = true;

            // Create the stdout, stderr and stdin pipes used in the process and add to the startupInfo
            SafeFileHandle stdout_read, stdout_write, stderr_read, stderr_write, stdin_read, stdin_write;
            if (!CreatePipe(out stdout_read, out stdout_write, pipesec, 0))
                throw new Win32Exception("STDOUT pipe setup failed");
            if (!SetHandleInformation(stdout_read, HandleFlags.INHERIT, 0))
                throw new Win32Exception("STDOUT pipe handle setup failed");

            if (!CreatePipe(out stderr_read, out stderr_write, pipesec, 0))
                throw new Win32Exception("STDERR pipe setup failed");
            if (!SetHandleInformation(stderr_read, HandleFlags.INHERIT, 0))
                throw new Win32Exception("STDERR pipe handle setup failed");

            if (!CreatePipe(out stdin_read, out stdin_write, pipesec, 0))
                throw new Win32Exception("STDIN pipe setup failed");
            if (!SetHandleInformation(stdin_write, HandleFlags.INHERIT, 0))
                throw new Win32Exception("STDIN pipe handle setup failed");

            si.startupInfo.hStdOutput = stdout_write;
            si.startupInfo.hStdError = stderr_write;
            si.startupInfo.hStdInput = stdin_read;

            // Setup the stdin buffer
            UTF8Encoding utf8_encoding = new UTF8Encoding(false);
            FileStream stdin_fs = new FileStream(stdin_write, FileAccess.Write, 32768);
            StreamWriter stdin = new StreamWriter(stdin_fs, utf8_encoding, 32768);

            // If lpCurrentDirectory is set to null in PS it will be an empty
            // string here, we need to convert it
            if (lpCurrentDirectory == "")
                lpCurrentDirectory = null;

            StringBuilder environmentString = null;

            if (environment != null && environment.Count > 0)
            {
                environmentString = new StringBuilder();
                foreach (DictionaryEntry kv in environment)
                    environmentString.AppendFormat("{0}={1}\0", kv.Key, kv.Value);
                environmentString.Append('\0');
            }

            // Create the environment block if set
            IntPtr lpEnvironment = IntPtr.Zero;
            if (environmentString != null)
                lpEnvironment = Marshal.StringToHGlobalUni(environmentString.ToString());

            // Create new process and run
            StringBuilder argument_string = new StringBuilder(lpCommandLine);
            PROCESS_INFORMATION pi = new PROCESS_INFORMATION();
            if (!CreateProcess(
                lpApplicationName,
                argument_string,
                IntPtr.Zero,
                IntPtr.Zero,
                true,
                startup_flags,
                lpEnvironment,
                lpCurrentDirectory,
                si,
                out pi))
            {
                throw new Win32Exception("Failed to create new process");
            }

            // Setup the output buffers and get stdout/stderr
            FileStream stdout_fs = new FileStream(stdout_read, FileAccess.Read, 4096);
            StreamReader stdout = new StreamReader(stdout_fs, utf8_encoding, true, 4096);
            stdout_write.Close();
            FileStream stderr_fs = new FileStream(stderr_read, FileAccess.Read, 4096);
            StreamReader stderr = new StreamReader(stderr_fs, utf8_encoding, true, 4096);
            stderr_write.Close();

            stdin.WriteLine(stdinInput);
            stdin.Close();

            string stdout_str, stderr_str = null;
            GetProcessOutput(stdout, stderr, out stdout_str, out stderr_str);
            uint rc = GetProcessExitCode(pi.hProcess);

            return new CommandResult
            {
                StandardOut = stdout_str,
                StandardError = stderr_str,
                ExitCode = rc
            };
        }

        private static void GetProcessOutput(StreamReader stdoutStream, StreamReader stderrStream, out string stdout, out string stderr)
        {
            var sowait = new EventWaitHandle(false, EventResetMode.ManualReset);
            var sewait = new EventWaitHandle(false, EventResetMode.ManualReset);
            string so = null, se = null;
            ThreadPool.QueueUserWorkItem((s) =>
            {
                so = stdoutStream.ReadToEnd();
                sowait.Set();
            });
            ThreadPool.QueueUserWorkItem((s) =>
            {
                se = stderrStream.ReadToEnd();
                sewait.Set();
            });
            foreach (var wh in new WaitHandle[] { sowait, sewait })
                wh.WaitOne();
            stdout = so;
            stderr = se;
        }

        private static uint GetProcessExitCode(IntPtr processHandle)
        {
            new NativeWaitHandle(processHandle).WaitOne();
            uint exitCode;
            if (!GetExitCodeProcess(processHandle, out exitCode))
                throw new Win32Exception("Error getting process exit code");
            return exitCode;
        }
    }
}
"@

$ErrorActionPreference = 'Stop'

Function Load-CommandUtils {
    # makes the following static functions available
    #   [Ansible.CommandUtil]::ParseCommandLine(string lpCommandLine)
    #   [Ansible.CommandUtil]::SearchPath(string lpFileName)
    #   [Ansible.CommandUtil]::RunCommand(string lpApplicationName, string lpCommandLine, string lpCurrentDirectory, string stdinInput, string environmentBlock)
    #
    # there are also numerous P/Invoke methods that can be called if you are feeling adventurous

    # FUTURE: find a better way to get the _ansible_remote_tmp variable
    $original_tmp = $env:TMP
    $original_temp = $env:TEMP

    $remote_tmp = $original_tmp
    $module_params = Get-Variable -Name complex_args -ErrorAction SilentlyContinue
    if ($module_params) {
        if ($module_params.Value.ContainsKey("_ansible_remote_tmp") ) {
            $remote_tmp = $module_params.Value["_ansible_remote_tmp"]
            $remote_tmp = [System.Environment]::ExpandEnvironmentVariables($remote_tmp)
        }
    }

    $env:TMP = $remote_tmp
    $env:TEMP = $remote_tmp
    Add-Type -TypeDefinition $process_util
    $env:TMP = $original_tmp
    $env:TEMP = $original_temp
}

Function Get-ExecutablePath($executable, $directory) {
    # lpApplicationName requires the full path to a file, we need to find it
    # ourselves.

    # we need to add .exe if it doesn't have an extension already
    if (-not [System.IO.Path]::HasExtension($executable)) {
        $executable = "$($executable).exe"
    }
    $full_path = [System.IO.Path]::GetFullPath($executable)

    if ($full_path -ne $executable -and $directory -ne $null) {
        $file = Get-Item -Path "$directory\$executable" -Force -ErrorAction SilentlyContinue
    } else {
        $file = Get-Item -Path $executable -Force -ErrorAction SilentlyContinue
    }

    if ($file -ne $null) {
        $executable_path = $file.FullName
    } else {
        $executable_path = [Ansible.CommandUtil]::SearchPath($executable)    
    }
    return $executable_path
}

Function Run-Command {
    Param(
        [string]$command, # the full command to run including the executable
        [string]$working_directory = $null, # the working directory to run under, will default to the current dir
        [string]$stdin = $null, # a string to send to the stdin pipe when executing the command
        [hashtable]$environment = @{} # a hashtable of environment values to run the command under, this will replace all the other environment variables with these
    )
    
    # load the C# code we call in this function
    Load-CommandUtils

    # need to validate the working directory if it is set
    if ($working_directory) {
        # validate working directory is a valid path
        if (-not (Test-Path -Path $working_directory)) {
            throw "invalid working directory path '$working_directory'"
        }
    }

    # lpApplicationName needs to be the full path to an executable, we do this
    # by getting the executable as the first arg and then getting the full path
    $arguments = [Ansible.CommandUtil]::ParseCommandLine($command)
    $executable = Get-ExecutablePath -executable $arguments[0] -directory $working_directory

    # run the command and get the results
    $command_result = [Ansible.CommandUtil]::RunCommand($executable, $command, $working_directory, $stdin, $environment)

    return ,@{
        executable = $executable
        stdout = $command_result.StandardOut
        stderr = $command_result.StandardError
        rc = $command_result.ExitCode
    }
}

# this line must stay at the bottom to ensure all defined module parts are exported
Export-ModuleMember -Alias * -Function * -Cmdlet *
