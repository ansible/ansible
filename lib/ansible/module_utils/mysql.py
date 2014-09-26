# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# Copyright (c), Michael DeHaan <michael.dehaan@gmail.com>, 2012-2013
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import ConfigParser

def mycnf_options():
    config_options = dict()
    config = ConfigParser.RawConfigParser()
    mycnf = os.path.expanduser('~/.my.cnf')
    if not os.path.exists(mycnf):
        return False
    try:
        config.readfp(open(mycnf))
    except (IOError):
        return False
    except:
        config = _safe_cnf_load(config, mycnf)

    # We support two forms of passwords in .my.cnf, both pass= and password=,
    # as these are both supported by MySQL.
    try:
        config_options['passwd'] = config_get(config, 'client', 'password');
    except (ConfigParser.NoOptionError):
        try:
            config_options['passwd'] = config_get(config, 'client', 'pass');
        except (ConfigParser.NoOptionError):
            pass

    # get the user if we can
    try:
        config_options['user'] = config_get(config, 'client', 'user')
    except (ConfigParser.NoOptionError):
        pass

    # get the socket if we can
    try:
        config_options['socket'] = config_get(config, 'client', 'socket')
    except (ConfigParser.NoOptionError):
        pass

    return config_options

def _safe_cnf_load(config, path):

    data = {'user':'', 'password':'', 'socket': ''}

    # read in user/pass
    f = open(path, 'r')
    for line in f.readlines():
        line = line.strip()
        if line.startswith('user='):
            data['user'] = line.split('=', 1)[1].strip()
        if line.startswith('password=') or line.startswith('pass='):
            data['password'] = line.split('=', 1)[1].strip()
        if line.startswith('socket='):
            data['socket'] = line.split('=', 1)[1].strip()
    f.close()

    # write out a new cnf file with only user/pass   
    fh, newpath = tempfile.mkstemp(prefix=path + '.')
    f = open(newpath, 'wb')
    f.write('[client]\n')
    f.write('user=%s\n' % data['user'])
    f.write('password=%s\n' % data['password'])
    f.write('socket=%s\n' % data['socket'])
    f.close()

    config.readfp(open(newpath))
    os.remove(newpath)
    return config

