using Microsoft.Win32.SafeHandles;
using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Management.Automation;
using System.Management.Automation.Runspaces;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
#if CORECLR
using Newtonsoft.Json;
#else
using System.Web.Script.Serialization;
#endif

// Newtonsoft.Json may reference a different System.Runtime version (6.x) than loaded by PowerShell 7.3 (7.x).
// Ignore CS1701 so the code can be compiled when warnings are reported as errors.
//NoWarn -Name CS1701 -CLR Core

// System.Diagnostics.EventLog.dll reference different versioned dlls that are
// loaded in PSCore, ignore CS1702 so the code will ignore this warning
//NoWarn -Name CS1702 -CLR Core

//AssemblyReference -Type Newtonsoft.Json.JsonConvert -CLR Core
//AssemblyReference -Type System.Diagnostics.EventLog -CLR Core
//AssemblyReference -Type System.Security.AccessControl.NativeObjectSecurity -CLR Core
//AssemblyReference -Type System.Security.AccessControl.DirectorySecurity -CLR Core
//AssemblyReference -Type System.Security.Principal.IdentityReference -CLR Core

//AssemblyReference -Name System.Web.Extensions.dll -CLR Framework

namespace Ansible.Basic
{
    public class AnsibleModule
    {
        public delegate void ExitHandler(int rc);
        public static ExitHandler Exit = new ExitHandler(ExitModule);

        public delegate void WriteLineHandler(string line);
        public static WriteLineHandler WriteLine = new WriteLineHandler(WriteLineModule);

        public static bool _DebugArgSpec = false;

        private static List<string> BOOLEANS_TRUE = new List<string>() { "y", "yes", "on", "1", "true", "t", "1.0" };
        private static List<string> BOOLEANS_FALSE = new List<string>() { "n", "no", "off", "0", "false", "f", "0.0" };

        private bool ignoreUnknownOpts = false;
        private string remoteTmp = Path.GetTempPath();
        private string tmpdir = null;
        private HashSet<string> noLogValues = new HashSet<string>();
        private List<string> optionsContext = new List<string>();
        private List<string> warnings = new List<string>();
        private List<Dictionary<string, string>> deprecations = new List<Dictionary<string, string>>();
        private List<string> cleanupFiles = new List<string>();

        private Dictionary<string, string> passVars = new Dictionary<string, string>()
        {
            // null values means no mapping, not used in Ansible.Basic.AnsibleModule
            // keep in sync with python counterpart in lib/ansible/module_utils/common/parameters.py
            { "check_mode", "CheckMode" },
            { "debug", "DebugMode" },
            { "diff", "DiffMode" },
            { "keep_remote_files", "KeepRemoteFiles" },
            { "ignore_unknown_opts", "ignoreUnknownOpts" },
            { "module_name", "ModuleName" },
            { "no_log", "NoLog" },
            { "remote_tmp", "remoteTmp" },
            { "selinux_special_fs", null },
            { "shell_executable", null },
            { "socket", null },
            { "string_conversion_action", null },
            { "syslog_facility", null },
            { "target_log_info", "TargetLogInfo"},
            { "tmpdir", "tmpdir" },
            { "verbosity", "Verbosity" },
            { "version", "AnsibleVersion" },
            { "backup_file_name_template", "BackupFileNameTemplate" },
        };
        private List<string> passBools = new List<string>() { "check_mode", "debug", "diff", "keep_remote_files", "ignore_unknown_opts", "no_log" };
        private List<string> passInts = new List<string>() { "verbosity" };
        private Dictionary<string, List<object>> specDefaults = new Dictionary<string, List<object>>()
        {
            // key - (default, type) - null is freeform
            { "apply_defaults", new List<object>() { false, typeof(bool) } },
            { "aliases", new List<object>() { typeof(List<string>), typeof(List<string>) } },
            { "choices", new List<object>() { typeof(List<object>), typeof(List<object>) } },
            { "default", new List<object>() { null, null } },
            { "deprecated_aliases", new List<object>() { typeof(List<Hashtable>), typeof(List<Hashtable>) } },
            { "elements", new List<object>() { null, null } },
            { "mutually_exclusive", new List<object>() { typeof(List<List<string>>), typeof(List<object>) } },
            { "no_log", new List<object>() { false, typeof(bool) } },
            { "options", new List<object>() { typeof(Hashtable), typeof(Hashtable) } },
            { "removed_in_version", new List<object>() { null, typeof(string) } },
            { "removed_at_date", new List<object>() { null, typeof(DateTime) } },
            { "removed_from_collection", new List<object>() { null, typeof(string) } },
            { "required", new List<object>() { false, typeof(bool) } },
            { "required_by", new List<object>() { typeof(Hashtable), typeof(Hashtable) } },
            { "required_if", new List<object>() { typeof(List<List<object>>), typeof(List<object>) } },
            { "required_one_of", new List<object>() { typeof(List<List<string>>), typeof(List<object>) } },
            { "required_together", new List<object>() { typeof(List<List<string>>), typeof(List<object>) } },
            { "supports_check_mode", new List<object>() { false, typeof(bool) } },
            { "type", new List<object>() { "str", null } },
        };
        private Dictionary<string, Delegate> optionTypes = new Dictionary<string, Delegate>()
        {
            { "bool", new Func<object, bool>(ParseBool) },
            { "dict", new Func<object, Dictionary<string, object>>(ParseDict) },
            { "float", new Func<object, float>(ParseFloat) },
            { "int", new Func<object, int>(ParseInt) },
            { "json", new Func<object, string>(ParseJson) },
            { "list", new Func<object, List<object>>(ParseList) },
            { "path", new Func<object, string>(ParsePath) },
            { "raw", new Func<object, object>(ParseRaw) },
            { "sid", new Func<object, SecurityIdentifier>(ParseSid) },
            { "str", new Func<object, string>(ParseStr) },
        };

        public Dictionary<string, object> Diff = new Dictionary<string, object>();
        public IDictionary Params = null;
        public Dictionary<string, object> Result = new Dictionary<string, object>() { { "changed", false } };

        public bool CheckMode { get; private set; }
        public bool DebugMode { get; private set; }
        public bool DiffMode { get; private set; }
        public bool KeepRemoteFiles { get; private set; }
        public string ModuleName { get; private set; }
        public bool NoLog { get; private set; }
        public string TargetLogInfo { get; private set; }
        public int Verbosity { get; private set; }
        public string AnsibleVersion { get; private set; }
        public string BackupFileNameTemplate { get; private set; }

        public string Tmpdir
        {
            get
            {
                if (tmpdir == null)
                {
#if WINDOWS
                    SecurityIdentifier user = WindowsIdentity.GetCurrent().User;
                    DirectorySecurity dirSecurity = new DirectorySecurity();
                    dirSecurity.SetOwner(user);
                    dirSecurity.SetAccessRuleProtection(true, false);  // disable inheritance rules
                    FileSystemAccessRule ace = new FileSystemAccessRule(user, FileSystemRights.FullControl,
                        InheritanceFlags.ContainerInherit | InheritanceFlags.ObjectInherit,
                        PropagationFlags.None, AccessControlType.Allow);
                    dirSecurity.AddAccessRule(ace);

                    string baseDir = Path.GetFullPath(Environment.ExpandEnvironmentVariables(remoteTmp));
                    if (!Directory.Exists(baseDir))
                    {
                        string failedMsg = null;
                        try
                        {
#if CORECLR
                            DirectoryInfo createdDir = Directory.CreateDirectory(baseDir);
                            FileSystemAclExtensions.SetAccessControl(createdDir, dirSecurity);
#else
                            Directory.CreateDirectory(baseDir, dirSecurity);
#endif
                        }
                        catch (Exception e)
                        {
                            failedMsg = String.Format("Failed to create base tmpdir '{0}': {1}", baseDir, e.Message);
                        }

                        if (failedMsg != null)
                        {
                            string envTmp = Path.GetTempPath();
                            Warn(String.Format("Unable to use '{0}' as temporary directory, falling back to system tmp '{1}': {2}", baseDir, envTmp, failedMsg));
                            baseDir = envTmp;
                        }
                        else
                        {
                            NTAccount currentUser = (NTAccount)user.Translate(typeof(NTAccount));
                            string warnMsg = String.Format("Module remote_tmp {0} did not exist and was created with FullControl to {1}, ", baseDir, currentUser.ToString());
                            warnMsg += "this may cause issues when running as another user. To avoid this, create the remote_tmp dir with the correct permissions manually";
                            Warn(warnMsg);
                        }
                    }

                    string dateTime = DateTime.Now.ToFileTime().ToString();
                    string dirName = String.Format("ansible-moduletmp-{0}-{1}-{2}", dateTime, System.Diagnostics.Process.GetCurrentProcess().Id,
                        new Random().Next(0, int.MaxValue));
                    string newTmpdir = Path.Combine(baseDir, dirName);
#if CORECLR
                    DirectoryInfo tmpdirInfo = Directory.CreateDirectory(newTmpdir);
                    FileSystemAclExtensions.SetAccessControl(tmpdirInfo, dirSecurity);
#else
                    Directory.CreateDirectory(newTmpdir, dirSecurity);
#endif
                    tmpdir = newTmpdir;

                    if (!KeepRemoteFiles)
                        cleanupFiles.Add(tmpdir);
#else
                    throw new NotImplementedException("Tmpdir is only supported on Windows");
#endif
                }
                return tmpdir;
            }
        }

