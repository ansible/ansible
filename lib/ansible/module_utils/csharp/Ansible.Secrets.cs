using System;
using System.Collections.Generic;
using System.Globalization;
using System.Runtime.InteropServices;
using System.Security;
using System.Text;

namespace Ansible.Secrets
{
    // See lib/ansible/module_utils/_internal/_secrets.py for the Python impl and details behind algorithm choices.
    public class SecretMasker
    {
        // Not marked readonly so integration tests can reset the singleton to a
        // pristine instance via reflection between test cases (setting a static
        // readonly field via reflection is not supported on CoreCLR).
        private static SecretMasker _instance = new SecretMasker();

        // If any of these are changed we need to ensure that _secrets.py is updated to match.
        private const int MinimumSecretLength = 4;  // below this, not registered at all
        private const int MaximumShortSecretLength = 6;  // above this, mask unconditionally
        private const int MaximumSecretLength = 65536;  // trims to this length as a cap for registration and matching
        private static readonly char[] StripChars = new char[] { ' ', '\t', '\r', '\n' };  // stripped from both ends before registration
        private const int AnchorLength = MinimumSecretLength;
        private const int ProbeLength = 8;  // chars compared from the middle of a candidate before the full comparison

        private readonly Dictionary<string, List<Bucket>> _scan;  // anchor -> buckets, longest first
        private readonly HashSet<string> _registered;
        private HashSet<string> _newSecrets;

        private sealed class Bucket
        {
            public readonly int Length;  // in UTF-16 chars, like the spans
            public readonly int ProbeOffset;
            public readonly int ProbeSize;
            public readonly HashSet<string> Probes = new HashSet<string>(StringComparer.Ordinal);
            public readonly HashSet<string> Values = new HashSet<string>(StringComparer.Ordinal);

            public Bucket(int length)
            {
                Length = length;
                ProbeSize = Math.Min(ProbeLength, length);
                ProbeOffset = Math.Max(0, length / 2 - ProbeSize / 2);
            }
        }

        /// <summary>
        /// Internal API: Used to register initial secrets known to Ansible.
        /// </summary>
        /// <param name="secrets">The initial secrets to register with the masker</param>
        public static void _RegisterAnsibleSecrets(IEnumerable<SecureString> secrets)
        {
            SecretMasker masker = _instance;

            foreach (SecureString secret in secrets)
            {
                masker.RegisterSecretImpl(secret);
            }

            masker.DrainNewSecretsImpl();
        }

        /// <summary>
        /// Drains any new secrets that have been registered since the last call to this method.
        /// Used to determine what secrets need to be sent to the Ansible controller for masking.
        /// </summary>
        /// <returns>The unique secrets that have been registered.</returns>
        public static HashSet<string> DrainNewSecrets()
        {
            return _instance.DrainNewSecretsImpl();
        }

        /// <summary>
        /// Registers a new secret with the masker.
        /// </summary>
        /// <param name="secret">The secret to register</param>
        public static void RegisterSecret(SecureString secret)
        {
            _instance.RegisterSecretImpl(secret);
        }

        /// <summary>
        /// Registers a new secret with the masker.
        /// Use the SecureString overload if possible to avoid AMSI logging in PowerShell.
        /// </summary>
        /// <param name="secret">The secret to register</param>
        public static void RegisterSecret(string secret)
        {
            _instance.RegisterSecretImpl(secret);
        }

        /// <summary>
        /// Masks any registered secrets found in the input string with the default placeholder "$REDACTED$".
        /// </summary>
        /// <param name="value">The input string to mask</param>
        /// <returns>The masked string</returns>
        public static string MaskString(string value)
        {
            return MaskString(value, "$REDACTED$");
        }

        /// <summary>
        /// Masks any registered secrets found in the input string with the specified placeholder.
        /// </summary>
        /// <param name="value">The input string to mask</param>
        /// <param name="maskPlaceholder">The placeholder to use for masking secrets</param>
        /// <returns>The masked string</returns>
        public static string MaskString(string value, string maskPlaceholder)
        {
            return _instance.MaskStringImpl(value, maskPlaceholder);
        }

        private SecretMasker()
        {
            _scan = new Dictionary<string, List<Bucket>>(StringComparer.Ordinal);
            _registered = new HashSet<string>(StringComparer.Ordinal);
            _newSecrets = new HashSet<string>(StringComparer.Ordinal);
        }

        private HashSet<string> DrainNewSecretsImpl()
        {
            HashSet<string> result = _newSecrets;
            _newSecrets = new HashSet<string>(StringComparer.Ordinal);
            return result;
        }

