from jinja2 import Environment, FileSystemLoader
from ansible import errors
from xml.sax.saxutils import escape
 
def xmlescape(a):
    return escape( str(a) )
 
class FilterModule(object):
    ''' xmlescape filter ''' 
    def filters(self):
        return {

            # filter map
            'xmlescape': xmlescape
 
        }