        public AnsibleModule(string[] args, IDictionary argumentSpec, IDictionary[] fragments = null)
        {
            // NoLog is not set yet, we cannot rely on FailJson to sanitize the output
            // Do the minimum amount to get this running before we actually parse the params
            Dictionary<string, string> aliases = new Dictionary<string, string>();
            try
            {
                ValidateArgumentSpec(argumentSpec);

                // Merge the fragments if present into the main arg spec.
                if (fragments != null)
                {
                    foreach (IDictionary fragment in fragments)
                    {
                        ValidateArgumentSpec(fragment);
                        MergeFragmentSpec(argumentSpec, fragment);
                    }
                }

                // Used by ansible-test to retrieve the module argument spec, not designed for public use.
                if (_DebugArgSpec)
                {
                    // Cannot call exit here because it will be caught with the catch (Exception e) below. Instead
                    // just throw a new exception with a specific message and the exception block will handle it.
                    ScriptBlock.Create("Set-Variable -Name ansibleTestArgSpec -Value $args[0] -Scope Global"
                        ).Invoke(argumentSpec);
                    throw new Exception("ansible-test validate-modules check");
                }

                // Now make sure all the metadata keys are set to their defaults, this must be done after we've
                // potentially output the arg spec for ansible-test.
                SetArgumentSpecDefaults(argumentSpec);

                Params = GetParams(args);
                aliases = GetAliases(argumentSpec, Params);
                SetNoLogValues(argumentSpec, Params);
            }
            catch (Exception e)
            {
                if (e.Message == "ansible-test validate-modules check")
                    Exit(0);

                Dictionary<string, object> result = new Dictionary<string, object>
                {
                    { "failed", true },
                    { "msg", String.Format("internal error: {0}", e.Message) },
                    { "exception", e.ToString() }
                };
                WriteLine(ToJson(result));
                Exit(1);
            }

            // Initialise public properties to the defaults before we parse the actual inputs
            CheckMode = false;
            DebugMode = false;
            DiffMode = false;
            KeepRemoteFiles = false;
            ModuleName = "undefined win module";
            TargetLogInfo = "";
            NoLog = (bool)argumentSpec["no_log"];
            Verbosity = 0;
            BackupFileNameTemplate = "";
            AppDomain.CurrentDomain.ProcessExit += CleanupFiles;

            List<string> legalInputs = passVars.Keys.Select(v => "_ansible_" + v).ToList();
            legalInputs.AddRange(((IDictionary)argumentSpec["options"]).Keys.Cast<string>().ToList());
            legalInputs.AddRange(aliases.Keys.Cast<string>().ToList());
            CheckArguments(argumentSpec, Params, legalInputs);

            // Set a Ansible friendly invocation value in the result object
            Dictionary<string, object> invocation = new Dictionary<string, object>() { { "module_args", Params } };
            Result["invocation"] = RemoveNoLogValues(invocation, noLogValues);

            if (!NoLog)
                LogEvent(String.Format("Invoked with:\r\n  {0}", FormatLogData(Params, 2)), sanitise: false);
        }

        public static AnsibleModule Create(string[] args, IDictionary argumentSpec, IDictionary[] fragments = null)
        {
            return new AnsibleModule(args, argumentSpec, fragments);
        }

        public void Debug(string message)
        {
            if (DebugMode)
                LogEvent(String.Format("[DEBUG] {0}", message));
        }

        public void Deprecate(string message, string version)
        {
            Deprecate(message, version, null);
        }

        public void Deprecate(string message, string version, string collectionName)
        {
            deprecations.Add(new Dictionary<string, string>() {
                { "msg", message }, { "version", version }, { "collection_name", collectionName } });
            LogEvent(String.Format("[DEPRECATION WARNING] {0} {1}", message, version));
        }

        public void Deprecate(string message, DateTime date)
        {
            Deprecate(message, date, null);
        }

        public void Deprecate(string message, DateTime date, string collectionName)
        {
            string isoDate = date.ToString("yyyy-MM-dd");
            deprecations.Add(new Dictionary<string, string>() {
                { "msg", message }, { "date", isoDate }, { "collection_name", collectionName } });
            LogEvent(String.Format("[DEPRECATION WARNING] {0} {1}", message, isoDate));
        }

        public void ExitJson()
        {
            CleanupFiles(null, null);
            WriteLine(GetFormattedResults(Result));
            Exit(0);
        }

        public void FailJson(string message) { FailJson(message, null, null); }
        public void FailJson(string message, ErrorRecord psErrorRecord) { FailJson(message, psErrorRecord, null); }
        public void FailJson(string message, Exception exception) { FailJson(message, null, exception); }
        private void FailJson(string message, ErrorRecord psErrorRecord, Exception exception)
        {
            Result["failed"] = true;
            Result["msg"] = RemoveNoLogValues(message, noLogValues);


            if (!Result.ContainsKey("exception") && (Verbosity > 2 || DebugMode))
            {
                if (psErrorRecord != null)
                {
                    string traceback = String.Format("{0}\r\n{1}", psErrorRecord.ToString(), psErrorRecord.InvocationInfo.PositionMessage);
                    traceback += String.Format("\r\n    + CategoryInfo          : {0}", psErrorRecord.CategoryInfo.ToString());
                    traceback += String.Format("\r\n    + FullyQualifiedErrorId : {0}", psErrorRecord.FullyQualifiedErrorId.ToString());
                    traceback += String.Format("\r\n\r\nScriptStackTrace:\r\n{0}", psErrorRecord.ScriptStackTrace);
                    Result["exception"] = traceback;
                }
                else if (exception != null)
                    Result["exception"] = exception.ToString();
            }

            CleanupFiles(null, null);
            WriteLine(GetFormattedResults(Result));
            Exit(1);
        }

        public void LogEvent(string message, EventLogEntryType logEntryType = EventLogEntryType.Information, bool sanitise = true)
        {
            if (NoLog)
                return;

#if WINDOWS
            string logSource = "Ansible";
            bool logSourceExists = false;
            try
            {
                logSourceExists = EventLog.SourceExists(logSource);
            }
            catch (System.Security.SecurityException) { }  // non admin users may not have permission

            if (!logSourceExists)
            {
                try
                {
                    EventLog.CreateEventSource(logSource, "Application");
                }
                catch (System.Security.SecurityException)
                {
                    // Cannot call Warn as that calls LogEvent and we get stuck in a loop
                    warnings.Add(String.Format("Access error when creating EventLog source {0}, logging to the Application source instead", logSource));
                    logSource = "Application";
                }
            }

            if (String.IsNullOrWhiteSpace(TargetLogInfo))
            {
                message = String.Format("{0} - {1}", ModuleName, message);
            }
            else
            {
                message = String.Format("{0} {1} - {2}", ModuleName, TargetLogInfo, message);
            }

            if (sanitise)
            {
                message = (string)RemoveNoLogValues(message, noLogValues);
            }

            using (EventLog eventLog = new EventLog("Application"))
            {
                eventLog.Source = logSource;
                try
                {
                    eventLog.WriteEntry(message, logEntryType, 0);
                }
                catch (System.InvalidOperationException) { }  // Ignore permission errors on the Application event log
                catch (System.Exception e)
                {
                    // Cannot call Warn as that calls LogEvent and we get stuck in a loop
                    warnings.Add(String.Format("Unknown error when creating event log entry: {0}", e.Message));
                }
            }
#else
            // Windows Event Log is only available on Windows
            return;
#endif
        }

