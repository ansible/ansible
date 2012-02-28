from optparse import OptionParser
import sys
import constants as C

def base_ans_parser(opthosts=True, outputpath=True, forkdef=C.DEFAULT_FORKS):
    parser = OptionParser()
    if opthosts:
        parser.add_option('--host', default=[], action='append',
            help="hosts to act on, defaults to ALL")
    parser.add_option("-H", "--host-list", dest="host_list",
        help="path to hosts list", default=C.DEFAULT_HOST_LIST)
    parser.add_option("-L", "--library", dest="module_path",
        help="path to module library", default=C.DEFAULT_MODULE_PATH)
    parser.add_option('-u', '--user', default=C.DEFAULT_REMOTE_USER, 
        dest='remote_user', help='set the default username')
    parser.add_option("-P", "--askpass", default=False, action="store_true",
         help="ask the user to input the ssh password for connecting")
    parser.add_option('-f','--forks', default=forkdef, type='int',
               help='set the number of forks to start up')
    if outputpath:
        parser.add_option('--outputpath', default='/tmp/ansible', dest="outputpath",
                   help="basepath to store results/errors output.")
    return parser

# other functions as needed for nicely handling output from json back
# to things people might be more inclined to deal with at a bash prompt


def errorprint(msg):
    print >> sys.stderr, msg
    
