from minicloud.core.core_out import info, warn
from minicloud.driver.os_driver_context import OSDriverContext
from minicloud.driver.stub_driver_context import StubDriverContext

from entity import ContextualStoredEntity

__author__ = 'Kris Sterckx'


class Cloud(ContextualStoredEntity):

    def __init__(self, name=None, type=None, version=None, location=None,
                 path=None, tenant=None, username=None, password=None,
                 user_domain_id=None, project_domain_id=None, _dict=None):

        super(Cloud, self).__init__(dict(name=name,
                                         type=type,
                                         version=version,
                                         location=location,
                                         path=path,
                                         tenant=tenant,
                                         username=username,
                                         password=password,
                                         user_domain_id=user_domain_id,
                                         project_domain_id=project_domain_id)
                                    if not _dict else _dict)
        self.auth = None

    def repr(self):
        return 'Cloud: ' + self.name + ' (' + self.location + ')'

    def deep_repr(self):
        spaces = ' ' * len(self.name)
        return 'Cloud: %s [Type:%s\n' \
               '       %s  Version:%s\n' \
               '       %s  Location:%s\n' \
               '       %s  Path:%s,\n' \
               '       %s  Tenant:%s\n' \
               '       %s  Username:%s\n' \
               '       %s  Password:%s]' % \
               (self.name, self.type,
                   spaces, self.version,
                   spaces, self.location,
                   spaces, self.path,
                   spaces, self.tenant,
                   spaces, self.username,
                   spaces, self.password)

    @property
    def type(self):
        return self.get('type')

    @property
    def version(self):
        return self.get('version')

    @property
    def location(self):
        return self.get('location')

    @property
    def path(self):
        return self.get('path')

    @property
    def tenant(self):
        return self.get('tenant')

    @property
    def username(self):
        return self.get('username')

    @property
    def password(self):
        return self.get('password')

    @property
    def user_domain_id(self):
        return self.get('user_domain_id')

    @property
    def project_domain_id(self):
        return self.get('project_domain_id')

    def context(self):
        if self.auth is None:
            self.authenticate()
        return self.driver_context

    def authenticate(self):
        info('[{}] authenticate()', self)
        if not self.driver_context:
            if self.type.lower() == 'openstack':
                from minicloud.clients.os_client import OSClient
                self.set_context(OSDriverContext(
                    OSClient(self.path, self.username,
                             self.tenant, self.password,
                             self.user_domain_id,
                             self.project_domain_id)))
            else:
                self.set_context(StubDriverContext())

        self.auth, auth_failure = self.driver_context.authenticate()
        if self.auth:
            info('[{}] successfully authenticated.', self)
        elif auth_failure:
            warn('[{}] authentication failed:\n[{}]', self, auth_failure)
        else:
            warn('[{}] authentication failed.', self)

        return self.auth

    def authenticated(self):
        if self.auth:
            return True
        elif self.auth is None:
            return self.authenticate()
        else:
            warn('[{}] is unauthenticated.', self)
            return False

    def is_stubbed(self):
        return 'stub' in self.name


class StubCloud(Cloud):
    def __init__(self):
        super(StubCloud, self).__init__(
            'stub', 'stub', '', '', '', '', '', '')
