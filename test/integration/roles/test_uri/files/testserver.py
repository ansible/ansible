import mimetypes
import SimpleHTTPServer

if __name__ == '__main__':
    mimetypes.add_type('application/json', '.json')
    SimpleHTTPServer.test()
