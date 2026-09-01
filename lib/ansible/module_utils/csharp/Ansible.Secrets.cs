using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Security;
using System.Text;

namespace Ansible.Secrets
{
    public class SecretMasker
    {
        // Not marked readonly so integration tests can reset the singleton to a
        // pristine instance via reflection between test cases (setting a static
        // readonly field via reflection is not supported on CoreCLR).
        private static SecretMasker _instance = new SecretMasker();

        private int[] _failureLink;
        private int[] _outputLink;
        private int[] _patternLength;
        private int _nodeCount;

        private readonly Dictionary<long, int> _trieGoto;
        private readonly HashSet<char> _alphabet;

        private int[] _transitions;
        private int[] _charToIndex;
        private int _alphaSize;
        private char[] _prevAlpha;

        public readonly HashSet<string> _registered;
        private HashSet<string> _newSecrets;
        private bool _dirty;

        private const int InitialNodeCapacity = 64;

        // Mirrors ansible.module_utils._internal._secrets. Secrets shorter than
        // MinimumSecretLength are never registered; secrets between Minimum and
        // MaximumShortSecretLength ("short") are only masked when they sit at a
        // word boundary. Longer secrets are always masked.
        private const int MinimumSecretLength = 4;
        private const int MaximumShortSecretLength = 6;

        public static SecretMasker Instance
        {
            get
            {
                return _instance;
            }
        }

        /// <summary>
        /// Internal API: Used to register initial secrets known to Ansible.
        /// </summary>
        /// <param name="secrets">The initial secrets to register with the masker</param>
        public static void _RegisterAnsibleSecrets(IEnumerable<SecureString> secrets)
        {
            SecretMasker masker = SecretMasker.Instance;

            foreach (SecureString secret in secrets)
            {
                masker.RegisterSecret(secret);
            }

            masker.DrainNewSecrets();
        }

        private SecretMasker()
        {
            _failureLink = new int[InitialNodeCapacity];
            _outputLink = new int[InitialNodeCapacity];
            _patternLength = new int[InitialNodeCapacity];
            _nodeCount = 1;

            _trieGoto = new Dictionary<long, int>();
            _alphabet = new HashSet<char>();

            _transitions = Array.Empty<int>();
            _charToIndex = null;
            _alphaSize = 0;
            _prevAlpha = Array.Empty<char>();

            _registered = new HashSet<string>(StringComparer.Ordinal);
            _newSecrets = new HashSet<string>(StringComparer.Ordinal);
            _dirty = false;
        }

        /// <summary>
        /// Drains any new secrets that have been registered since the last call to this method.
        /// Used to determine what secrets need to be sent to the Ansible controller for masking.
        /// </summary>
        /// <returns>The unique secrets that have been registered.</returns>
        public HashSet<string> DrainNewSecrets()
        {
            HashSet<string> result = _newSecrets;
            _newSecrets = new HashSet<string>(StringComparer.Ordinal);
            return result;
        }

