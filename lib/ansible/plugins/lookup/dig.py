# (c) 2015, Jan-Piet Mens <jpmens(at)gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
import socket

try:
    import dns.resolver
    import dns.reversename
    from dns.rdatatype import (A, AAAA, CNAME, DLV, DNAME, DNSKEY, DS, HINFO, LOC,
            MX, NAPTR, NS, NSEC3PARAM, PTR, RP, SOA, SPF, SRV, SSHFP, TLSA, TXT)
    import dns.exception
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
            A           : ['address'],
            AAAA        : ['address'],
            CNAME       : ['target'],
            DNAME       : ['target'],
            DLV         : ['algorithm', 'digest_type', 'key_tag', 'digest'],
            DNSKEY      : ['flags', 'algorithm', 'protocol', 'key'],
            DS          : ['algorithm', 'digest_type', 'key_tag', 'digest'],
            HINFO       : ['cpu', 'os'],
            LOC         : ['latitude', 'longitude', 'altitude', 'size', 'horizontal_precision', 'vertical_precision'],
            MX          : ['preference', 'exchange'],
            NAPTR       : ['order', 'preference', 'flags', 'service', 'regexp', 'replacement'],
            NS          : ['target'],
            NSEC3PARAM  : ['algorithm', 'flags', 'iterations', 'salt'],
            PTR         : ['target'],
            RP          : ['mbox', 'txt'],
            # RRSIG       : ['algorithm', 'labels', 'original_ttl', 'expiration', 'inception', 'signature'],
            SOA         : ['mname', 'rname', 'serial', 'refresh', 'retry', 'expire', 'minimum'],
            SPF         : ['strings'],
            SRV         : ['priority', 'weight', 'port', 'target'],
            SSHFP       : ['algorithm', 'fp_type', 'fingerprint'],
            TLSA        : ['usage', 'selector', 'mtype', 'cert'],
            TXT         : ['strings'],
        }

    rd = {}

    if rdata.rdtype in supported_types:
        fields = supported_types[rdata.rdtype]
        for f in fields:
            val     = rdata.__getattribute__(f)

            if type(val) == dns.name.Name:
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


            rd[f]   = val

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
            192.168.1.2/PTR                                 # reverse PTR
              ^^ shortcut for 2.1.168.192.in-addr.arpa/PTR
            example.net/AAAA  @nameserver                   # query specified server
                               ^^^ can be comma-sep list of names/addresses

            ... flat=0                                      # returns a dict; default is 1 == string
        '''

        if HAVE_DNS == False:
            raise AnsibleError("Can't LOOKUP(dig): module dns.resolver is not installed")

        # Create Resolver object so that we can set NS if necessary
        myres = dns.resolver.Resolver()
        edns_size = 4096
        myres.use_edns(0, ednsflags=dns.flags.DO, payload=edns_size)

        domain = None
        qtype  = 'A'
        flat   = True

        for t in terms:
            if t.startswith('@'):       # e.g. "@10.0.1.2,192.168.1.1" is ok.
                nsset = t[1:].split(',')
                nameservers = []
                for ns in nsset:
                    # Check if we have a valid IP address. If so, use that, otherwise
                    # try to resolve name to address using system's resolver. If that
                    # fails we bail out.
                    try:
                        socket.inet_aton(ns)
                        nameservers.append(ns)
                    except:
                        try:
                            nsaddr = dns.resolver.query(ns)[0].address
                            nameservers.append(nsaddr)
                        except Exception as e:
                            raise AnsibleError("dns lookup NS: ", str(e))
                    myres.nameservers = nameservers
                continue
            if '=' in t:
                try:
                    opt, arg = t.split('=')
                except:
                    pass

                if opt == 'qtype':
                    qtype = arg.upper()
                elif opt == 'flat':
                    flat = int(arg)

                continue

            if '/' in t:
                try:
                    domain, qtype = t.split('/')
                except:
                    domain = t
            else:
                domain = t

        # print "--- domain = {0} qtype={1}".format(domain, qtype)

        ret = []

        if qtype.upper() == 'PTR':
            try:
                n = dns.reversename.from_address(domain)
                domain = n.to_text()
            except dns.exception.SyntaxError:
                pass
            except Exception as e:
                raise AnsibleError("dns.reversename unhandled exception", str(e))

        try:
            answers = myres.query(domain, qtype)
            for rdata in answers:
                s = rdata.to_text()
                if qtype.upper() == 'TXT':
                    s = s[1:-1]  # Strip outside quotes on TXT rdata

                if flat:
                    ret.append(s)
                else:
                    try:
                        rd = make_rdata_dict(rdata)
                        rd['owner']     = answers.canonical_name.to_text()
                        rd['type']      = dns.rdatatype.to_text(rdata.rdtype)
                        rd['ttl']       = answers.rrset.ttl

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
            raise AnsibleError("dns.resolver unhandled exception", e)

        return ret
