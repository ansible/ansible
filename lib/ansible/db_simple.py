# (C) 2013, Stephen Fromm, <sfromm@gmail.com>

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

import json
import datetime

from sqlalchemy import *
from sqlalchemy.types import TypeDecorator, Text
from sqlalchemy.ext.declarative import declarative_base

class JSONEncodedDict(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

def now():
    return datetime.datetime.now()

Base = declarative_base()

class AnsibleResult(Base):
    __tablename__ = 'host_result'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=now())
    hostname = Column(String)
    module = Column(String)
    result = Column(String)
    data = Column(JSONEncodedDict)

    def __init__(self, hostname, module, result, data, timestamp=now()):
        self.hostname = hostname
        self.timestamp = timestamp
        self.data = data
        self.module = module
        self.result = result

    def __repr__(self):
        return "<AnsibleResult<'%s', '%s', '%s'>" % (self.hostname, self.module, self.result)
