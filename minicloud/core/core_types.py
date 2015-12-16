__author__ = 'Kris Sterckx'


class MiniCloudException(Exception):
    pass


class AuthorizationException(MiniCloudException):
    pass


class HttpAccessException(MiniCloudException):
    pass


class DatabaseException(MiniCloudException):
    pass


class DatabaseFatalException(DatabaseException):
    pass


class IntegrityException(MiniCloudException):
    pass


class DoesNotExistException(MiniCloudException):
    pass


class InUseException(MiniCloudException):
    pass


class NotSupportedYetException(MiniCloudException):
    pass


class InstanceNotReadyYet(MiniCloudException):
    pass


class DatabaseCredentials:
    MINI_CLOUD_DATABASE = 'minicloud'

    def __init__(self, host, username, password, database=None):
        self.host = host
        self.username = username
        self.password = password
        self.database = database if not None else self.MINI_CLOUD_DATABASE


class UserCredentials:
    def __init__(self, username, tenant, password):
        self.username = username
        self.tenant = tenant
        self.password = password
