def testfilter(data):
    return "{0}_from_userdir".format(data)


class FilterModule(object):

    def filters(self):
        return {
            'testfilter': testfilter
        }
