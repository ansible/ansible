# (c) 2015, Jan-Piet Mens <jpmens(at)gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: dig
    author: Jan-Piet Mens (@jpmens) <jpmens(at)gmail.com>
    version_added: "1.9"
    short_description: query DNS using the dnspython library
    requirements:
      - dnspython (python library, http://www.dnspython.org/)
    description:
      - The dig lookup runs queries against DNS servers to retrieve DNS records for a specific name (FQDN - fully qualified domain name).
        It is possible to lookup any DNS record in this manner.
      - There is a couple of different syntaxes that can be used to specify what record should be retrieved, and for which name.
         It is also possible to explicitly specify the DNS server(s) to use for lookups.
      - In its simplest form, the dig lookup plugin can be used to retrieve an IPv4 address (DNS A record) associated with FQDN
      - In addition to (default) A record, it is also possible to specify a different record type that should be queried.
        This can be done by either passing-in additional parameter of format qtype=TYPE to the dig lookup, or by appending /TYPE to the FQDN being queried.
      - If multiple values are associated with the requested record, the results will be returned as a comma-separated list.
        In such cases you may want to pass option wantlist=True to the plugin, which will result in the record values being returned as a list
        over which you can iterate later on.
      - By default, the lookup will rely on system-wide configured DNS servers for performing the query.
        It is also possible to explicitly specify DNS servers to query using the @DNS_SERVER_1,DNS_SERVER_2,...,DNS_SERVER_N notation.
        This needs to be passed-in as an additional parameter to the lookup
    options:
      _terms:
        description: domain(s) to query
      qtype:
        description: record type to query
        default: 'A'
        choices: [A, ALL, AAAA, CNAME, DNAME, DLV, DNSKEY, DS, HINFO, LOC, MX, NAPTR, NS, NSEC3PARAM, PTR, RP, RRSIG, SOA, SPF, SRV, SSHFP, TLSA, TXT]
      flat:
        description: If 0 each record is returned as a dictionary, otherwise a string
        default: 1
    notes:
      - ALL is not a record per-se, merely the listed fields are available for any record results you retrieve in the form of a dictionary.
      - While the 'dig' lookup plugin supports anything which dnspython supports out of the box, only a subset can be converted into a dictionary.
      - If you need to obtain the AAAA record (IPv6 address), you must specify the record type explicitly.
        Syntax for specifying the record type is shown in the examples below.
      - The trailing dot in most of the examples listed is purely optional, but is specified for completeness/correctness sake.
"""

EXAMPLES = """
- name: Simple A record (IPV4 address) lookup for example.com
  debug: msg="{{ lookup('dig', 'example.com.')}}"

- name: "The TXT record for example.org."
  debug: msg="{{ lookup('dig', 'example.org.', 'qtype=TXT') }}"

- name: "The TXT record for example.org, alternative syntax."
  debug: msg="{{ lookup('dig', 'example.org./TXT') }}"

- name: use in a loop
  debug: msg="MX record for gmail.com {{ item }}"
  with_items: "{{ lookup('dig', 'gmail.com./MX', wantlist=True) }}"

- debug: msg="Reverse DNS for 192.0.2.5 is {{ lookup('dig', '192.0.2.5/PTR') }}"
- debug: msg="Reverse DNS for 192.0.2.5 is {{ lookup('dig', '5.2.0.192.in-addr.arpa./PTR') }}"
- debug: msg="Reverse DNS for 192.0.2.5 is {{ lookup('dig', '5.2.0.192.in-addr.arpa.', 'qtype=PTR') }}"
- debug: msg="Querying 198.51.100.23 for IPv4 address for example.com. produces {{ lookup('dig', 'example.com', '@198.51.100.23') }}"

- debug: msg="XMPP service for gmail.com. is available at {{ item.target }} on port {{ item.port }}"
  with_items: "{{ lookup('dig', '_xmpp-server._tcp.gmail.com./SRV', 'flat=0', wantlist=True) }}"
"""

RETURN = """
  _list:
    description:
      - list of composed strings or dictonaries with key and value
        If a dictionary, fields shows the keys returned depending on query type
    fields:
       ALL: owner, ttl, type
       A: address
       AAAA: address
       CNAME: target
       DNAME: target
       DLV: algorithm, digest_type, key_tag, digest
       DNSKEY: flags, algorithm, protocol, key
       DS: algorithm, digest_type, key_tag, digest
       HINFO:  cpu, os
       LOC: latitude, longitude, altitude, size, horizontal_precision, vertical_precision
       MX: preference, exchange
       NAPTR: order, preference, flags, service, regexp, replacement
       NS: target
       NSEC3PARAM: algorithm, flags, iterations, salt
       PTR: target
       RP: mbox, txt
       SOA: mname, rname, serial, refresh, retry, expire, minimum
       SPF: strings
       SRV: priority, weight, port, target
       SSHFP: algorithm, fp_type, fingerprint
       TLSA: usage, selector, mtype, cert
       TXT: strings
"""

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_native
import socket

try:
    import dns.exception
    import dns.name
    import dns.resolver
    import dns.reversename
    import dns.rdataclass
    from dns.rdatatype import (A, AAAA, CNAME, DLV, DNAME, DNSKEY, DS, HINFO, LOC,
                               MX, NAPTR, NS, NSEC3PARAM, PTR, RP, SOA, SPF, SRV, SSHFP, TLSA, TXT)
    HAVE_DNS = True
except ImportError:
    HAVE_DNS = False


def make_rdata_dict(rdata):
    ''' While the 'dig' lookup plugin supports anything which dnspython supports
        out of the box, the following supported_types list describes which
        DNS query types we can convert to a dict.

        Note: adding support for RRSIG is hard work. :)
    '''
    supported_types = {
        A: ['address'],
        AAAA: ['address'],
        CNAME: ['target'],
        DNAME: ['target'],
        DLV: ['algorithm', 'digest_type', 'key_tag', 'digest'],
        DNSKEY: ['flags', 'algorithm', 'protocol', 'key'],
        DS: ['algorithm', 'digest_type', 'key_tag', 'digest'],
        HINFO: ['cpu', 'os'],
        LOC: ['latitude', 'longitude', 'altitude', 'size', 'horizontal_precision', 'vertical_precision'],
        MX: ['preference', 'exchange'],
        NAPTR: ['order', 'preference', 'flags', 'service', 'regexp', 'replacement'],
        NS: ['target'],
        NSEC3PARAM: ['algorithm', 'flags', 'iterations', 'salt'],
        PTR: ['target'],
        RP: ['mbox', 'txt'],
        # RRSIG: ['algorithm', 'labels', 'original_ttl', 'expiration', 'inception', 'signature'],
        SOA: ['mname', 'rname', 'serial', 'refresh', 'retry', 'expire', 'minimum'],
        SPF: ['strings'],
        SRV: ['priority', 'weight', 'port', 'target'],
        SSHFP: ['algorithm', 'fp_type', 'fingerprint'],
        TLSA: ['usage', 'selector', 'mtype', 'cert'],
        TXT: ['strings'],
    }

    rd = {}

    if rdata.rdtype in supported_types:
        fields = supported_types[rdata.rdtype]
        for f in fields:
            val = rdata.__getattribute__(f)

            if isinstance(val, dns.name.Name):
                val = dns.name.Name.to_text(val)

            if rdata.rdtype == DLV and f == 'digest':
                val = dns.rdata._hexify(rdata.digest).replace(' ', '')
            if rdata.rdtype == DS and f == 'digest':
                val = dns.rdata._hexify(rdata.digest).replace(' ', '')
            if rdata.rdtype == DNSKEY and f == 'key':
                val = dns.rdata._base64ify(rdata.key).replace(' ', '')
            if rdata.rdtype == NSEC3PARAM and f == 'salt':
                val = dns.rdata._hexify(rdata.salt).replace(' ', '')
            if rdata.rdtype == SSHFP and f == 'fingerprint':
                val = dns.rdata._hexify(rdata.fingerprint).replace(' ', '')
            if rdata.rdtype == TLSA and f == 'cert':
                val = dns.rdata._hexify(rdata.cert).replace(' ', '')

            rd[f] = val

    return rd


# ==============================================================
# dig: Lookup DNS records
#
# --------------------------------------------------------------

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        '''
        terms contains a string with things to `dig' for. We support the
        following formats:
            example.com                                     # A record
            example.com  qtype=A                            # same
            example.com/TXT                                 # specific qtype
            example.com  qtype=txt                          # same
            192.0.2.23/PTR                                 # reverse PTR
              ^^ shortcut for 23.2.0.192.in-addr.arpa/PTR
            example.net/AAAA  @nameserver                   # query specified server
                               ^^^ can be comma-sep list of names/addresses

            ... flat=0                                      # returns a dict; default is 1 == string
        '''

        if HAVE_DNS is False:
            raise AnsibleError("The dig lookup requires the python 'dnspython' library and it is not installed")

        # Create Resolver object so that we can set NS if necessary
        myres = dns.resolver.Resolver(configure=True)
        edns_size = 4096
        myres.use_edns(0, ednsflags=dns.flags.DO, payload=edns_size)

        domain = None
        qtype = 'A'
        flat = True
        rdclass = dns.rdataclass.from_text('IN')

        for t in terms:
            if t.startswith('@'):       # e.g. "@10.0.1.2,192.0.2.1" is ok.
                nsset = t[1:].split(',')
                for ns in nsset:
                    nameservers = []
                    # Check if we have a valid IP address. If so, use that, otherwise
                    # try to resolve name to address using system's resolver. If that
                    # fails we bail out.
                    try:
                        socket.inet_aton(ns)
                        nameservers.append(ns)
                    except Exception:
                        try:
                            nsaddr = dns.resolver.query(ns)[0].address
                            nameservers.append(nsaddr)
                        except Exception as e:
                            raise AnsibleError("dns lookup NS: %s" % to_native(e))
                    myres.nameservers = nameservers
                continue
            if '=' in t:
                try:
                    opt, arg = t.split('=')
                except Exception:
                    pass

                if opt == 'qtype':
                    qtype = arg.upper()
                elif opt == 'flat':
                    flat = int(arg)
                elif opt == 'class':
                    try:
                        rdclass = dns.rdataclass.from_text(arg)
                    except Exception as e:
                        raise AnsibleError("dns lookup illegal CLASS: %s" % to_native(e))

                continue

            if '/' in t:
                try:
                    domain, qtype = t.split('/')
                except Exception:
                    domain = t
            else:
                domain = t

        # print "--- domain = {0} qtype={1} rdclass={2}".format(domain, qtype, rdclass)

        ret = []

        if qtype.upper() == 'PTR':
            try:
                n = dns.reversename.from_address(domain)
                domain = n.to_text()
            except dns.exception.SyntaxError:
                pass
            except Exception as e:
                raise AnsibleError("dns.reversename unhandled exception %s" % to_native(e))

        try:
            answers = myres.query(domain, qtype, rdclass=rdclass)
            for rdata in answers:
                s = rdata.to_text()
                if qtype.upper() == 'TXT':
                    s = s[1:-1]  # Strip outside quotes on TXT rdata

                if flat:
                    ret.append(s)
                else:
                    try:
                        rd = make_rdata_dict(rdata)
                        rd['owner'] = answers.canonical_name.to_text()
                        rd['type'] = dns.rdatatype.to_text(rdata.rdtype)
                        rd['ttl'] = answers.rrset.ttl
                        rd['class'] = dns.rdataclass.to_text(rdata.rdclass)

                        ret.append(rd)
                    except Exception as e:
                        ret.append(str(e))

        except dns.resolver.NXDOMAIN:
            ret.append('NXDOMAIN')
        except dns.resolver.NoAnswer:
            ret.append("")
        except dns.resolver.Timeout:
            ret.append('')
        except dns.exception.DNSException as e:
            raise AnsibleError("dns.resolver unhandled exception %s" % to_native(e))

        return ret
