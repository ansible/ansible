using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Management.Automation;
using System.Management.Automation.Runspaces;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Web.Script.Serialization;

//AssemblyReference -Name System.Web.Extensions.dll -CLR Framework

namespace Ansible.Basic
{
    public class AnsibleModule
    {
        private static List<string> BOOLEANS_TRUE = new List<string>() { "y", "yes", "on", "1", "true", "t", "1.0" };
        private static List<string> BOOLEANS_FALSE = new List<string>() { "n", "no", "off", "0", "false", "f", "0.0" };

        private string remoteTmp = Path.GetTempPath();
        private string tmpdir = null;

        private Dictionary<string, string> aliases = new Dictionary<string, string>();
        private List<string> legalInputs = new List<string>();
        private HashSet<string> noLogValues = new HashSet<string>();
        private List<string> optionsContext = new List<string>();
        private List<string> warnings = new List<string>();
        private List<Dictionary<string, string>> deprecations = new List<Dictionary<string, string>>();
        private List<string> cleanupFiles = new List<string>();

        private Dictionary<string, string> passVars = new Dictionary<string, string>()
        {
            { "check_mode", "CheckMode" },
            { "debug", "DebugMode" },
            { "diff", "DiffMode" },
            { "keep_remote_files", "KeepRemoteFiles" },
            { "module_name", "ModuleName" },
            { "no_log", "NoLog" },
            { "remote_tmp", "remoteTmp" },
            { "tmpdir", "tmpdir" },
            { "verbosity", "Verbosity" },
            { "version", "AnsibleVersion" },
        };
        private List<string> passBools = new List<string>() { "check_mode", "debug", "diff", "keep_remote_files", "no_log" };
        private Dictionary<string, List<object>> metadataDefaults = new Dictionary<string, List<object>>()
        {
            // key - (default, type) - null is freeform
            { "apply_defaults", new List<object>() { false, typeof(bool)} },
            { "aliases", new List<object>() { typeof(List<string>), typeof(List<string>) } },
            { "choices", new List<object>() { typeof(List<object>), typeof(List<object>) } },
            { "default", new List<object>() { null, null } },
            { "elements", new List<object>() { null, typeof(string) } },
            { "mutually_exclusive", new List<object>() { typeof(List<List<string>>), typeof(List<List<string>>) } },
            { "no_log", new List<object>() { false, typeof(bool) } },
            { "options", new List<object>() { null, typeof(Hashtable) } },
            { "removed_in_version", new List<object>() { null, typeof(string) } },
            { "required", new List<object>() { false, typeof(bool) } },
            { "required_if", new List<object>() { typeof(List<List<object>>), typeof(List<List<object>>) } },
            { "required_one_of", new List<object>() { typeof(List<List<string>>), typeof(List<List<string>>) } },
            { "required_together", new List<object>() { typeof(List<List<string>>), typeof(List<List<string>>) } },
            { "type", new List<object>() { "str", typeof(string) } },
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
        public Dictionary<string, object> Params = new Dictionary<string, object>();
        public Dictionary<string, object> Result = new Dictionary<string, object>() { { "changed", false } };

        public bool CheckMode { get; private set; }
        public bool DebugMode { get; private set; }
        public bool DiffMode { get; private set; }
        public bool KeepRemoteFiles { get; private set; }
        public string ModuleName { get; private set; }
        public bool NoLog { get; private set; }
        public int Verbosity { get; private set; }
        public string AnsibleVersion { get; private set; }

        public string Tmpdir
        {
            get
            {
                if (tmpdir == null)
                {
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
                            Directory.CreateDirectory(baseDir, dirSecurity);
                        }
                        catch (Exception e)
                        {
                            failedMsg = String.Format("Failed to create base tmpdir '{0}': {1}", baseDir, e.Message);
                        }

                        if (failedMsg == null)
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
                    string dirName = String.Format("ansible-moduletmp-{0}-{0}", dateTime, new Random().Next(0, int.MaxValue));
                    string newTmpdir = Path.Combine(baseDir, dirName);
                    Directory.CreateDirectory(newTmpdir, dirSecurity);
                    tmpdir = newTmpdir;

                    if (!KeepRemoteFiles)
                        cleanupFiles.Add(tmpdir);
                }
                return tmpdir;
            }
        }

