class EncodedException(Exception):

    def __init__(self, msg):
        super(EncodedException, self).__init__(msg.encode('utf-8'))