        private void RegisterSecretImpl(SecureString secret)
        {
            if (secret.Length == 0)
            {
                return;
            }

            IntPtr stringPtr = IntPtr.Zero;
            try
            {
                stringPtr = Marshal.SecureStringToBSTR(secret);
                string secretString = Marshal.PtrToStringBSTR(stringPtr);
                RegisterSecretImpl(secretString);
            }
            finally
            {
                if (stringPtr != IntPtr.Zero)
                {
                    Marshal.ZeroFreeBSTR(stringPtr);
                }
            }
        }

        private void RegisterSecretImpl(string secret)
        {
            if (secret == null)
            {
                return;
            }

            // Copies behaviour of Python to strip whitespace and trim to the
            // maximum length before registering.
            secret = TrimToCodePoints(secret.Trim(StripChars), MaximumSecretLength);
            if (CodePointCount(secret, 0, secret.Length) < MinimumSecretLength)
            {
                return;
            }

            if (!_registered.Add(secret))
            {
                return;
            }

            _newSecrets.Add(secret);

            // Register the literal value and the forms it takes once JSON encoded. The ASCII
            // form escapes non-ASCII characters as well (legacy module serialization profile),
            // the other form only escapes what JSON requires (modern profile). When the ASCII
            // form is the same as the literal value neither form can differ from it.
            AddValue(secret);

            string jsonAsciiForm = JsonEncode(secret, true);
            if (jsonAsciiForm != secret)
            {
                AddValue(jsonAsciiForm);
                AddValue(JsonEncode(secret, false));
            }
        }

        private void AddValue(string value)
        {
            string anchor = value.Substring(0, AnchorLength);

            List<Bucket> buckets;
            if (!_scan.TryGetValue(anchor, out buckets))
            {
                buckets = new List<Bucket>();
                _scan[anchor] = buckets;
            }

            Bucket bucket = buckets.Find(b => b.Length == value.Length);
            if (bucket == null)
            {
                bucket = new Bucket(value.Length);
                buckets.Add(bucket);

                // Buckets are kept longest first so FindSpans reports the spans at one position
                // longest first, the order MergeSpans relies on.
                buckets.Sort((a, b) => b.Length.CompareTo(a.Length));
            }

            bucket.Probes.Add(value.Substring(bucket.ProbeOffset, bucket.ProbeSize));
            bucket.Values.Add(value);
        }

        private static int CodePointCount(string value, int start, int end)
        {
            int count = end - start;
            for (int i = start; i < end - 1; i++)
            {
                if (char.IsSurrogatePair(value[i], value[i + 1]))
                {
                    count--;
                    i++;
                }
            }

            return count;
        }

        private static string TrimToCodePoints(string value, int maxCodePoints)
        {
            if (value.Length <= maxCodePoints)
            {
                return value;
            }

            int index = 0;
            for (int count = 0; count < maxCodePoints && index < value.Length; count++)
            {
                index += char.IsSurrogatePair(value, index) ? 2 : 1;
            }

            return index < value.Length ? value.Substring(0, index) : value;
        }

        /// <summary>
        /// Encodes a string as the Python json module would, without the surrounding quotes. With
        /// <paramref name="asciiOnly"/> every character outside the printable ASCII range is escaped as
        /// \uXXXX (ensure_ascii=True), otherwise only the characters JSON requires to be escaped are.
        /// </summary>
        private static string JsonEncode(string value, bool asciiOnly)
        {
            StringBuilder sb = null;

            for (int i = 0; i < value.Length; i++)
            {
                char c = value[i];
                string escaped = null;

                switch (c)
                {
                    case '"':
                        escaped = "\\\"";
                        break;
                    case '\\':
                        escaped = "\\\\";
                        break;
                    case '\n':
                        escaped = "\\n";
                        break;
                    case '\r':
                        escaped = "\\r";
                        break;
                    case '\t':
                        escaped = "\\t";
                        break;
                    case '\b':
                        escaped = "\\b";
                        break;
                    case '\f':
                        escaped = "\\f";
                        break;
                    default:
                        if (c < ' ' || (asciiOnly && c > '~'))
                        {
                            // Python escapes each UTF-16 code unit, so a surrogate pair becomes two escapes.
                            escaped = "\\u" + ((int)c).ToString("x4");
                        }
                        break;
                }

                if (escaped == null)
                {
                    if (sb != null)
                    {
                        sb.Append(c);
                    }
                    continue;
                }

                if (sb == null)
                {
                    sb = new StringBuilder(value.Length + 16);
                    sb.Append(value, 0, i);
                }
                sb.Append(escaped);
            }

            return sb == null ? value : sb.ToString();
        }