        public AnsibleModule(string[] args, Hashtable argumentSpec, bool supportsCheckMode, bool noLog,
            List<List<string>> mutuallyExclusive, List<List<string>> requiredTogether, List<List<string>> requiredOneOf,
            List<List<object>> requiredIf, Dictionary<string, Delegate> extraTypes)
        {
            // Initialise public properties to the defaults
            CheckMode = false;
            DebugMode = false;
            DiffMode = false;
            KeepRemoteFiles = false;
            ModuleName = "undefined win module";
            NoLog = noLog;
            Verbosity = 0;

            // Add any extra types defined by the user
            if (extraTypes != null)
                foreach (KeyValuePair<string, Delegate> type in extraTypes)
                    optionTypes[type.Key] = type.Value;
            legalInputs = passVars.Keys.Select(v => "_ansible_" + v).ToList();
            AppDomain.CurrentDomain.ProcessExit += CleanupFiles;

            // NoLog is not set yet, we cannot rely on FailJson to sanitize the output
            // Do the minimum amount to get this running before we actually parse the params
            try
            {
                ValidateArgumentSpec(argumentSpec);
                Params = GetParams(args);
                aliases = GetAliases(argumentSpec, Params);
                SetNoLogValues(argumentSpec, Params);
            }
            catch (Exception e)
            {
                Dictionary<string, object> result = new Dictionary<string, object>
                {
                    { "failed", true },
                    { "msg", String.Format("internal error: {0}", e.Message) },
                    { "exception", e.ToString() }
                };
                WriteLine(ToJson(result));
                Exit(1);
            }

            CheckArguments(argumentSpec, Params, legalInputs, supportsCheckMode, mutuallyExclusive, requiredTogether, requiredOneOf, requiredIf);
            if (!NoLog)
                Log(String.Format("Invoked with:\r\n  {0}", FormatLogData(Params, 2)), sanitise: false);
        }

        public void Debug(string message)
        {
            if (DebugMode)
                Log(String.Format("[DEBUG] {0}", message));
        }

        public void Deprecate(string message, string version)
        {
            deprecations.Add(new Dictionary<string, string>() { { "message", message }, { "version", version } });
            Log(String.Format("[DEPRECATION WARNING] {0} {1}", message, version));
        }

        public void ExitJson()
        {
            WriteLine(GetFormattedResults(Result));
            CleanupFiles(null, null);
            Exit(0);
        }

        public void FailJson(string message) { FailJson(message, null, null); }
        public void FailJson(string message, ErrorRecord psErrorRecord) { FailJson(message, psErrorRecord, null); }
        public void FailJson(string message, Exception exception) { FailJson(message, null, exception); }
        private void FailJson(string message, ErrorRecord psErrorRecord, Exception exception)
        {
            Result["failed"] = true;
            Result["msg"] = message;

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

            WriteLine(GetFormattedResults(Result));
            CleanupFiles(null, null);
            Exit(1);
        }

        public void Log(string message, EventLogEntryType logEntryType = EventLogEntryType.Information, bool sanitise = true)
        {
            if (NoLog)
                return;

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
                    Warn(String.Format("Access error when creating EventLog source {0}, logging to the Application source instead", logSource));
                    logSource = "Application";
                }
            }
            if (sanitise)
                message = (string)RemoveNoLogValues(message, noLogValues);
            message = String.Format("{0} - {1}", ModuleName, message);

