import mimetypes

if __name__ == '__main__':
    mimetypes.init()
    mimetypes.add_type('application/json', '.json')
    import SimpleHTTPServer
    SimpleHTTPServer.test()
