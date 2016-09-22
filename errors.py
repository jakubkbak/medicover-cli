from __future__ import unicode_literals


class MedicoverException(Exception):

    def __init__(self, msg):
        super(MedicoverException, self).__init__(msg)


class AuthenticationError(Exception):
    msg = 'Incorrect username or password'

    def __init__(self):
        super(AuthenticationError, self).__init__(self.msg)


class MissingCredentialsError(Exception):
    msg = 'Missing username or password'

    def __init__(self):
        super(MissingCredentialsError, self).__init__(self.msg)