        public void Warn(string message)
        {
            warnings.Add(message);
            LogEvent(String.Format("[WARNING] {0}", message), EventLogEntryType.Warning);
        }

        public static object FromJson(string json) { return FromJson<object>(json); }
        public static T FromJson<T>(string json)
        {
#if CORECLR
            return JsonConvert.DeserializeObject<T>(json);
#else
            JavaScriptSerializer jss = new JavaScriptSerializer();
            jss.MaxJsonLength = int.MaxValue;
            jss.RecursionLimit = int.MaxValue;
            return jss.Deserialize<T>(json);
#endif
        }

        public static string ToJson(object obj)
        {
            // Using PowerShell to serialize the JSON is preferable over the native .NET libraries as it handles
            // PS Objects a lot better than the alternatives. In case we are debugging in Visual Studio we have a
            // fallback to the other libraries as we won't be dealing with PowerShell objects there.
            if (Runspace.DefaultRunspace != null)
            {
                PSObject rawOut = ScriptBlock.Create("ConvertTo-Json -InputObject $args[0] -Depth 99 -Compress").Invoke(obj)[0];
                return rawOut.BaseObject as string;
            }
            else
            {
#if CORECLR
                return JsonConvert.SerializeObject(obj);
#else
                JavaScriptSerializer jss = new JavaScriptSerializer();
                jss.MaxJsonLength = int.MaxValue;
                jss.RecursionLimit = int.MaxValue;
                return jss.Serialize(obj);
#endif
            }
        }

        public static IDictionary GetParams(string[] args)
        {
            if (args.Length > 0)
            {
                string inputJson = File.ReadAllText(args[0]);
                Dictionary<string, object> rawParams = FromJson<Dictionary<string, object>>(inputJson);
                if (!rawParams.ContainsKey("ANSIBLE_MODULE_ARGS"))
                    throw new ArgumentException("Module was unable to get ANSIBLE_MODULE_ARGS value from the argument path json");
                return (IDictionary)rawParams["ANSIBLE_MODULE_ARGS"];
            }
            else
            {
                // $complex_args is already a Hashtable, no need to waste time converting to a dictionary
                PSObject rawArgs = ScriptBlock.Create("$complex_args").Invoke()[0];
                return rawArgs.BaseObject as Hashtable;
            }
        }

        public static bool ParseBool(object value)
        {
            if (value.GetType() == typeof(bool))
                return (bool)value;

            List<string> booleans = new List<string>();
            booleans.AddRange(BOOLEANS_TRUE);
            booleans.AddRange(BOOLEANS_FALSE);

            string stringValue = ParseStr(value).ToLowerInvariant().Trim();
            if (BOOLEANS_TRUE.Contains(stringValue))
                return true;
            else if (BOOLEANS_FALSE.Contains(stringValue))
                return false;

            string msg = String.Format("The value '{0}' is not a valid boolean. Valid booleans include: {1}",
                stringValue, String.Join(", ", booleans));
            throw new ArgumentException(msg);
        }

        public static Dictionary<string, object> ParseDict(object value)
        {
            Type valueType = value.GetType();
            if (valueType == typeof(Dictionary<string, object>))
                return (Dictionary<string, object>)value;
            else if (value is IDictionary)
                return ((IDictionary)value).Cast<DictionaryEntry>().ToDictionary(kvp => (string)kvp.Key, kvp => kvp.Value);
            else if (valueType == typeof(string))
            {
                string stringValue = (string)value;
                if (stringValue.StartsWith("{") && stringValue.EndsWith("}"))
                    return FromJson<Dictionary<string, object>>((string)value);
                else if (stringValue.IndexOfAny(new char[1] { '=' }) != -1)
                {
                    List<string> fields = new List<string>();
                    List<char> fieldBuffer = new List<char>();
                    char? inQuote = null;
                    bool inEscape = false;
                    string field;

                    foreach (char c in stringValue.ToCharArray())
                    {
                        if (inEscape)
                        {
                            fieldBuffer.Add(c);
                            inEscape = false;
                        }
                        else if (c == '\\')
                            inEscape = true;
                        else if (inQuote == null && (c == '\'' || c == '"'))
                            inQuote = c;
                        else if (inQuote != null && c == inQuote)
                            inQuote = null;
                        else if (inQuote == null && (c == ',' || c == ' '))
                        {
                            field = String.Join("", fieldBuffer);
                            if (field != "")
                                fields.Add(field);
                            fieldBuffer = new List<char>();
                        }
                        else
                            fieldBuffer.Add(c);
                    }

                    field = String.Join("", fieldBuffer);
                    if (field != "")
                        fields.Add(field);

                    return fields.Distinct().Select(i => i.Split(new[] { '=' }, 2)).ToDictionary(i => i[0], i => i.Length > 1 ? (object)i[1] : null);
                }
                else
                    throw new ArgumentException("string cannot be converted to a dict, must either be a JSON string or in the key=value form");
            }

            throw new ArgumentException(String.Format("{0} cannot be converted to a dict", valueType.FullName));
        }

        public static float ParseFloat(object value)
        {
            if (value.GetType() == typeof(float))
                return (float)value;

            string valueStr = ParseStr(value);
            return float.Parse(valueStr);
        }

        public static int ParseInt(object value)
        {
            Type valueType = value.GetType();
            if (valueType == typeof(int))
                return (int)value;
            else
                return Int32.Parse(ParseStr(value));
        }

        public static string ParseJson(object value)
        {
            // mostly used to ensure a dict is a json string as it may
            // have been converted on the controller side
            Type valueType = value.GetType();
            if (value is IDictionary)
                return ToJson(value);
            else if (valueType == typeof(string))
                return (string)value;
            else
                throw new ArgumentException(String.Format("{0} cannot be converted to json", valueType.FullName));
        }

        public static List<object> ParseList(object value)
        {
            if (value == null)
                return null;

            Type valueType = value.GetType();
            if (valueType.IsGenericType && valueType.GetGenericTypeDefinition() == typeof(List<>))
                return (List<object>)value;
            else if (valueType == typeof(ArrayList))
                return ((ArrayList)value).Cast<object>().ToList();
            else if (valueType.IsArray)
                return ((object[])value).ToList();
            else if (valueType == typeof(string))
                return ((string)value).Split(',').Select(s => s.Trim()).ToList<object>();
            else if (valueType == typeof(int))
                return new List<object>() { value };
            else
                throw new ArgumentException(String.Format("{0} cannot be converted to a list", valueType.FullName));
        }