        /// <summary>
        /// Registers a new secret with the masker.
        /// </summary>
        /// <param name="secret">The secret to register</param>
        public void RegisterSecret(SecureString secret)
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
                RegisterSecret(secretString);
            }
            finally
            {
                if (stringPtr != IntPtr.Zero)
                {
                    Marshal.ZeroFreeBSTR(stringPtr);
                }
            }
        }

        /// <summary>
        /// Registers a new secret with the masker.
        /// Use the SecureString overload if possible to avoid AMSI logging in PowerShell.
        /// </summary>
        /// <param name="secret">The secret to register</param>
        public void RegisterSecret(string secret)
        {
            if (string.IsNullOrEmpty(secret) || secret.Length < MinimumSecretLength)
            {
                return;
            }

            if (!_registered.Add(secret))
            {
                return;
            }

            int current = 0;
            for (int i = 0; i < secret.Length; i++)
            {
                char c = secret[i];
                _alphabet.Add(c);

                long key = ((long)current << 16) | (long)c;
                int next = 0;
                if (!_trieGoto.TryGetValue(key, out next))
                {
                    next = _nodeCount++;
                    EnsureNodeCapacity(_nodeCount);
                    _trieGoto[key] = next;
                }
                current = next;
            }

            if (_patternLength[current] == 0)
            {
                _patternLength[current] = secret.Length;
            }

            _dirty = true;
            _newSecrets.Add(secret);

            return;
        }

        /// <summary>
        /// Masks any registered secrets found in the input string with the default placeholder "$REDACTED$".
        /// </summary>
        /// <param name="value">The input string to mask</param>
        /// <returns>The masked string</returns>
        public string MaskString(string value)
        {
            return MaskString(value, "$REDACTED$");
        }

        /// <summary>
        /// Masks any registered secrets found in the input string with the specified placeholder.
        /// </summary>
        /// <param name="value">The input string to mask</param>
        /// <param name="maskPlaceholder">The placeholder to use for masking secrets</param>
        /// <returns>The masked string</returns>
        public string MaskString(string value, string maskPlaceholder)
        {
            if (string.IsNullOrEmpty(value) || _registered.Count == 0)
            {
                return value;
            }

            if (_dirty)
            {
                BuildAutomaton();
                _dirty = false;
            }

            // Leftmost-longest, non-overlapping matching, mirroring the pure-Python
            // Aho-Corasick iter_long implementation in _ahocorasick.py. Fail links are
            // followed only while seeking (never while extending) and on a commit we
            // resume at the character after the match to re-scan any probe overshoot
            // while staying non-overlapping. Only matches surviving the short-secret
            // boundary check (see MaskSpan) are actually redacted.
            StringBuilder sb = null;
            int valuePos = 0;

            int state = 0;
            int i = 0;
            int length = value.Length;

            bool haveCandidate = false;
            int candidateStart = 0;
            int candidateEnd = 0;

            while (i < length)
            {
                char c = value[i];
                long key = ((long)state << 16) | (long)c;

                int next;
                if (_trieGoto.TryGetValue(key, out next))
                {
                    // Descend the goto edge; record a match if it is at least as leftward.
                    state = next;
                    int matchLen = GetLongestMatch(state);
                    if (matchLen > 0)
                    {
                        int start = i - matchLen + 1;
                        if (!haveCandidate || start <= candidateStart)
                        {
                            candidateStart = start;
                            candidateEnd = i;
                            haveCandidate = true;
                        }
                    }
                    i++;
                }
                else if (haveCandidate)
                {
                    // Extending dead-ended: commit the candidate and resume past its end.
                    sb = MaskSpan(value, maskPlaceholder, sb, ref valuePos, candidateStart, candidateEnd + 1);
                    i = candidateEnd + 1;
                    state = 0;
                    haveCandidate = false;
                }
                else if (state == 0)
                {
                    // Seeking with no edge at the un-seeded root: skip this char.
                    i++;
                }
                else
                {
                    // Seeking: follow one fail link and re-try the goto next iteration.
                    state = _failureLink[state];
                }
            }

            if (haveCandidate)
            {
                sb = MaskSpan(value, maskPlaceholder, sb, ref valuePos, candidateStart, candidateEnd + 1);
            }

            if (sb == null)
            {
                return value;
            }

            sb.Append(value, valuePos, value.Length - valuePos);
            return sb.ToString();
        }

        /// <summary>
        /// Redacts a matched span into <paramref name="sb"/> unless it is a short secret
        /// that does not sit at a word boundary, in which case the text is left untouched.
        /// </summary>
        private static StringBuilder MaskSpan(string value, string maskPlaceholder, StringBuilder sb, ref int valuePos, int start, int end)
        {
            int spanLength = end - start;
            if (IsShortSecret(spanLength) && !SitsAtBoundary(value, start, end))
            {
                return sb;
            }

            if (sb == null)
            {
                sb = new StringBuilder(value.Length);
            }
            sb.Append(value, valuePos, start - valuePos);
            sb.Append(maskPlaceholder);
            valuePos = end;
            return sb;
        }

        private static bool IsShortSecret(int length)
        {
            return length >= MinimumSecretLength && length <= MaximumShortSecretLength;
        }

        private static bool SitsAtBoundary(string value, int start, int end)
        {
            bool atBeginning = start == 0;
            bool atEnd = end == value.Length;
            bool boundaryLeft = atBeginning || !IsAlphaNumeric(value[start - 1]);
            bool boundaryRight = atEnd || !IsAlphaNumeric(value[end]);
            return boundaryLeft && boundaryRight;
        }

        private static bool IsAlphaNumeric(char c)
        {
            // Matches Python's str.isalnum for the character classes secret masking cares about.
            return char.IsLetterOrDigit(c);
        }

        private void EnsureNodeCapacity(int needed)
        {
            if (needed <= _failureLink.Length)
                return;
            int newCap = Math.Max(_failureLink.Length * 2, needed);
            Array.Resize(ref _failureLink, newCap);
            Array.Resize(ref _outputLink, newCap);
            Array.Resize(ref _patternLength, newCap);
        }

        private int GetLongestMatch(int state)
        {
            if (state == 0)
            {
                return 0;
            }

            if (_patternLength[state] > 0)
            {
                return _patternLength[state];
            }

            int outLink = _outputLink[state];
            if (outLink > 0)
            {
                return _patternLength[outLink];
            }

            return 0;
        }

        private void BuildAutomaton()
        {
            if (_charToIndex == null)
            {
                _charToIndex = new int[65536];
                for (int i = 0; i < _charToIndex.Length; i++)
                {
                    _charToIndex[i] = -1;
                }
            }
            else
            {
                for (int i = 0; i < _prevAlpha.Length; i++)
                {
                    _charToIndex[_prevAlpha[i]] = -1;
                }
            }

            char[] alpha = new char[_alphabet.Count];
            _alphabet.CopyTo(alpha);
            _alphaSize = alpha.Length;
            for (int i = 0; i < alpha.Length; i++)
                _charToIndex[alpha[i]] = i;
            _prevAlpha = alpha;

            _transitions = new int[_nodeCount * _alphaSize];

            foreach (KeyValuePair<long, int> kvp in _trieGoto)
            {
                int fromState = (int)(kvp.Key >> 16);
                int ci = _charToIndex[(char)(kvp.Key & 0xFFFF)];
                _transitions[fromState * _alphaSize + ci] = kvp.Value;
            }

            for (int i = 0; i < _nodeCount; i++)
            {
                _failureLink[i] = 0;
                _outputLink[i] = 0;
            }

            Queue<int> queue = new Queue<int>();

            for (int ai = 0; ai < _alphaSize; ai++)
            {
                int child = _transitions[ai];
                if (child != 0)
                {
                    _failureLink[child] = 0;
                    queue.Enqueue(child);
                }
            }

            while (queue.Count > 0)
            {
                int u = queue.Dequeue();
                int uBase = u * _alphaSize;
                int failBase = _failureLink[u] * _alphaSize;

                for (int ai = 0; ai < _alphaSize; ai++)
                {
                    int v = _transitions[uBase + ai];
                    if (v != 0)
                    {
                        int fv = _transitions[failBase + ai];
                        if (fv != v)
                        {
                            _failureLink[v] = fv;
                        }
                        else
                        {
                            _failureLink[v] = 0;
                        }

                        int fl = _failureLink[v];
                        if (_patternLength[fl] > 0)
                        {
                            _outputLink[v] = fl;
                        }
                        else
                        {
                            _outputLink[v] = _outputLink[fl];
                        }

                        queue.Enqueue(v);
                    }
                    else
                    {
                        _transitions[uBase + ai] = _transitions[failBase + ai];
                    }
                }
            }
        }
    }
}
