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

        private readonly Node _root;
        private readonly HashSet<string> _registered;
        private HashSet<string> _newSecrets;
        private bool _dirty;

        private sealed class Node
        {
            public readonly Dictionary<char, Node> Children = new Dictionary<char, Node>();
            public readonly int Depth;
            public bool IsTerminal;  // a registered value ends here; its length in chars is Depth
            public int CodePoints;  // length of that value in code points, the unit the length rules use
            public Node Fail;  // longest proper suffix of this node's path that is also a path
            public Node Output;  // nearest terminal node on the fail chain, excluding this node

            public Node(int depth)
            {
                Depth = depth;
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
            _root = new Node(0);
            _root.Fail = _root;
            _registered = new HashSet<string>(StringComparer.Ordinal);
            _newSecrets = new HashSet<string>(StringComparer.Ordinal);
            _dirty = false;
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
            // Lengths are measured in code points, as Python does, so a surrogate pair counts once.
            if (string.IsNullOrEmpty(secret) || CodePointCount(secret) < MinimumSecretLength)
            {
                return;
            }

            // Overly long secrets are trimmed before registration so only the
            // first MaximumSecretLength characters are matched and masked.
            secret = TrimToCodePoints(secret, MaximumSecretLength);

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
            Node node = _root;
            foreach (char c in value)
            {
                Node child;
                if (!node.Children.TryGetValue(c, out child))
                {
                    child = new Node(node.Depth + 1);
                    node.Children[c] = child;
                    _dirty = true;
                }
                node = child;
            }

            if (!node.IsTerminal)
            {
                node.IsTerminal = true;
                node.CodePoints = CodePointCount(value);
                _dirty = true;
            }
        }

        private static int CodePointCount(string value)
        {
            int count = value.Length;
            for (int i = 0; i < value.Length - 1; i++)
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

        private void BuildLinks()
        {
            // Standard breadth first computation of the fail and output links.
            Queue<Node> queue = new Queue<Node>();

            foreach (Node child in _root.Children.Values)
            {
                child.Fail = _root;
                child.Output = null;
                queue.Enqueue(child);
            }

            while (queue.Count > 0)
            {
                Node node = queue.Dequeue();

                foreach (KeyValuePair<char, Node> edge in node.Children)
                {
                    char c = edge.Key;
                    Node child = edge.Value;

                    Node fail = node.Fail;
                    Node target;
                    while (!fail.Children.TryGetValue(c, out target) && fail != _root)
                    {
                        fail = fail.Fail;
                    }

                    child.Fail = target ?? _root;
                    child.Output = child.Fail.IsTerminal ? child.Fail : child.Fail.Output;
                    queue.Enqueue(child);
                }
            }

            _dirty = false;
        }

        private string MaskStringImpl(string value, string maskPlaceholder)
        {
            if (string.IsNullOrEmpty(value) || _registered.Count == 0)
            {
                return value;
            }

            if (_dirty)
            {
                BuildLinks();
            }

            List<int[]> spans = FindSpans(value);
            if (spans.Count == 0)
            {
                return value;
            }

            MergeSpans(spans);

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
        /// Every occurrence of every registered value in <paramref name="value"/> as [start, end) spans,
        /// overlapping included, except short values that do not sit at a word boundary.
        /// </summary>
        private List<int[]> FindSpans(string value)
        {
            List<int[]> spans = new List<int[]>();
            Node state = _root;

            for (int i = 0; i < value.Length; i++)
            {
                char c = value[i];

                Node next;
                while (!state.Children.TryGetValue(c, out next) && state != _root)
                {
                    state = state.Fail;
                }
                state = next ?? _root;

                // every registered value ending at this index: the state's own then the shorter suffixes
                Node hit = state.IsTerminal ? state : state.Output;
                while (hit != null)
                {
                    int start = i - hit.Depth + 1;
                    int end = i + 1;

                    if (hit.CodePoints > MaximumShortSecretLength || SitsAtBoundary(value, start, end))
                    {
                        spans.Add(new int[] { start, end });
                    }

                    hit = hit.Output;
                }
            }

            return spans;
        }

        /// <summary>
        /// Sorts spans and merges any that overlap or touch into one, so one placeholder covers them all.
        /// </summary>
        private static void MergeSpans(List<int[]> spans)
        {
            if (spans.Count < 2)
            {
                return;
            }

            spans.Sort((a, b) => a[0] != b[0] ? a[0].CompareTo(b[0]) : a[1].CompareTo(b[1]));

            int merged = 0;
            for (int i = 1; i < spans.Count; i++)
            {
                int[] last = spans[merged];
                int[] current = spans[i];

                if (current[0] <= last[1])
                {
                    if (current[1] > last[1])
                    {
                        last[1] = current[1];
                    }
                }
                else
                {
                    merged++;
                    spans[merged] = current;
                }
            }

            spans.RemoveRange(merged + 1, spans.Count - merged - 1);
        }

        private static bool SitsAtBoundary(string value, int start, int end)
        {
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
