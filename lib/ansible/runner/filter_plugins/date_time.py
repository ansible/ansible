# (c) 2015, Steve Gargan <steve.gargan@gmail.com>
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
#
# Custom jinja filters that are useful in Ansible conditionals and variable expansions
# related to dates and times.
#
import time
from datetime import datetime, timedelta 
from time import mktime as mktime
from ansible import errors

# simple common formats
date_and_time_24h = '%d %b %Y %H:%M:%S'
date_and_time_12h = '%d %b %Y %I:%M:%S %p'
date_and_time_iso = '%Y-%m-%dT%H:%M:%SZ'
date_and_time_iso_micro = '%Y-%m-%dT%H:%M:%S.%fZ'
date_basic = '%d %b %Y'
date_us = '%m/%d/%y'
time_24h = '%H:%M:%S' 
time_12h = '%I:%M:%S %p' 

common_formats = [date_and_time_24h, date_and_time_12h, date_and_time_iso, 
                    date_and_time_iso_micro,date_basic, date_us, time_24h, time_12h]

# Units for date arithmetic, timedelta punts on month/year arithmetic
# so we skip it too. possilby revisit with dateutils library.
seconds_units = ['s', 'secs', 'seconds'] 
min_units  = ['m', 'mins', 'minutes'] 
hour_units    = ['h', 'hour', 'hours'] 
day_units     = ['d', 'days', 'day']
year_units    = ['y', 'yrs', 'years']

time_units = sum([seconds_units, min_units, hour_units,
               day_units, year_units], [])

def to_date_str(date, fmt):
    '''format the date using the given format''' 
    if type(date) in [str, unicode]:
        date = _convert_datetime(date)  
        
    return datetime.strftime(date, fmt)
    
def to_date(date, fmt=None):
    ''' converts a date string into a date object for comaprison'''
    if type(date) == str:
        if date.lower() == 'today':
            return datetime.today()
        elif date.lower() == 'now':
            return datetime.now()
    return _convert_datetime(date, fmt)

def _future(date, num, units):
    '''calculates a date ahead a given amount in the future'''
    return _convert_datetime(date) + _get_delta(num, units)

def _past(date, num, units):
    '''calculates a date a given amount in the past'''
    return _convert_datetime(date) - _get_delta(num, units)

def _get_delta(num, unit):
    ''' creates a delta for date arithmetic '''
    if not unit in time_units:
        raise errors.AnsibleFilterError("Date/time arithmetic required valid unit. " \
                                   "Given '%s' is not one of '%s' " % (unit, time_units))
    if unit in seconds_units:
        delta = timedelta(seconds=num)
    elif unit in min_units:
        delta = timedelta(minutes=num)
    elif unit in hour_units:
        delta = timedelta(hours=num)
    elif unit in day_units:
        delta = timedelta(days=num)
    elif unit in year_units:
        delta = timedelta(days=365 * num)
    
    return delta
        
def before(date, before, fmt=None):
    '''Compares two dates to see if one is before another'''
    return _convert_datetime(date) < _convert_datetime(before, fmt)
    
def after(date, after, fmt=None):
    '''Compares two dates to see if one is after the other'''
    return _convert_datetime(date) > _convert_datetime(after, fmt)

def to_unix(date, fmt=None):
    '''parse the date using a supplied format or one of the common formats and 
       return its value as a unix timestamp'''
    return mktime(_convert_datetime(date).timetuple())

def _parse_date(date, fmt):
    return datetime.strptime(date, fmt)

def _convert_datetime(date, fmt=None):
    '''Attempts to convert a date by when no format string is supplied. It will 
       try a number of more common formats'''
    
    # already a date?
    date_type = type(date)
    if date_type in [datetime, time]:
        return date   
    elif not (date_type == str or date_type == unicode):
        raise errors.AnsibleFilterError("Date/time filters expect strings " \
                                   "not '%s' like '%s' " % (date_type, date))
    
    # fmt supplied?    
    if fmt:
        try:
            return _parse_date(date, fmt)
        except:
            raise errors.AnsibleFilterError("Could not parse '%s' using format string '%s'" % (date, fmt))
       
    try:
        # unix time?
        return datetime.datetime.fromtimestamp(float(date))
    except:
        pass
    
    # common format ?    
    for known in common_formats:
        try:   
            return _parse_date(date, known)
        except Exception, e:
            pass
    
    err = "No format string was provided and '%s' could not be parsed using one of the standard formats." % date
    raise errors.AnsibleFilterError(err + '''
        - unix time 123456789.012345
        - date and time %d %b %Y %I:%M:%S %p
        - date and time 24hr %d %b %Y %H:%M:%S
        - date %d %b %Y
        - time %I:%M:%S %p
        - time 24hr %H:%M:%S
        - time from directory listing.''') 

def to_date_fuction(fn, num, units):
    ''' creates a date functions for convenience names 'next_week' etc '''
    def date_function(date):
        return fn(date, num, units)
    return date_function
            
class FilterModule(object):
    '''Ansible filters for manipulating dates and times'''

    def filters(self):
        date_filters = {
                'before' : before,
                'after'  : after,
                'to_date' : to_date,
                'as_date' : to_date,
                'to_date_str' : to_date_str,
                'to_unix' : to_unix,
                'previous': _past,
                'in_past': _past,
                'in_future': _future,
            }
            
        timeframes = [('day', 1, 'days'), 
                      ('week', 7, 'days'),
                      ('year', 1, 'years')]

        for (label, num, units) in timeframes:
            date_filters['%s_before' % label] = to_date_fuction( _past, num, units)
            date_filters['%s_ago' % label] = to_date_fuction( _past, num, units)
            date_filters['previous_%s' % label] = to_date_fuction( _past, num, units)
                            
            date_filters['%s_after' % label] = to_date_fuction( _future, num, units)
            date_filters['next_%s' % label] = to_date_fuction( _future, num, units)
            
        return date_filters