        public static string ParsePath(object value)
        {
            string stringValue = ParseStr(value);

            // do not validate, expand the env vars if it starts with \\?\ as
            // it is a special path designed for the NT kernel to interpret
            if (stringValue.StartsWith(@"\\?\"))
                return stringValue;

            stringValue = Environment.ExpandEnvironmentVariables(stringValue);
            if (stringValue.IndexOfAny(Path.GetInvalidPathChars()) != -1)
                throw new ArgumentException("string value contains invalid path characters, cannot convert to path");

            // will fire an exception if it contains any invalid chars
            Path.GetFullPath(stringValue);
            return stringValue;
        }

        public static object ParseRaw(object value) { return value; }

        public static SecurityIdentifier ParseSid(object value)
        {
            string stringValue = ParseStr(value);

            try
            {
                return new SecurityIdentifier(stringValue);
            }
            catch (ArgumentException) { }  // ignore failures string may not have been a SID

            NTAccount account = new NTAccount(stringValue);
            return (SecurityIdentifier)account.Translate(typeof(SecurityIdentifier));
        }

        public static string ParseStr(object value) { return value.ToString(); }

        private void ValidateArgumentSpec(IDictionary argumentSpec)
        {
            Dictionary<string, object> changedValues = new Dictionary<string, object>();
            foreach (DictionaryEntry entry in argumentSpec)
            {
                string key = (string)entry.Key;

                // validate the key is a valid argument spec key
                if (!specDefaults.ContainsKey(key))
                {
                    string msg = String.Format("argument spec entry contains an invalid key '{0}', valid keys: {1}",
                        key, String.Join(", ", specDefaults.Keys));
                    throw new ArgumentException(FormatOptionsContext(msg, " - "));
                }

                // ensure the value is casted to the type we expect
                Type optionType = null;
                if (entry.Value != null)
                    optionType = (Type)specDefaults[key][1];
                if (optionType != null)
                {
                    Type actualType = entry.Value.GetType();
                    bool invalid = false;
                    if (optionType.IsGenericType && optionType.GetGenericTypeDefinition() == typeof(List<>))
                    {
                        // verify the actual type is not just a single value of the list type
                        Type entryType = optionType.GetGenericArguments()[0];
                        object[] arrayElementTypes = new object[]
                        {
                            null,  // ArrayList does not have an ElementType
                            entryType,
                            typeof(object),  // Hope the object is actually entryType or it can at least be casted.
                        };

                        bool isArray = entry.Value is IList && arrayElementTypes.Contains(actualType.GetElementType());
                        if (actualType == entryType || isArray)
                        {
                            object rawArray;
                            if (isArray)
                                rawArray = entry.Value;
                            else
                                rawArray = new object[1] { entry.Value };

                            MethodInfo castMethod = typeof(Enumerable).GetMethod("Cast").MakeGenericMethod(entryType);
                            MethodInfo toListMethod = typeof(Enumerable).GetMethod("ToList").MakeGenericMethod(entryType);

                            var enumerable = castMethod.Invoke(null, new object[1] { rawArray });
                            var newList = toListMethod.Invoke(null, new object[1] { enumerable });
                            changedValues.Add(key, newList);
                        }
                        else if (actualType != optionType && !(actualType == typeof(List<object>)))
                            invalid = true;
                    }
                    else
                        invalid = actualType != optionType;

                    if (invalid)
                    {
                        string msg = String.Format("argument spec for '{0}' did not match expected type {1}: actual type {2}",
                            key, optionType.FullName, actualType.FullName);
                        throw new ArgumentException(FormatOptionsContext(msg, " - "));
                    }
                }

                // recursively validate the spec
                if (key == "options" && entry.Value != null)
                {
                    IDictionary optionsSpec = (IDictionary)entry.Value;
                    foreach (DictionaryEntry optionEntry in optionsSpec)
                    {
                        optionsContext.Add((string)optionEntry.Key);
                        IDictionary optionMeta = (IDictionary)optionEntry.Value;
                        ValidateArgumentSpec(optionMeta);
                        optionsContext.RemoveAt(optionsContext.Count - 1);
                    }
                }

                // validate the type and elements key type values are known types
                if (key == "type" || key == "elements" && entry.Value != null)
                {
                    Type valueType = entry.Value.GetType();
                    if (valueType == typeof(string))
                    {
                        string typeValue = (string)entry.Value;
                        if (!optionTypes.ContainsKey(typeValue))
                        {
                            string msg = String.Format("{0} '{1}' is unsupported", key, typeValue);
                            msg = String.Format("{0}. Valid types are: {1}", FormatOptionsContext(msg, " - "), String.Join(", ", optionTypes.Keys));
                            throw new ArgumentException(msg);
                        }
                    }
                    else if (!(entry.Value is Delegate))
                    {
                        string msg = String.Format("{0} must either be a string or delegate, was: {1}", key, valueType.FullName);
                        throw new ArgumentException(FormatOptionsContext(msg, " - "));
                    }
                }
            }

            // Outside of the spec iterator, change the values that were casted above
            foreach (KeyValuePair<string, object> changedValue in changedValues)
                argumentSpec[changedValue.Key] = changedValue.Value;
        }

        private void MergeFragmentSpec(IDictionary argumentSpec, IDictionary fragment)
        {
            foreach (DictionaryEntry fragmentEntry in fragment)
            {
                string fragmentKey = fragmentEntry.Key.ToString();

                if (argumentSpec.Contains(fragmentKey))
                {
                    // We only want to add new list entries and merge dictionary new keys and values. Leave the other
                    // values as is in the argument spec as that takes priority over the fragment.
                    if (fragmentEntry.Value is IDictionary)
                    {
                        MergeFragmentSpec((IDictionary)argumentSpec[fragmentKey], (IDictionary)fragmentEntry.Value);
                    }
                    else if (fragmentEntry.Value is IList)
                    {
                        IList specValue = (IList)argumentSpec[fragmentKey];
                        foreach (object fragmentValue in (IList)fragmentEntry.Value)
                            specValue.Add(fragmentValue);
                    }
                }
                else
                    argumentSpec[fragmentKey] = fragmentEntry.Value;
            }
        }

        private void SetArgumentSpecDefaults(IDictionary argumentSpec)
        {
            foreach (KeyValuePair<string, List<object>> metadataEntry in specDefaults)
            {
                List<object> defaults = metadataEntry.Value;
                object defaultValue = defaults[0];
                if (defaultValue != null && defaultValue.GetType() == typeof(Type).GetType())
                    defaultValue = Activator.CreateInstance((Type)defaultValue);

                if (!argumentSpec.Contains(metadataEntry.Key))
                    argumentSpec[metadataEntry.Key] = defaultValue;
            }

            // Recursively set the defaults for any inner options.
            foreach (DictionaryEntry entry in argumentSpec)
            {
                if (entry.Value == null || entry.Key.ToString() != "options")
                    continue;

                IDictionary optionsSpec = (IDictionary)entry.Value;
                foreach (DictionaryEntry optionEntry in optionsSpec)
                {
                    optionsContext.Add((string)optionEntry.Key);
                    IDictionary optionMeta = (IDictionary)optionEntry.Value;
                    SetArgumentSpecDefaults(optionMeta);
                    optionsContext.RemoveAt(optionsContext.Count - 1);
                }
            }
        }

        private Dictionary<string, string> GetAliases(IDictionary argumentSpec, IDictionary parameters)
        {
            Dictionary<string, string> aliasResults = new Dictionary<string, string>();

            foreach (DictionaryEntry entry in (IDictionary)argumentSpec["options"])
            {
                string k = (string)entry.Key;
                Hashtable v = (Hashtable)entry.Value;

                List<string> aliases = (List<string>)v["aliases"];
                object defaultValue = v["default"];
                bool required = (bool)v["required"];

                if (defaultValue != null && required)
                    throw new ArgumentException(String.Format("required and default are mutually exclusive for {0}", k));

                foreach (string alias in aliases)
                {
                    aliasResults.Add(alias, k);
                    if (parameters.Contains(alias))
                        parameters[k] = parameters[alias];
                }

                List<Hashtable> deprecatedAliases = (List<Hashtable>)v["deprecated_aliases"];
                foreach (Hashtable depInfo in deprecatedAliases)
                {
                    foreach (string keyName in new List<string> { "name" })
                    {
                        if (!depInfo.ContainsKey(keyName))
                        {
                            string msg = String.Format("{0} is required in a deprecated_aliases entry", keyName);
                            throw new ArgumentException(FormatOptionsContext(msg, " - "));
                        }
                    }
                    if (!depInfo.ContainsKey("version") && !depInfo.ContainsKey("date"))
                    {
                        string msg = "One of version or date is required in a deprecated_aliases entry";
                        throw new ArgumentException(FormatOptionsContext(msg, " - "));
                    }
                    if (depInfo.ContainsKey("version") && depInfo.ContainsKey("date"))
                    {
                        string msg = "Only one of version or date is allowed in a deprecated_aliases entry";
                        throw new ArgumentException(FormatOptionsContext(msg, " - "));
                    }
                    if (depInfo.ContainsKey("date") && depInfo["date"].GetType() != typeof(DateTime))
                    {
                        string msg = "A deprecated_aliases date must be a DateTime object";
                        throw new ArgumentException(FormatOptionsContext(msg, " - "));
                    }
                    string collectionName = null;
                    if (depInfo.ContainsKey("collection_name"))
                    {
                        collectionName = (string)depInfo["collection_name"];
                    }
                    string aliasName = (string)depInfo["name"];

                    if (parameters.Contains(aliasName))
                    {
                        string msg = String.Format("Alias '{0}' is deprecated. See the module docs for more information", aliasName);
                        if (depInfo.ContainsKey("version"))
                        {
                            string depVersion = (string)depInfo["version"];
                            Deprecate(FormatOptionsContext(msg, " - "), depVersion, collectionName);
                        }
                        if (depInfo.ContainsKey("date"))
                        {
                            DateTime depDate = (DateTime)depInfo["date"];
                            Deprecate(FormatOptionsContext(msg, " - "), depDate, collectionName);
                        }
                    }
                }
            }

            return aliasResults;
        }

        private void SetNoLogValues(IDictionary argumentSpec, IDictionary parameters)
        {
            foreach (DictionaryEntry entry in (IDictionary)argumentSpec["options"])
            {
                string k = (string)entry.Key;
                Hashtable v = (Hashtable)entry.Value;

                if ((bool)v["no_log"])
                {
                    object noLogObject = parameters.Contains(k) ? parameters[k] : null;
                    string noLogString = noLogObject == null ? "" : noLogObject.ToString();
                    if (!String.IsNullOrEmpty(noLogString))
                        noLogValues.Add(noLogString);
                }
                string collectionName = null;
                if (v.ContainsKey("removed_from_collection"))
                {
                    collectionName = (string)v["removed_from_collection"];
                }

                object removedInVersion = v["removed_in_version"];
                if (removedInVersion != null && parameters.Contains(k))
                    Deprecate(String.Format("Param '{0}' is deprecated. See the module docs for more information", k),
                              removedInVersion.ToString(), collectionName);

                object removedAtDate = v["removed_at_date"];
                if (removedAtDate != null && parameters.Contains(k))
                    Deprecate(String.Format("Param '{0}' is deprecated. See the module docs for more information", k),
                              (DateTime)removedAtDate, collectionName);
            }
        }

        private void CheckArguments(IDictionary spec, IDictionary param, List<string> legalInputs)
        {
            // initially parse the params and check for unsupported ones and set internal vars
            CheckUnsupportedArguments(param, legalInputs);

            // Only run this check if we are at the root argument (optionsContext.Count == 0)
            if (CheckMode && !(bool)spec["supports_check_mode"] && optionsContext.Count == 0)
            {
                Result["skipped"] = true;
                Result["msg"] = String.Format("remote module ({0}) does not support check mode", ModuleName);
                ExitJson();
            }
            IDictionary optionSpec = (IDictionary)spec["options"];

            CheckMutuallyExclusive(param, (IList)spec["mutually_exclusive"]);
            CheckRequiredArguments(optionSpec, param);

            // set the parameter types based on the type spec value
            foreach (DictionaryEntry entry in optionSpec)
            {
                string k = (string)entry.Key;
                Hashtable v = (Hashtable)entry.Value;

                object value = param.Contains(k) ? param[k] : null;
                if (value != null)
                {
                    // convert the current value to the wanted type
                    Delegate typeConverter;
                    string type;
                    if (v["type"].GetType() == typeof(string))
                    {
                        type = (string)v["type"];
                        typeConverter = optionTypes[type];
                    }
                    else
                    {
                        type = "delegate";
                        typeConverter = (Delegate)v["type"];
                    }

                    try
                    {
                        value = typeConverter.DynamicInvoke(value);
                        param[k] = value;
                    }
                    catch (Exception e)
                    {
                        string msg = String.Format("argument for {0} is of type {1} and we were unable to convert to {2}: {3}",
                            k, value.GetType(), type, e.InnerException.Message);
                        FailJson(FormatOptionsContext(msg));
                    }

                    // ensure it matches the choices if there are choices set
                    List<string> choices = ((List<object>)v["choices"]).Select(x => x.ToString()).Cast<string>().ToList();
                    if (choices.Count > 0)
                    {
                        List<string> values;
                        string choiceMsg;
                        if (type == "list")
                        {
                            values = ((List<object>)value).Select(x => x.ToString()).Cast<string>().ToList();
                            choiceMsg = "one or more of";
                        }
                        else
                        {
                            values = new List<string>() { value.ToString() };
                            choiceMsg = "one of";
                        }

                        List<string> diffList = values.Except(choices, StringComparer.OrdinalIgnoreCase).ToList();
                        List<string> caseDiffList = values.Except(choices).ToList();
                        if (diffList.Count > 0)
                        {
                            string msg = String.Format("value of {0} must be {1}: {2}. Got no match for: {3}",
                                                       k, choiceMsg, String.Join(", ", choices), String.Join(", ", diffList));
                            FailJson(FormatOptionsContext(msg));
                        }
                        /*
                        For now we will just silently accept case insensitive choices, uncomment this if we want to add it back in
                        else if (caseDiffList.Count > 0)
                        {
                            // For backwards compatibility with Legacy.psm1 we need to be matching choices that are not case sensitive.
                            // We will warn the user it was case insensitive and tell them this will become case sensitive in the future.
                            string msg = String.Format(
                                "value of {0} was a case insensitive match of {1}: {2}. Checking of choices will be case sensitive in a future Ansible release. Case insensitive matches were: {3}",
                                k, choiceMsg, String.Join(", ", choices), String.Join(", ", caseDiffList.Select(x => RemoveNoLogValues(x, noLogValues)))
                            );
                            Warn(FormatOptionsContext(msg));
                        }*/
                    }
                }
            }

            CheckRequiredTogether(param, (IList)spec["required_together"]);
            CheckRequiredOneOf(param, (IList)spec["required_one_of"]);
            CheckRequiredIf(param, (IList)spec["required_if"]);
            CheckRequiredBy(param, (IDictionary)spec["required_by"]);

            // finally ensure all missing parameters are set to null and handle sub options
            foreach (DictionaryEntry entry in optionSpec)
            {
                string k = (string)entry.Key;
                IDictionary v = (IDictionary)entry.Value;

                if (!param.Contains(k))
                    param[k] = null;

                CheckSubOption(param, k, v);
            }
        }

        private void CheckUnsupportedArguments(IDictionary param, List<string> legalInputs)
        {
            HashSet<string> unsupportedParameters = new HashSet<string>();
            HashSet<string> caseUnsupportedParameters = new HashSet<string>();
            List<string> removedParameters = new List<string>();

            foreach (DictionaryEntry entry in param)
            {
                string paramKey = (string)entry.Key;
                if (paramKey == "_ansible_exec_wrapper_warnings")
                {
                    // Special key used in module_powershell_wrapper to pass
                    // along any warnings that should be returned back to
                    // Ansible.
                    removedParameters.Add(paramKey);
                    foreach (string warning in (IList<string>)entry.Value)
                        Warn(warning);
                }
                else if (!legalInputs.Contains(paramKey, StringComparer.OrdinalIgnoreCase))
                    unsupportedParameters.Add(paramKey);
                else if (!legalInputs.Contains(paramKey))
                    // For backwards compatibility we do not care about the case but we need to warn the users as this will
                    // change in a future Ansible release.
                    caseUnsupportedParameters.Add(paramKey);
                else if (paramKey.StartsWith("_ansible_"))
                {
                    removedParameters.Add(paramKey);
                    string key = paramKey.Replace("_ansible_", "");
                    // skip setting NoLog if NoLog is already set to true (set by the module)
                    // or there's no mapping for this key
                    if ((key == "no_log" && NoLog == true) || (passVars[key] == null))
                        continue;

                    object value = entry.Value;
                    if (passBools.Contains(key))
                        value = ParseBool(value);
                    else if (passInts.Contains(key))
                        value = ParseInt(value);

                    string propertyName = passVars[key];
                    PropertyInfo property = typeof(AnsibleModule).GetProperty(propertyName);
                    FieldInfo field = typeof(AnsibleModule).GetField(propertyName, BindingFlags.NonPublic | BindingFlags.Instance);
                    if (property != null)
                        property.SetValue(this, value, null);
                    else if (field != null)
                        field.SetValue(this, value);
                    else
                        FailJson(String.Format("implementation error: unknown AnsibleModule property {0}", propertyName));
                }
            }
            foreach (string parameter in removedParameters)
                param.Remove(parameter);

            if (unsupportedParameters.Count > 0 && !ignoreUnknownOpts)
            {
                legalInputs.RemoveAll(x => passVars.Keys.Contains(x.Replace("_ansible_", "")));
                string msg = String.Format("Unsupported parameters for ({0}) module: {1}", ModuleName, String.Join(", ", unsupportedParameters));
                msg = String.Format("{0}. Supported parameters include: {1}", FormatOptionsContext(msg), String.Join(", ", legalInputs));
                FailJson(msg);
            }

            /*
            // Uncomment when we want to start warning users around options that are not a case sensitive match to the spec
            if (caseUnsupportedParameters.Count > 0)
            {
                legalInputs.RemoveAll(x => passVars.Keys.Contains(x.Replace("_ansible_", "")));
                string msg = String.Format("Parameters for ({0}) was a case insensitive match: {1}", ModuleName, String.Join(", ", caseUnsupportedParameters));
                msg = String.Format("{0}. Module options will become case sensitive in a future Ansible release. Supported parameters include: {1}",
                    FormatOptionsContext(msg), String.Join(", ", legalInputs));
                Warn(msg);
            }*/

            // Make sure we convert all the incorrect case params to the ones set by the module spec
            foreach (string key in caseUnsupportedParameters)
            {
                string correctKey = legalInputs[legalInputs.FindIndex(s => s.Equals(key, StringComparison.OrdinalIgnoreCase))];
                object value = param[key];
                param.Remove(key);
                param.Add(correctKey, value);
            }
        }

        private void CheckMutuallyExclusive(IDictionary param, IList mutuallyExclusive)
        {
            if (mutuallyExclusive == null)
                return;

            foreach (object check in mutuallyExclusive)
            {
                List<string> mutualCheck = ((IList)check).Cast<string>().ToList();
                int count = 0;
                foreach (string entry in mutualCheck)
                    if (param.Contains(entry))
                        count++;

                if (count > 1)
                {
                    string msg = String.Format("parameters are mutually exclusive: {0}", String.Join(", ", mutualCheck));
                    FailJson(FormatOptionsContext(msg));
                }
            }
        }

        private void CheckRequiredArguments(IDictionary spec, IDictionary param)
        {
            List<string> missing = new List<string>();
            foreach (DictionaryEntry entry in spec)
            {
                string k = (string)entry.Key;
                Hashtable v = (Hashtable)entry.Value;

                // set defaults for values not already set
                object defaultValue = v["default"];
                if (defaultValue != null && !param.Contains(k))
                    param[k] = defaultValue;

                // check required arguments
                bool required = (bool)v["required"];
                if (required && !param.Contains(k))
                    missing.Add(k);
            }
            if (missing.Count > 0)
            {
                string msg = String.Format("missing required arguments: {0}", String.Join(", ", missing));
                FailJson(FormatOptionsContext(msg));
            }
        }

        private void CheckRequiredTogether(IDictionary param, IList requiredTogether)
        {
            if (requiredTogether == null)
                return;

            foreach (object check in requiredTogether)
            {
                List<string> requiredCheck = ((IList)check).Cast<string>().ToList();
                List<bool> found = new List<bool>();
                foreach (string field in requiredCheck)
                    if (param.Contains(field))
                        found.Add(true);
                    else
                        found.Add(false);

                if (found.Contains(true) && found.Contains(false))
                {
                    string msg = String.Format("parameters are required together: {0}", String.Join(", ", requiredCheck));
                    FailJson(FormatOptionsContext(msg));
                }
            }
        }

        private void CheckRequiredOneOf(IDictionary param, IList requiredOneOf)
        {
            if (requiredOneOf == null)
                return;

            foreach (object check in requiredOneOf)
            {
                List<string> requiredCheck = ((IList)check).Cast<string>().ToList();
                int count = 0;
                foreach (string field in requiredCheck)
                    if (param.Contains(field))
                        count++;

                if (count == 0)
                {
                    string msg = String.Format("one of the following is required: {0}", String.Join(", ", requiredCheck));
                    FailJson(FormatOptionsContext(msg));
                }
            }
        }

        private void CheckRequiredIf(IDictionary param, IList requiredIf)
        {
            if (requiredIf == null)
                return;

            foreach (object check in requiredIf)
            {
                IList requiredCheck = (IList)check;
                List<string> missing = new List<string>();
                List<string> missingFields = new List<string>();
                int maxMissingCount = 1;
                bool oneRequired = false;

                if (requiredCheck.Count < 3 && requiredCheck.Count < 4)
                    FailJson(String.Format("internal error: invalid required_if value count of {0}, expecting 3 or 4 entries", requiredCheck.Count));
                else if (requiredCheck.Count == 4)
                    oneRequired = (bool)requiredCheck[3];

                string key = (string)requiredCheck[0];
                object val = requiredCheck[1];
                IList requirements = (IList)requiredCheck[2];

                if (ParseStr(param[key]) != ParseStr(val))
                    continue;

                string term = "all";
                if (oneRequired)
                {
                    maxMissingCount = requirements.Count;
                    term = "any";
                }

                foreach (string required in requirements.Cast<string>())
                    if (!param.Contains(required))
                        missing.Add(required);

                if (missing.Count >= maxMissingCount)
                {
                    string msg = String.Format("{0} is {1} but {2} of the following are missing: {3}",
                        key, val.ToString(), term, String.Join(", ", missing));
                    FailJson(FormatOptionsContext(msg));
                }
            }
        }

        private void CheckRequiredBy(IDictionary param, IDictionary requiredBy)
        {
            foreach (DictionaryEntry entry in requiredBy)
            {
                string key = (string)entry.Key;
                if (!param.Contains(key))
                    continue;

                List<string> missing = new List<string>();
                List<string> requires = ParseList(entry.Value).Cast<string>().ToList();
                foreach (string required in requires)
                    if (!param.Contains(required))
                        missing.Add(required);

                if (missing.Count > 0)
                {
                    string msg = String.Format("missing parameter(s) required by '{0}': {1}", key, String.Join(", ", missing));
                    FailJson(FormatOptionsContext(msg));
                }
            }
        }

        private void CheckSubOption(IDictionary param, string key, IDictionary spec)
        {
            object value = param[key];

            string type;
            if (spec["type"].GetType() == typeof(string))
                type = (string)spec["type"];
            else
                type = "delegate";

            string elements = null;
            Delegate typeConverter = null;
            if (spec["elements"] != null && spec["elements"].GetType() == typeof(string))
            {
                elements = (string)spec["elements"];
                typeConverter = optionTypes[elements];
            }
            else if (spec["elements"] != null)
            {
                elements = "delegate";
                typeConverter = (Delegate)spec["elements"];
            }

            if (!(type == "dict" || (type == "list" && elements != null)))
                // either not a dict, or list with the elements set, so continue
                return;
            else if (type == "list")
            {
                // cast each list element to the type specified
                if (value == null)
                    return;

                List<object> newValue = new List<object>();
                foreach (object element in (List<object>)value)
                {
                    if (elements == "dict")
                        newValue.Add(ParseSubSpec(spec, element, key));
                    else
                    {
                        try
                        {
                            object newElement = typeConverter.DynamicInvoke(element);
                            newValue.Add(newElement);
                        }
                        catch (Exception e)
                        {
                            string msg = String.Format("argument for list entry {0} is of type {1} and we were unable to convert to {2}: {3}",
                                key, element.GetType(), elements, e.Message);
                            FailJson(FormatOptionsContext(msg));
                        }
                    }
                }

                param[key] = newValue;
            }
            else
                param[key] = ParseSubSpec(spec, value, key);
        }

        private object ParseSubSpec(IDictionary spec, object value, string context)
        {
            bool applyDefaults = (bool)spec["apply_defaults"];

            // set entry to an empty dict if apply_defaults is set
            IDictionary optionsSpec = (IDictionary)spec["options"];
            if (applyDefaults && optionsSpec.Keys.Count > 0 && value == null)
                value = new Dictionary<string, object>();
            else if (optionsSpec.Keys.Count == 0 || value == null)
                return value;

            optionsContext.Add(context);
            Dictionary<string, object> newValue = (Dictionary<string, object>)ParseDict(value);
            Dictionary<string, string> aliases = GetAliases(spec, newValue);
            SetNoLogValues(spec, newValue);

            List<string> subLegalInputs = optionsSpec.Keys.Cast<string>().ToList();
            subLegalInputs.AddRange(aliases.Keys.Cast<string>().ToList());

            CheckArguments(spec, newValue, subLegalInputs);
            optionsContext.RemoveAt(optionsContext.Count - 1);
            return newValue;
        }

        private string GetFormattedResults(Dictionary<string, object> result)
        {
            if (!result.ContainsKey("invocation"))
                result["invocation"] = new Dictionary<string, object>() { { "module_args", RemoveNoLogValues(Params, noLogValues) } };

            if (warnings.Count > 0)
                result["warnings"] = warnings;

            if (deprecations.Count > 0)
                result["deprecations"] = deprecations;

            if (Diff.Count > 0 && DiffMode)
                result["diff"] = Diff;

            return ToJson(result);
        }

        private string FormatLogData(object data, int indentLevel)
        {
            if (data == null)
                return "$null";

            string msg = "";
            if (data is IList)
            {
                string newMsg = "";
                foreach (object value in (IList)data)
                {
                    string entryValue = FormatLogData(value, indentLevel + 2);
                    newMsg += String.Format("\r\n{0}- {1}", new String(' ', indentLevel), entryValue);
                }
                msg += newMsg;
            }
            else if (data is IDictionary)
            {
                bool start = true;
                foreach (DictionaryEntry entry in (IDictionary)data)
                {
                    string newMsg = FormatLogData(entry.Value, indentLevel + 2);
                    if (!start)
                        msg += String.Format("\r\n{0}", new String(' ', indentLevel));
                    msg += String.Format("{0}: {1}", (string)entry.Key, newMsg);
                    start = false;
                }
            }
            else
                msg = (string)RemoveNoLogValues(ParseStr(data), noLogValues);

            return msg;
        }

        private object RemoveNoLogValues(object value, HashSet<string> noLogStrings)
        {
            Queue<Tuple<object, object>> deferredRemovals = new Queue<Tuple<object, object>>();
            object newValue = RemoveValueConditions(value, noLogStrings, deferredRemovals);

            while (deferredRemovals.Count > 0)
            {
                Tuple<object, object> data = deferredRemovals.Dequeue();
                object oldData = data.Item1;
                object newData = data.Item2;

                if (oldData is IDictionary)
                {
                    foreach (DictionaryEntry entry in (IDictionary)oldData)
                    {
                        object newElement = RemoveValueConditions(entry.Value, noLogStrings, deferredRemovals);
                        ((IDictionary)newData).Add((string)entry.Key, newElement);
                    }
                }
                else
                {
                    foreach (object element in (IList)oldData)
                    {
                        object newElement = RemoveValueConditions(element, noLogStrings, deferredRemovals);
                        ((IList)newData).Add(newElement);
                    }
                }
            }

            return newValue;
        }

        private object RemoveValueConditions(object value, HashSet<string> noLogStrings, Queue<Tuple<object, object>> deferredRemovals)
        {
            if (value == null)
                return value;

            Type valueType = value.GetType();
            HashSet<Type> numericTypes = new HashSet<Type>
            {
                typeof(byte), typeof(sbyte), typeof(short), typeof(ushort), typeof(int), typeof(uint),
                typeof(long), typeof(ulong), typeof(decimal), typeof(double), typeof(float)
            };

            if (numericTypes.Contains(valueType) || valueType == typeof(bool))
            {
                string valueString = ParseStr(value);
                if (noLogStrings.Contains(valueString))
                    return "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER";
                foreach (string omitMe in noLogStrings)
                    if (valueString.Contains(omitMe))
                        return "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER";
            }
            else if (valueType == typeof(DateTime))
                value = ((DateTime)value).ToString("o");
            else if (value is IList)
            {
                List<object> newValue = new List<object>();
                deferredRemovals.Enqueue(new Tuple<object, object>((IList)value, newValue));
                value = newValue;
            }
            else if (value is IDictionary)
            {
                Hashtable newValue = new Hashtable();
                deferredRemovals.Enqueue(new Tuple<object, object>((IDictionary)value, newValue));
                value = newValue;
            }
            else
            {
                string stringValue = value.ToString();
                if (noLogStrings.Contains(stringValue))
                    return "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER";
                foreach (string omitMe in noLogStrings)
                    if (stringValue.Contains(omitMe))
                        return (stringValue).Replace(omitMe, "********");
                value = stringValue;
            }
            return value;
        }

        private void CleanupFiles(object s, EventArgs ev)
        {
            foreach (string path in cleanupFiles)
            {
                try
                {
#if WINDOWS
                    FileCleaner.Delete(path);
#else
                    if (File.Exists(path))
                        File.Delete(path);
                    else if (Directory.Exists(path))
                        Directory.Delete(path, true);
#endif
                }
                catch (Exception e)
                {
                    Warn(string.Format("Failure cleaning temp path '{0}': {1} {2}",
                        path, e.GetType().Name, e.Message));
                }
            }
            cleanupFiles = new List<string>();
        }

        private string FormatOptionsContext(string msg, string prefix = " ")
        {
            if (optionsContext.Count > 0)
                msg += String.Format("{0}found in {1}", prefix, String.Join(" -> ", optionsContext));
            return msg;
        }

        [DllImport("kernel32.dll")]
        private static extern IntPtr GetConsoleWindow();

        private static void ExitModule(int rc)
        {
            // When running in a Runspace Environment.Exit will kill the entire
            // process which is not what we want, detect if we are in a
            // Runspace and call a ScriptBlock with exit instead.
            if (Runspace.DefaultRunspace != null)
                ScriptBlock.Create("Set-Variable -Name LASTEXITCODE -Value $args[0] -Scope Global; exit $args[0]").Invoke(rc);
            else
            {
                // Used for local debugging in Visual Studio
                if (System.Diagnostics.Debugger.IsAttached)
                {
                    Console.WriteLine("Press enter to continue...");
                    Console.ReadLine();
                }
                Environment.Exit(rc);
            }
        }

        private static void WriteLineModule(string line)
        {
            Console.WriteLine(line);
        }
    }

#if WINDOWS
    // Windows is tricky as AVs and other software might still
    // have an open handle to files causing a failure. Use a
    // custom deletion mechanism to remove the files/dirs.
    // https://github.com/ansible/ansible/pull/80247
    internal static class FileCleaner
    {
        private const int FileDispositionInformation = 13;
        private const int FileDispositionInformationEx = 64;

        private const int ERROR_INVALID_PARAMETER = 0x00000057;
        private const int ERROR_DIR_NOT_EMPTY = 0x00000091;

        private static bool? _supportsPosixDelete = null;

        [Flags()]
        public enum DispositionFlags : uint
        {
            FILE_DISPOSITION_DO_NOT_DELETE = 0x00000000,
            FILE_DISPOSITION_DELETE = 0x00000001,
            FILE_DISPOSITION_POSIX_SEMANTICS = 0x00000002,
            FILE_DISPOSITION_FORCE_IMAGE_SECTION_CHECK = 0x00000004,
            FILE_DISPOSITION_ON_CLOSE = 0x00000008,
            FILE_DISPOSITION_IGNORE_READONLY_ATTRIBUTE = 0x00000010,
        }

        [Flags()]
        public enum FileFlags : uint
        {
            FILE_FLAG_OPEN_NO_RECALL = 0x00100000,
            FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000,
            FILE_FLAG_SESSION_AWARE = 0x00800000,
            FILE_FLAG_POSIX_SEMANTICS = 0x01000000,
            FILE_FLAG_BACKUP_SEMANTICS = 0x02000000,
            FILE_FLAG_DELETE_ON_CLOSE = 0x04000000,
            FILE_FLAG_SEQUENTIAL_SCAN = 0x08000000,
            FILE_FLAG_RANDOM_ACCESS = 0x10000000,
            FILE_FLAG_NO_BUFFERING = 0x20000000,
            FILE_FLAG_OVERLAPPED = 0x40000000,
            FILE_FLAG_WRITE_THROUGH = 0x80000000,
        }

        [DllImport("Kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        private static extern SafeFileHandle CreateFileW(
            [MarshalAs(UnmanagedType.LPWStr)] string lpFileName,
            FileSystemRights dwDesiredAccess,
            FileShare dwShareMode,
            IntPtr lpSecurityAttributes,
            FileMode dwCreationDisposition,
            uint dwFlagsAndAttributes,
            IntPtr hTemplateFile);

        private static SafeFileHandle CreateFile(string path, FileSystemRights access, FileShare share, FileMode mode,
            FileAttributes attributes, FileFlags flags)
        {
            uint flagsAndAttributes = (uint)attributes | (uint)flags;
            SafeFileHandle handle = CreateFileW(path, access, share, IntPtr.Zero, mode, flagsAndAttributes,
                IntPtr.Zero);
            if (handle.IsInvalid)
            {
                int errCode = Marshal.GetLastWin32Error();
                string msg = string.Format("CreateFileW({0}) failed 0x{1:X8}: {2}",
                    path, errCode, new Win32Exception(errCode).Message);
                throw new Win32Exception(errCode, msg);
            }

            return handle;
        }

        [DllImport("Ntdll.dll")]
        private static extern int NtSetInformationFile(
            SafeFileHandle FileHandle,
            out IntPtr IoStatusBlock,
            ref int FileInformation,
            int Length,
            int FileInformationClass);

        [DllImport("Ntdll.dll")]
        private static extern int RtlNtStatusToDosError(
            int Status);

        public static void Delete(string path)
        {
            if (File.Exists(path))
            {
                DeleteEntry(path, FileAttributes.ReadOnly);
            }
            else if (Directory.Exists(path))
            {
                Queue<DirectoryInfo> dirQueue = new Queue<DirectoryInfo>();
                dirQueue.Enqueue(new DirectoryInfo(path));
                bool nonEmptyDirs = false;
                HashSet<string> processedDirs = new HashSet<string>();

                while (dirQueue.Count > 0)
                {
                    DirectoryInfo currentDir = dirQueue.Dequeue();

                    bool deleteDir = true;
                    if (processedDirs.Add(currentDir.FullName))
                    {
                        foreach (FileSystemInfo entry in currentDir.EnumerateFileSystemInfos())
                        {
                            // Tries to delete each entry. Failures are ignored
                            // as they will be picked up when the dir is
                            // deleted and not empty.
                            if (entry is DirectoryInfo)
                            {
                                if ((entry.Attributes & FileAttributes.ReparsePoint) != 0)
                                {
                                    // If it's a reparse point, just delete it directly.
                                    DeleteEntry(entry.FullName, entry.Attributes, ignoreFailure: true);
                                }
                                else
                                {
                                    // Add the dir to the queue to delete and it will be processed next round.
                                    dirQueue.Enqueue((DirectoryInfo)entry);
                                    deleteDir = false;
                                }
                            }
                            else
                            {
                                DeleteEntry(entry.FullName, entry.Attributes, ignoreFailure: true);
                            }
                        }
                    }

                    if (deleteDir)
                    {
                        try
                        {
                            DeleteEntry(currentDir.FullName, FileAttributes.Directory);
                        }
                        catch (Win32Exception e)
                        {
                            if (e.NativeErrorCode == ERROR_DIR_NOT_EMPTY)
                            {
                                nonEmptyDirs = true;
                            }
                            else
                            {
                                throw;
                            }
                        }
                    }
                    else
                    {
                        dirQueue.Enqueue(currentDir);
                    }
                }

                if (nonEmptyDirs)
                {
                    throw new IOException("Directory contains files still open by other processes");
                }
            }
        }

        private static void DeleteEntry(string path, FileAttributes attr, bool ignoreFailure = false)
        {
            try
            {
                if ((attr & FileAttributes.ReadOnly) != 0)
                {
                    // Windows does not allow files set with ReadOnly to be
                    // deleted. Pre-emptively unset the attribute.
                    // FILE_DISPOSITION_IGNORE_READONLY_ATTRIBUTE is quite new,
                    // look at using that flag with POSIX delete once Server 2019
                    // is the baseline.
                    File.SetAttributes(path, FileAttributes.Normal);
                }

                // REPARSE - Only touch the symlink itself and not the target
                // BACKUP - Needed for dir handles, bypasses access checks for admins
                // DELETE_ON_CLOSE is not used as it interferes with the POSIX delete
                FileFlags flags = FileFlags.FILE_FLAG_OPEN_REPARSE_POINT |
                    FileFlags.FILE_FLAG_BACKUP_SEMANTICS;

                using (SafeFileHandle fileHandle = CreateFile(path, FileSystemRights.Delete,
                    FileShare.ReadWrite | FileShare.Delete, FileMode.Open, FileAttributes.Normal, flags))
                {
                    if (_supportsPosixDelete == null || _supportsPosixDelete == true)
                    {
                        // A POSIX delete will delete the filesystem entry even if
                        // it's still opened by another process so favour that if
                        // available.
                        DispositionFlags deleteFlags = DispositionFlags.FILE_DISPOSITION_DELETE |
                            DispositionFlags.FILE_DISPOSITION_POSIX_SEMANTICS;

                        SetInformationFile(fileHandle, FileDispositionInformationEx, (int)deleteFlags);
                        if (_supportsPosixDelete == true)
                        {
                            return;
                        }
                    }

                    // FileDispositionInformation takes in a struct with only a BOOLEAN value.
                    // Using an int will also do the same thing to set that flag to true.
                    SetInformationFile(fileHandle, FileDispositionInformation, Int32.MaxValue);
                }
            }
            catch
            {
                if (!ignoreFailure)
                {
                    throw;
                }
            }
        }

        private static void SetInformationFile(SafeFileHandle handle, int infoClass, int value)
        {
            IntPtr ioStatusBlock = IntPtr.Zero;

            int ntStatus = NtSetInformationFile(handle, out ioStatusBlock, ref value,
                Marshal.SizeOf(typeof(int)), infoClass);

            if (ntStatus != 0)
            {
                int errCode = RtlNtStatusToDosError(ntStatus);

                // The POSIX delete was added in Server 2016 (Win 10 14393/Redstone 1)
                // Mark this flag so we don't try again.
                if (infoClass == FileDispositionInformationEx && _supportsPosixDelete == null &&
                    errCode == ERROR_INVALID_PARAMETER)
                {
                    _supportsPosixDelete = false;
                    return;
                }

                string msg = string.Format("NtSetInformationFile() failed 0x{0:X8}: {1}",
                    errCode, new Win32Exception(errCode).Message);
                throw new Win32Exception(errCode, msg);
            }

            if (infoClass == FileDispositionInformationEx)
            {
                _supportsPosixDelete = true;
            }
        }
    }
#endif
}