            using (EventLog eventLog = new EventLog("Application"))
            {
                eventLog.Source = logSource;
                eventLog.WriteEntry(message, logEntryType, 0);
            }
        }

        public void Warn(string message)
        {
            warnings.Add(message);
            Log(String.Format("[WARNING] {0}", message), EventLogEntryType.Warning);
        }

        public static Dictionary<string, object> FromJson(string json) { return FromJson<Dictionary<string, object>>(json); }
        public static T FromJson<T>(string json)
        {
            JavaScriptSerializer jss = new JavaScriptSerializer();
            jss.MaxJsonLength = int.MaxValue;
            jss.RecursionLimit = int.MaxValue;
            return jss.Deserialize<T>(json);
        }

        public static string ToJson(object obj)
        {
            JavaScriptSerializer jss = new JavaScriptSerializer();
            jss.MaxJsonLength = int.MaxValue;
            jss.RecursionLimit = int.MaxValue;
            return jss.Serialize(obj);
        }

        public static Dictionary<string, object> GetParams(string[] args)
        {
            if (args.Length > 0)
            {
                string inputJson = File.ReadAllText(args[0]);
                Dictionary<string, object> rawParams = FromJson(inputJson);
                if (!rawParams.ContainsKey("ANSIBLE_MODULE_ARGS"))
                    throw new ArgumentException("Module was unable to get ANSIBLE_MODULE_ARGS value from the argument path json");
                return (Dictionary<string, object>)rawParams["ANSIBLE_MODULE_ARGS"];
            }
            else
            {
                PSObject rawArgs = ScriptBlock.Create("$complex_args").Invoke()[0];
                Hashtable test = rawArgs.BaseObject as Hashtable;
                return test.Cast<DictionaryEntry>().ToDictionary(kvp => (string)kvp.Key, kvp => (object)kvp.Value);
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
            if (valueType.IsGenericType && valueType.GetGenericTypeDefinition() == typeof(Dictionary<,>))
                return (Dictionary<string, object>)value;
            else if (valueType == typeof(Hashtable))
                return (Dictionary<string, object>)value;
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
            else if (valueType == typeof(string))
                return Int32.Parse((string)value);
            else
                throw new ArgumentException(String.Format("{0} cannot be converted to an int", valueType.FullName));
        }

        public static string ParseJson(object value)
        {
            // mostly used to ensure a dict or list is a json string as it may
            // have been converted on the controller side
            Type valueType = value.GetType();
            if (valueType.GetGenericTypeDefinition() == typeof(Dictionary<,>) || valueType.GetGenericTypeDefinition() == typeof(List<>))
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

        private void ValidateArgumentSpec(Hashtable argumentSpec)
        {
            foreach (DictionaryEntry entry in argumentSpec)
            {
                Hashtable metadata = (Hashtable)entry.Value;

                Dictionary<string, object> changedValues = new Dictionary<string, object>();
                foreach (DictionaryEntry metadataEntry in metadata)
                {
                    string key = (string)metadataEntry.Key;
                    if (!metadataDefaults.ContainsKey(key))
                    {
                        string msg = String.Format("argument spec entry '{0}' contains an invalid key '{1}', valid keys: {2}",
                            (string)entry.Key, key, String.Join(", ", metadataDefaults.Keys));
                        if (optionsContext.Count > 0)
                            msg += String.Format(" - found in {0}.", String.Join(" -> ", optionsContext));
                        throw new ArgumentException(msg);
                    }

                    if (metadataEntry.Value != null)
                    {
                        Type optionType = (Type)metadataDefaults[key][1];
                        if (optionType == null)
                            continue;

                        Type actualType = metadataEntry.Value.GetType();
                        bool invalid = false;
                        if (optionType.IsGenericType && optionType.GetGenericTypeDefinition() == typeof(List<>))
                        {
                            // verify the actual type is not just a single value of the list type
                            Type entryType = optionType.GetGenericArguments()[0];

                            bool isArray = actualType.IsArray && (actualType.GetElementType() == entryType || actualType.GetElementType() == typeof(object));
                            if (actualType == entryType || isArray)
                            {
                                object[] rawArray;
                                if (isArray)
                                    rawArray = (object[])metadataEntry.Value;
                                else
                                    rawArray = new object[1] { metadataEntry.Value };

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
                            string msg = String.Format("argument spec for '{0}' entry '{1}' did not match expected type {2}: actual type {3}",
                                (string)entry.Key, key, optionType.FullName, actualType.FullName);
                            if (optionsContext.Count > 0)
                                msg += String.Format(" - found in {0}.", String.Join(" -> ", optionsContext));
                            throw new ArgumentException(msg);
                        }
                    }

                    if (key == "options" && metadataEntry.Value != null)
                    {
                        optionsContext.Add((string)entry.Key);
                        ValidateArgumentSpec((Hashtable)metadataEntry.Value);
                        optionsContext.RemoveAt(optionsContext.Count - 1);
                    }

                    if (key == "type" || key == "elements" && metadataEntry.Value != null)
                    {
                        string typeValue = (string)metadataEntry.Value;
                        if (!optionTypes.ContainsKey(typeValue))
                        {
                            string msg = String.Format("{0} '{1}' for '{2}' is unsupported", key, typeValue, (string)entry.Key);
                            if (optionsContext.Count > 0)
                                msg += String.Format(" - found in {0}", String.Join(" -> ", optionsContext));
                            msg += String.Format(". Valid types are: {0}", String.Join(", ", optionTypes.Keys));
                            throw new ArgumentException(msg);
                        }
                    }
                }
                foreach (KeyValuePair<string, object> changedValue in changedValues)
                    metadata[changedValue.Key] = changedValue.Value;

                foreach (KeyValuePair<string, List<object>> metadataEntry in metadataDefaults)
                {
                    List<object> defaults = metadataEntry.Value;
                    object defaultValue = defaults[0];
                    if (defaultValue != null && defaultValue.GetType() == typeof(Type).GetType())
                        defaultValue = Activator.CreateInstance((Type)defaultValue);

                    if (!metadata.ContainsKey(metadataEntry.Key))
                        metadata[metadataEntry.Key] = defaultValue;
                }
            }
        }

        private Dictionary<string, string> GetAliases(Hashtable argumentSpec, Dictionary<string, object> parameters)
        {
            Dictionary<string, string> aliasResults = new Dictionary<string, string>();

            foreach (DictionaryEntry entry in argumentSpec)
            {
                string k = (string)entry.Key;
                Hashtable v = (Hashtable)entry.Value;

                legalInputs.Add(k);
                List<string> aliases = (List<string>)v["aliases"];
                object defaultValue = v["default"];
                bool required = (bool)v["required"];

                if (defaultValue != null && required)
                    throw new ArgumentException(String.Format("required and default are mutually exclusive for {0}", k));

                foreach (string alias in aliases)
                {
                    legalInputs.Add(alias);
                    aliasResults.Add(alias, k);
                    if (parameters.ContainsKey(alias))
                        parameters[k] = parameters[alias];
                }
            }

            return aliasResults;
        }

        private void SetNoLogValues(Hashtable argumentSpec, Dictionary<string, object> parameters)
        {
            foreach (DictionaryEntry entry in argumentSpec)
            {
                string k = (string)entry.Key;
                Hashtable v = (Hashtable)entry.Value;

                if ((bool)v["no_log"])
                {
                    object noLogObject = parameters.ContainsKey(k) ? parameters[k] : null;
                    if (noLogObject != null)
                        noLogValues.Add(noLogObject.ToString());
                }

                object removedInVersion = v["removed_in_version"];
                if (removedInVersion != null && parameters.ContainsKey(k))
                    Deprecate(String.Format("Param '{0}' is deprecated. See the module docs for more information", k), removedInVersion.ToString());
            }
        }

        private void CheckArguments(Hashtable spec, Dictionary<string, object> param, List<string> legalInputs, bool supportsCheckMode,
            List<List<string>> mutuallyExclusive, List<List<string>> requiredTogether, List<List<string>> requiredOneOf, List<List<object>> requiredIf)
        {
            // initially parse the params and check for unsupported ones and set internal vars
            CheckUnsupportedArguments(spec, param);

            if (CheckMode && !supportsCheckMode)
            {
                Result["skipped"] = true;
                Result["msg"] = String.Format("remote module ({0}) does not support check mode", ModuleName);
                ExitJson();
            }

            if (mutuallyExclusive != null)
                CheckMutuallyExclusive(param, mutuallyExclusive);
            CheckRequiredArguments(spec, param);

            // set the parameter types based on the type spec value
            foreach (DictionaryEntry entry in spec)
            {
                string k = (string)entry.Key;
                Hashtable v = (Hashtable)entry.Value;

                object value = param.ContainsKey(k) ? param[k] : null;
                if (value != null)
                {
                    // convert the current value to the wanted type
                    string type = (string)v["type"];
                    Delegate typeConverter = optionTypes[type];
                    try
                    {
                        value = typeConverter.DynamicInvoke(value);
                        param[k] = value;

                    }
                    catch (Exception e)
                    {
                        string msg = String.Format("argument for {0} is of type {1} and we were unable to convert to {2}: {3}",
                            k, value.GetType(), type, e.Message);
                        if (optionsContext.Count > 0)
                            msg += String.Format(" found in {0}", String.Join(" -> ", optionsContext));
                        FailJson(msg);
                    }

                    // ensure it matches the choices if there are choices set
                    List<object> choices = (List<object>)v["choices"];
                    if (choices.Count > 0)
                    {
                        // allow one or more when type="list" param with choices
                        if (type == "list")
                        {
                            var diffList = ((List<object>)value).Except(choices).ToList();
                            if (diffList.Count > 0)
                            {
                                string msg = String.Format("value of {0} must be one or more of: {1}. Got no match for: {2}",
                                    k, String.Join(", ", choices), String.Join(", ", diffList));
                                if (optionsContext.Count > 0)
                                    msg += String.Format(" found in {0}", String.Join(" -> ", optionsContext));
                                FailJson(msg);
                            }
                        }
                        else if (!choices.Contains(value))
                        {
                            string msg = String.Format("value of {0} must be one of: {1}, got: {2}", k, String.Join(", ", choices), value);
                            if (optionsContext.Count > 0)
                                msg += String.Format(" found in {0}", String.Join(" -> ", optionsContext));
                            FailJson(msg);
                        }
                    }
                }
            }

            if (requiredTogether != null)
                CheckRequiredTogether(param, requiredTogether);
            if (requiredOneOf != null)
                CheckRequiredOneOf(param, requiredOneOf);
            if (requiredIf != null)
                CheckRequiredIf(param, requiredIf);

            // finally ensure all missing parameters are set to null and handle sub options
            foreach (DictionaryEntry entry in spec)
            {
                string k = (string)entry.Key;
                Hashtable v = (Hashtable)entry.Value;

                if (!param.ContainsKey(k))
                    param[k] = null;

                CheckSubOption(param, k, v);
            }
        }

        private void CheckUnsupportedArguments(Hashtable spec, Dictionary<string, object> param)
        {
            HashSet<string> unsupportedParameters = new HashSet<string>();
            List<string> removedParameters = new List<string>();

            foreach (KeyValuePair<string, object> entry in param)
            {
                if (entry.Key.StartsWith("_ansible_"))
                {
                    removedParameters.Add(entry.Key);
                    string key = entry.Key.Replace("_ansible_", "");
                    // skip setting NoLog if NoLog is already set to true (set by the module)
                    if (!passVars.ContainsKey(key) || (key == "no_log" && NoLog == true))
                        continue;

                    object value = entry.Value;
                    if (passBools.Contains(key))
                        value = ParseBool(value);

                    string propertyName = passVars[key];
                    PropertyInfo property = typeof(AnsibleModule).GetProperty(propertyName);
                    FieldInfo field = typeof(AnsibleModule).GetField(propertyName, BindingFlags.NonPublic | BindingFlags.Instance);
                    if (property != null)
                        property.SetValue(this, value);
                    else if (field != null)
                        field.SetValue(this, value);
                    else
                        FailJson(String.Format("implementation error: unknown AnsibleModule property {0}", propertyName));
                }
                else if (!legalInputs.Contains(entry.Key))
                    unsupportedParameters.Add(entry.Key);
            }
            foreach (string parameter in removedParameters)
                param.Remove(parameter);

            if (unsupportedParameters.Count > 0)
            {
                string msg = String.Format("Unsupported parameters for ({0}) module: {1}", ModuleName, String.Join(", ", unsupportedParameters));
                if (optionsContext.Count > 0)
                    msg += String.Format(" found in {0}.", String.Join(" -> ", optionsContext));
                msg += String.Format(" Supported parameters include: {0}", String.Join(", ", spec.Keys.Cast<string>().ToList()));
                FailJson(msg);
            }
        }

        private void CheckMutuallyExclusive(Dictionary<string, object> param, List<List<string>> mutuallyExclusive)
        {
            foreach (List<string> check in mutuallyExclusive)
            {
                int count = 0;
                foreach (string entry in check)
                    if (param.ContainsKey(entry))
                        count++;

                if (count > 1)
                {
                    string msg = String.Format("parameters are mutually exclusive: {0}", String.Join(", ", check));
                    if (optionsContext.Count > 0)
                        msg += String.Format(" found in {0}", String.Join(" -> ", optionsContext));
                    FailJson(msg);
                }
            }
        }

        private void CheckRequiredArguments(Hashtable spec, Dictionary<string, object> param)
        {
            List<string> missing = new List<string>();
            foreach (DictionaryEntry entry in spec)
            {
                string k = (string)entry.Key;
                Hashtable v = (Hashtable)entry.Value;

                // set defaults for values not already set
                object defaultValue = v["default"];
                if (defaultValue != null && !param.ContainsKey(k))
                    param[k] = defaultValue;

                // check required arguments
                bool required = (bool)v["required"];
                if (required && !param.ContainsKey(k))
                    missing.Add(k);
            }
            if (missing.Count > 0)
            {
                string msg = String.Format("missing required arguments: {0}", String.Join(", ", missing));
                if (optionsContext.Count > 0)
                    msg += String.Format(" found in {0}", String.Join(" -> ", optionsContext));
                FailJson(msg);
            }
        }

        private void CheckRequiredTogether(Dictionary<string, object> param, List<List<string>> requiredTogether)
        {
            foreach (List<string> check in requiredTogether)
            {
                List<bool> found = new List<bool>();
                foreach (string field in check)
                    if (param.ContainsKey(field))
                        found.Add(true);
                    else
                        found.Add(false);

                if (found.Contains(true) && found.Contains(false))
                {
                    string msg = String.Format("parameters are required together: {0}", String.Join(", ", check));
                    if (optionsContext.Count > 0)
                        msg += String.Format(" found in {0}", String.Join(" -> ", optionsContext));
                    FailJson(msg);
                }
            }
        }

        private void CheckRequiredOneOf(Dictionary<string, object> param, List<List<string>> requiredOneOf)
        {
            foreach (List<string> check in requiredOneOf)
            {
                int count = 0;
                foreach (string field in check)
                    if (param.ContainsKey(field))
                        count++;

                if (count == 0)
                {
                    string msg = String.Format("one of the following is required: {0}", String.Join(", ", check));
                    if (optionsContext.Count > 0)
                        msg += String.Format(" found in {0}", String.Join(" -> ", optionsContext));
                    FailJson(msg);
                }
            }
        }

        private void CheckRequiredIf(Dictionary<string, object> param, List<List<object>> requiredIf)
        {
            List<string> missing = new List<string>();
            foreach (List<object> check in requiredIf)
            {
                List<string> missingFields = new List<string>();
                int maxMissingCount = 1;
                bool oneRequired = false;

                if (check.Count < 3 && check.Count < 4)
                    FailJson(String.Format("internal error: invalid required if value count of {0}, expecting 3 or 4 entries", check.Count));
                else if (check.Count == 4)
                    oneRequired = (bool)check[3];

                string key = (string)check[0];
                object val = check[1];
                List<string> requirements = (List<string>)check[2];

                if (ParseStr(param[key]) != ParseStr(val))
                    continue;

                string term = "all";
                if (oneRequired)
                {
                    maxMissingCount = requirements.Count;
                    term = "any";
                }

                foreach (string required in requirements)
                    if (!param.ContainsKey(required))
                        missing.Add(required);

                if (missing.Count >= maxMissingCount)
                {
                    string msg = String.Format("{0} is {1} but {2} of the following are missing: {3}",
                        key, val.ToString(), term, String.Join(", ", missing));
                    if (optionsContext.Count > 0)
                        msg += String.Format(" found in {0}", String.Join(" -> ", optionsContext));
                    FailJson(msg);
                }
            }
        }

        private void CheckSubOption(Dictionary<string, object> param, string key, Hashtable spec)
        {
            string type = (string)spec["type"];
            string elements = (string)spec["elements"];
            object value = param[key];

            if (!(type == "dict" || (type == "list" && elements != null)))
                // either not a dict, or list with the elements set, so continue
                return;
            else if (type == "list")
            {
                // cast each list element to the type specified
                if (value == null)
                    return;

                List<object> newValue = new List<object>();
                Delegate typeConverter = optionTypes[elements];
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
                            if (optionsContext.Count > 0)
                                msg += String.Format(" found in {0}", String.Join(" -> ", optionsContext));
                            FailJson(msg);
                        }
                    }
                }

                param[key] = newValue;
            }
            else
                param[key] = ParseSubSpec(spec, value, key);
        }

        private object ParseSubSpec(Hashtable options, object value, string context)
        {
            Hashtable spec = (Hashtable)options["options"];
            if (options == null)
                return value;

            bool applyDefaults = (bool)options["apply_defaults"];

            // set entry to an empty dict if apply_defaults is set
            if (applyDefaults && options != null && value == null)
                value = new Dictionary<string, object>();
            else if (options == null || value == null)
                return value;

            optionsContext.Add(context);
            Dictionary<string, object> newValue = ParseDict(value);
            Dictionary<string, string> aliases = GetAliases(spec, newValue);
            SetNoLogValues(spec, newValue);

            List<string> subLegalInputs = spec.Keys.Cast<string>().ToList();
            subLegalInputs.AddRange(aliases.Keys.Cast<string>().ToList());

            CheckArguments(spec, newValue, subLegalInputs, true, (List<List<string>>)options["mutually_exclusive"],
                (List<List<string>>)options["required_together"], (List<List<string>>)options["required_one_of"],
                (List<List<object>>)options["required_if"]);

            optionsContext.RemoveAt(optionsContext.Count - 1);
            return newValue;
        }

        private string GetFormattedResults(Dictionary<string, object> result)
        {
            if (!result.ContainsKey("invocation"))
                result["invocation"] = new Dictionary<string, object>() { { "module_args", Params } };

            if (warnings.Count > 0)
                result["warnings"] = warnings;

            if (deprecations.Count > 0)
                result["deprecations"] = deprecations;

            if (Diff.Count > 0 && DiffMode)
                result["diff"] = Diff;

            object newResult = RemoveNoLogValues(result, noLogValues);
            return ToJson(newResult);
        }

        private string FormatLogData(object data, int indentLevel)
        {
            if (data == null)
                return "$null";

            string msg = "";
            Type dataType = data.GetType();
            if ((dataType.IsGenericType && dataType.GetGenericTypeDefinition() == typeof(List<>)) || dataType == typeof(ArrayList) || dataType.IsArray)
            {
                string newMsg = "";
                foreach (object value in ParseList(data))
                {
                    string entryValue = FormatLogData(value, indentLevel + 2);
                    newMsg += String.Format("\r\n{0}- {1}", new String(' ', indentLevel), entryValue);
                }
                msg += newMsg;
            }
            else if ((dataType.IsGenericType && dataType.GetGenericTypeDefinition() == typeof(Dictionary<,>)) || dataType == typeof(Hashtable))
            {
                bool start = true;
                foreach (KeyValuePair<string, object> entry in ParseDict(data))
                {
                    string newMsg = FormatLogData(entry.Value, indentLevel + 2);
                    if (!start)
                        msg += String.Format("\r\n{0}", new String(' ', indentLevel));
                    msg += String.Format("{0}: {1}", entry.Key, newMsg);
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

                if (oldData.GetType() == typeof(Hashtable))
                {
                    foreach (DictionaryEntry entry in (Hashtable)oldData)
                    {
                        object newElement = RemoveValueConditions(entry.Value, noLogStrings, deferredRemovals);
                        ((Hashtable)newData).Add((string)entry.Key, newElement);
                    }
                }
                else
                {
                    foreach (object element in (List<object>)oldData)
                    {
                        object newElement = RemoveValueConditions(element, noLogStrings, deferredRemovals);
                        ((List<object>)newData).Add(newElement);
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

            if (valueType == typeof(string))
            {
                if (noLogStrings.Contains((string)value))
                    return "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER";
                foreach (string omitMe in noLogStrings)
                    return ((string)value).Replace(omitMe, new String('*', omitMe.Length));
            }
            else if (numericTypes.Contains(valueType) || valueType == typeof(bool))
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

            // common list types in PowerShell
            else if (valueType.IsGenericType && valueType.GetGenericTypeDefinition() == typeof(List<>))
            {
                List<object> newValue = new List<object>();
                deferredRemovals.Enqueue(new Tuple<object, object>((List<object>)value, newValue));
                value = newValue;

            }
            else if (valueType.IsArray)
            {
                List<object> newValue = new List<object>();
                List<object> oldValue = ((object[])value).ToList();
                deferredRemovals.Enqueue(new Tuple<object, object>(oldValue, newValue));
                value = newValue;
            }
            else if (valueType == typeof(ArrayList))
            {
                List<object> newValue = new List<object>();
                List<object> oldValue = ((ArrayList)value).Cast<object>().ToList();
                deferredRemovals.Enqueue(new Tuple<object, object>(oldValue, newValue));
                value = newValue;
            }

            // common Dictionary types in PowerShell
            else if (valueType.IsGenericType && valueType.GetGenericTypeDefinition() == typeof(Dictionary<,>))
            {
                Hashtable newValue = new Hashtable();
                Hashtable oldValue = new Hashtable((IDictionary)value);
                deferredRemovals.Enqueue(new Tuple<object, object>(oldValue, newValue));
                value = newValue;
            }
            else if (valueType == typeof(Hashtable))
            {
                Hashtable newValue = new Hashtable();
                deferredRemovals.Enqueue(new Tuple<object, object>((Hashtable)value, newValue));
                value = newValue;
            }
            else
                throw new ArgumentException(String.Format("Value of unsupported type: {0}, {1}", valueType.FullName, value.ToString()));

            return value;
        }

        private void CleanupFiles(object s, EventArgs ev)
        {
            foreach (string path in cleanupFiles)
            {
                if (File.Exists(path))
                    File.Delete(path);
                else if (Directory.Exists(path))
                    Directory.Delete(path, true);
            }
            cleanupFiles = new List<string>();
        }

        [DllImport("kernel32.dll")]
        private static extern IntPtr GetConsoleWindow();

        private static void Exit(int rc)
        {
            // When running in a Runspace Environment.Exit will kill the entire
            // process which is not what we want, detect if we are in a
            // Runspace and call a ScriptBlock with exit instead.
            if (Runspace.DefaultRunspace != null)
                ScriptBlock.Create("Set-Variable -Name LASTEXITCODE -Value $args[0] -Scope Global; exit $args[0]").Invoke(rc);
            else
                if (System.Diagnostics.Debugger.IsAttached)
                    Console.ReadLine();
                Environment.Exit(rc);
        }

        private static void WriteLine(string line)
        {
            // When running over psrp there may not be a console to write the
            // line to, we check if there is a Console Window and fallback on
            // setting a variable that the Ansible leaf_exec will check and
            // output to the PowerShell Output stream on close
            Console.WriteLine(line);
            if (GetConsoleWindow() == IntPtr.Zero && Runspace.DefaultRunspace != null)
                ScriptBlock.Create("Set-Variable -Name _ansible_output -Value $args[0] -Scope Global").Invoke(line);
        }
    }
}