        private string MaskStringImpl(string value, string maskPlaceholder)
        {
            if (string.IsNullOrEmpty(value) || _scan.Count == 0)
            {
                return value;
            }

            List<int[]> spans = MergeSpans(value, FindSpans(value));
            if (spans.Count == 0)
            {
                return value;
            }

            StringBuilder sb = new StringBuilder(value.Length);
            int valuePos = 0;
            foreach (int[] span in spans)
            {
                sb.Append(value, valuePos, span[0] - valuePos);
                sb.Append(maskPlaceholder);
                valuePos = span[1];
            }
            sb.Append(value, valuePos, value.Length - valuePos);

            return sb.ToString();
        }

        /// <summary>
        /// Every occurrence of every registered value in <paramref name="value"/> as [start, end) spans.
        /// </summary>
        private List<int[]> FindSpans(string value)
        {
            List<int[]> spans = new List<int[]>();
            int valueLength = value.Length;

            // A value shorter than the anchor never enters the loop and yields no spans.
            for (int start = 0; start <= valueLength - AnchorLength; start++)
            {
                List<Bucket> buckets;
                if (!_scan.TryGetValue(value.Substring(start, AnchorLength), out buckets))
                {
                    continue;
                }

                foreach (Bucket bucket in buckets)
                {
                    int end = start + bucket.Length;
                    if (end > valueLength)
                    {
                        continue;
                    }

                    if (!bucket.Probes.Contains(value.Substring(start + bucket.ProbeOffset, bucket.ProbeSize)))
                    {
                        continue;
                    }

                    if (!bucket.Values.Contains(value.Substring(start, bucket.Length)))
                    {
                        continue;
                    }

                    spans.Add(new int[] { start, end });
                }
            }

            return spans;
        }

        /// <summary>
        /// Merges overlapping/touching spans into one placeholder each and drops the runs that do not
        /// qualify. Mirrors _merge_spans in _secrets.py, see there for the rules and examples.
        /// </summary>
        private static List<int[]> MergeSpans(string value, List<int[]> spans)
        {
            if (spans.Count == 0)
            {
                return spans;
            }

            List<int[]> result = new List<int[]>();

            int runStart = spans[0][0];
            int runEnd = spans[0][1];
            bool keep = SpanIsQualified(value, runStart, runEnd);

            for (int i = 1; i < spans.Count; i++)
            {
                int start = spans[i][0];
                int end = spans[i][1];

                if (start > runEnd)
                {
                    // Current run is complete, start new run with the current span.
                    if (keep)
                    {
                        result.Add(new int[] { runStart, runEnd });
                    }

                    runStart = start;
                    runEnd = end;
                    keep = SpanIsQualified(value, start, end);
                }
                else if (end > runEnd)
                {
                    // Span is inside or touching the current run and extends it.
                    runEnd = end;
                    keep = true;
                }
                else if (!keep)
                {
                    // Span lies inside the current run that is not qualified by its own merit.
                    keep = SpanIsQualified(value, start, end);
                }
            }

            if (keep)
            {
                result.Add(new int[] { runStart, runEnd });
            }

            return result;
        }

        private static bool SpanIsQualified(string value, int start, int end)
        {
            // Every code point is at most two chars, so a span longer than twice the limit in chars is
            // long whatever it contains and the code points only need counting below that.
            int length = end - start;
            if (length > MaximumShortSecretLength * 2 || CodePointCount(value, start, end) > MaximumShortSecretLength)
            {
                return true;
            }

            bool boundaryLeft = start == 0 || !IsAlphaNumeric(value, start - 1);
            bool boundaryRight = end == value.Length || !IsAlphaNumeric(value, end);
            return boundaryLeft && boundaryRight;
        }

        /// <summary>
        /// Matches Python's str.isalnum for the character at <paramref name="index"/>: any letter or number
        /// category, with a surrogate pair classified as the code point it encodes.
        /// </summary>
        private static bool IsAlphaNumeric(string value, int index)
        {
            if (index > 0 && char.IsLowSurrogate(value[index]) && char.IsHighSurrogate(value[index - 1]))
            {
                index--;
            }

            switch (CharUnicodeInfo.GetUnicodeCategory(value, index))
            {
                case UnicodeCategory.UppercaseLetter:
                case UnicodeCategory.LowercaseLetter:
                case UnicodeCategory.TitlecaseLetter:
                case UnicodeCategory.ModifierLetter:
                case UnicodeCategory.OtherLetter:
                case UnicodeCategory.DecimalDigitNumber:
                case UnicodeCategory.LetterNumber:
                case UnicodeCategory.OtherNumber:
                    return true;
                default:
                    return false;
            }
        }
    }
}
