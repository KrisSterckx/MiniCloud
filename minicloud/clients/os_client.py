import time

from minicloud.core.core_in import boolean_error, shell_variable
from minicloud.core.core_out import end, error, error_n, \
    exc_error, output, trace, warn, warn_n
from minicloud.core.core_types import AuthorizationException, \
    HttpAccessException, InUseException, IntegrityException, \
    MiniCloudException
from minicloud.core.core_utils import _, __

import requests

__author__ = 'Kris Sterckx'

CLOSE = True
SLOW_SYSTEM = shell_variable('WINDIR')  # slow on windows

# suppress warning
requests.packages.urllib3.disable_warnings()

try:
    if SLOW_SYSTEM:
        _('Loading...', thru_silent_mode=True)

    from glanceclient.v2 import client as glance_client
    from keystoneclient.v2_0 import client as keystone_v2_client
    from keystoneclient.v3 import client as keystone_client
    from keystoneauth1.identity import v3 as keystone_v3
    from keystoneauth1 import session as keystone_session
    from keystoneauth1.exceptions.auth import AuthorizationFailure \
        as KeyStoneAuthorizationFailure
    from keystoneauth1.exceptions.catalog import EmptyCatalog
    from keystoneauth1.exceptions.connection import ConnectFailure \
        as KeyStoneConnectionFailure
    from keystoneauth1.exceptions.http import NotFound \
        as KeyStoneHttpNotFound
    from osc_lib.exceptions import \
        Forbidden, AuthorizationFailure, Unauthorized
    from neutronclient.v2_0 import client as neutron_client_v2
    from neutronclient.neutron import client as neutron_client
    from neutronclient.common.exceptions import NetworkInUseClient, \
        BadRequest, NotFound, InternalServerError, \
        IpAddressGenerationFailureClient, \
        Conflict, OverQuotaClient
    from neutronclient.common.exceptions import Forbidden as NeutronForbidden
    from novaclient import client as nova_client
    from novaclient.exceptions import OverLimit
    from novaclient.exceptions import Forbidden as NovaForbidden
    from novaclient.exceptions import ClientException as NovaClientException
    from novaclient.exceptions import BadRequest as NovaBadRequest

    if SLOW_SYSTEM:
        __(thru_silent_mode=True)

except ImportError as e:
    __(thru_silent_mode=True)

    error('{}: Can\'t import python clients for OpenStack.', e.message)
    error('Please install them '
          '(e.g. using \'sudo pip install python-openstackclient\')\n')

    error('Meanwhile, MiniCloud can continue with stubbed clients.')
    if boolean_error(
            'Do you want to continue experimenting with this software',
            default=False):
        output()

        class glance_client(object):
            pass

        class keystone_client(object):
            pass

        class keystone_v2_client(object):
            pass

        class neutron_client(object):
            pass

        class nova_client(object):
            pass

        class Forbidden(object):
            pass

        class KeyStoneAuthorizationFailure(object):
            pass

        class KeyStoneHttpNotFound(object):
            pass

        class EmptyCatalog(object):
            pass

        class AuthorizationFailure(object):
            pass

        class Unauthorized(object):
            pass

        class NetworkInUseClient(object):
            pass

        class BadRequest(object):
            pass

        class NotFound(object):
            pass

        class IpAddressGenerationFailureClient(object):
            pass

        class Conflict(object):
            pass

        class OverQuotaClient(object):
            pass

        class NeutronForbidden(object):
            pass

        class OverLimit(object):
            pass

        class NovaForbidden(object):
            pass

        class NovaClientException(object):
            pass

        class NovaBadRequest(object):
            pass
    else:
        end(1)


class OSCredentials(object):
    def __init__(self, auth_url, username, project_name, password,
                 user_domain_id, project_domain_id):
        self.auth_url = auth_url
        self.username = username
        self.project_name = project_name  # or tenant_name, in v2
        self.password = password
        self.user_domain_id = user_domain_id
        self.project_domain_id = project_domain_id


class Keystone(object):

    def __init__(self, session=None, credentials=None):
        try:
            self.authentication_success = False
            self.authentication_failure = None
            if session:
                self.client = keystone_client.Client(session=session)
            else:
                self.credentials = credentials
                self.client = keystone_v2_client.Client(
                    username=credentials.username,
                    password=credentials.password,
                    tenant_name=credentials.project_name,
                    auth_url=credentials.auth_url)

            self.authentication_success = True
        except (AuthorizationFailure, KeyStoneAuthorizationFailure,
                Unauthorized) as e:
            self.authentication_failure = e

    def __repr__(self):
        return 'OS Client'

    @property
    def roles(self):
        try:
            return self.client.roles.list()
        except Forbidden:
            return None

    @property
    def services(self):
        try:
            return self.client.services.list()
        except Forbidden:
            return None

    @property
    def tenants(self):
        try:
            return self.client.tenants.list()
        except Forbidden:
            return None

    @property
    def users(self):
        try:
            return self.client.users.list()
        except Forbidden:
            pass
        return None

    @property
    def endpoints(self):
        try:
            return self.client.endpoints.list()
        except Forbidden:
            return None

    @property
    def extensions(self):
        try:
            return self.client.extensions.list()
        except Forbidden:
            return None

    @property
    def user_id(self):
        return self.client.user_id

    @property
    def tenant_id(self):
        return self.client.project_id

    @property
    def auth_token(self):
        return self.client.auth_token

    @property
    def service_catalog(self):
        return self.client.service_catalog

    @property
    def image_url(self):
        return self.service_catalog.url_for(service_type='image',
                                            endpoint_type='publicURL')

    @property
    def network_url(self):
        return self.service_catalog.url_for(service_type='network',
                                            endpoint_type='publicURL')

    @property
    def compute_url(self):
        return self.service_catalog.url_for(service_type='compute',
                                            endpoint_type='publicURL')

    def get_token(self):
        return self.client.get_raw_token_from_identity_service(
            auth_url=self.credentials.auth_url,
            username=self.credentials.username,
            password=self.credentials.password,
            tenant_name=self.credentials.project_name)['token']


class Glance(object):
    def __init__(self, session=None, endpoint=None, token=None):
        if session:
            self.client = glance_client.Client('2.0', session=session)
        else:
            self.client = glance_client.Client(endpoint=endpoint, token=token)

    def __repr__(self):
        return 'OS Client'

    def images(self, img_id=None, name=None):
        if img_id:
            return self.client.images.findall(id=img_id)
        elif name:
            return self.client.images.findall(name=name)
        else:
            return self.client.images.list()


class Neutron(object):
    def __init__(self, session=None, credentials=None):
        if session:
            self.client = neutron_client.Client('2.0', session=session)
        else:
            self.client = neutron_client_v2.Client(
                username=credentials.username,
                password=credentials.password,
                tenant_name=credentials.project_name,
                auth_url=credentials.auth_url)
        self.client.format = 'json'

    def __repr__(self):
        return 'OS Client'

    @staticmethod
    def delete_resource(f, *args):
        try:
            f(*args)
        except Conflict as e:
            error_n('Conflicting request: {}', e)
            raise IntegrityException
        except NotFound as e:
            warn_n('Resource not found when deleting it: {}', e)
            # but, silently pass for now...
        except InternalServerError as e:
            warn_n('InternalServerError when deleting resource: {}', e)
            # but, silently pass for now...

    @staticmethod
    def router_names(routers):
        router_names = list()
        for router in routers:
            router_names.append(router['name'])
        return router_names

    def routers(self, name=None, router_id=None):
        try:
            if router_id:
                return self.client.list_routers(id=router_id)['routers']
            elif name:
                return self.client.list_routers(name=name)['routers']
            else:
                return self.client.list_routers()['routers']
        except KeyStoneHttpNotFound as e:
            exc_error('[{}] Router api failure: {}', self, e)
            raise HttpAccessException

    def networks(self, name=None, net_id=None):
        try:
            if net_id:
                return self.client.list_networks(id=net_id)['networks']
            elif name:
                return self.client.list_networks(name=name)['networks']
            else:
                return self.client.list_networks()['networks']
        except KeyStoneHttpNotFound as e:
            exc_error('[{}] Network api failure: {}', self, e)
            raise HttpAccessException

    def subnets(self, network_id=None):
        try:
            if network_id:
                return self.client.list_subnets(
                    network_id=network_id)['subnets']
            else:
                return self.client.list_subnets()['subnets']
        except KeyStoneHttpNotFound as e:
            exc_error('[{}] Subnet api failure: {}', self, e)
            raise HttpAccessException

    def ports(self, network_id=None, device_id=None, standalone_only=False):
        trace('[{}] ports [{}] [{}] [{}]', self,
              network_id if network_id else ' ',
              device_id if device_id else ' ',
              standalone_only if standalone_only else ' ')
        if device_id and network_id:
            return self.client.list_ports(
                device_id=device_id, network_id=network_id)['ports']
        elif device_id:
            return self.client.list_ports(device_id=device_id)['ports']
        elif network_id:
            ports = self.client.list_ports(network_id=network_id)['ports']
        else:
            ports = self.client.list_ports()['ports']
        if standalone_only:  # TODO(Kris) Optimize
            trace('[{}] {} ports found, filtering to standalone',
                  self, len(ports))
            sa_ports = []
            for port in ports:
                trace('[{}] processing port [{}]', self, port)
                if (not port['device_owner'] or
                        # i think below criterium are lost ports whose vm was
                        # destroyed
                        # ------------------- cover compute:nova and :ironic
                        (port['device_owner'].startswith('compute') or
                         port['device_owner'] == 'nuage:vip') and
                        not port['binding:profile'] or
                        # TODO(Kris) i have no clue what this ...
                        port['device_owner'] == 'compute:None'):
                    sa_ports.append(port)
            trace('[{}] {} standalone ports', self, len(sa_ports))
            return sa_ports
        else:
            trace('[{}] {} ports found, standalone was not set',
                  self, len(ports))
            return ports

    def create_router(self, name, external_network_id=None):
        if external_network_id:
            router = {'name': name, 'admin_state_up': True,
                      'external_gateway_info':
                          {'network_id': external_network_id}}
        else:
            router = {'name': name, 'admin_state_up': True}
        try:
            return self.client.create_router({'router': router})['router']
        except OverQuotaClient as e:
            exc_error('[{}] Router creation failure: {}', self, e)
            raise IntegrityException

    def uplink_router(self, router_id, external_network_id):
        router_update_body = {'router':
                              {'external_gateway_info':
                               {'network_id': external_network_id}}}
        return self.client.update_router(router_id, router_update_body)

    def unlink_router(self, router_id):
        router_update_body = {'router': {'external_gateway_info': {}}}
        try:
            return self.client.update_router(router_id, router_update_body)
        except Conflict as c:
            error_n('[{}] Unlink router conflict: {}', self, c)
            raise IntegrityException

    def delete_router(self, router_id):
        self.delete_resource(self.client.delete_router, router_id)

    def create_network(self, name, external=False):
        network = {'name': name, 'admin_state_up': True,
                   'router:external': external}
        try:
            return self.client.create_network({'network': network})['network']
        except NeutronForbidden as f:
            exc_error('[{}] Forbidden to create network: {}', self, f)
            raise IntegrityException

    def delete_network(self, net_id):
        try:
            self.delete_resource(self.client.delete_network, net_id)
        except NetworkInUseClient as e:
            exc_error('[{}] Network is in use: {}', self, e)
            raise InUseException

    def create_subnet(self, net_id, cidr):
        subnet = {'name': cidr, 'network_id': net_id, 'cidr': cidr,
                  'ip_version': '4', 'enable_dhcp': True}
        try:
            return self.client.create_subnet({'subnet': subnet})['subnet']
        except BadRequest as e:
            exc_error('[{}] Bad subnet create request: {}', self, e)
            raise IntegrityException

    def delete_subnet(self, subnet_id):
        self.delete_resource(self.client.delete_subnet, subnet_id)

    def delete_port(self, port_id):
        self.delete_resource(self.client.delete_port, port_id)

    def add_router_interface(self, router_id, subnet_id):
        add_itf = {'subnet_id': subnet_id}
        try:
            self.client.add_interface_router(router_id, add_itf)
        except BadRequest as e:
            exc_error('[{}] Bad router interface request: {}', self, e)
            raise IntegrityException

    def remove_router_interface(self, router_id, subnet_id):
        add_itf = {'subnet_id': subnet_id}
        self.delete_resource(self.client.remove_interface_router,
            router_id, add_itf)

    def security_groups(self, name=None):
        if name:
            return self.client.list_security_groups(name=name)[
                'security_groups']
        else:
            return self.client.list_security_groups()['security_groups']

    def create_sg(self, name, description):
        sg = {'name': name, 'description': description}
        return self.client.create_security_group(
            {'security_group': sg})['security_group']

    def delete_sg(self, sg_id):
        self.delete_resource(self.client.delete_security_group, sg_id)

    def create_sg_rule(self, sg_id, protocol,
                       port_min, port_max, direction, cidr):
        sg_rule = {'security_group_id': sg_id,
                   'protocol': protocol,
                   'port_range_min': port_min,
                   'port_range_max': port_max,
                   'direction': direction,
                   'remote_ip_prefix': cidr}
        return self.client.create_security_group_rule(
            {'security_group_rule': sg_rule})['security_group_rule']

    def floating_ips(self, fixed_ip=None, fip_id=None):
        if fip_id:
            floating_ips = self.client.list_floatingips(
                id=fip_id)['floatingips']
        elif fixed_ip:
            floating_ips = self.client.list_floatingips(
                fixed_ip_address=fixed_ip)['floatingips']
        else:
            floating_ips = self.client.list_floatingips()['floatingips']
        return floating_ips

    def allocate_floating_ip(self, network_id, port_id=None):
        try:
            if port_id:
                create_fip = {'floating_network_id': network_id,
                              'port_id': port_id}
            else:
                create_fip = {'floating_network_id': network_id}
            return self.client.create_floatingip(
                {'floatingip': create_fip})['floatingip']

        except (NotFound, BadRequest, IpAddressGenerationFailureClient,
                OverQuotaClient) as e:
            exc_error('[{}] Floating IP allocation failure: {}', self, e)
            raise IntegrityException

    def associate_floating_ip(self, fip, port_id):
        try:
            update_fip = {'port_id': port_id}
            return self.client.update_floatingip(fip['id'],
                                                 {'floatingip': update_fip})

        except (NotFound, BadRequest, IpAddressGenerationFailureClient) as e:
            error_n('[{}] Floating IP association failure: {}', self, e)
            raise IntegrityException

    def deallocate_floating_ip(self, fip):
        self.delete_resource(self.client.delete_floatingip, fip['id'])


class Nova(object):
    def __init__(self, session=None, credentials=None):
        if session:
            self.client = nova_client.Client(
                2, session=session)
        else:
            self.client = nova_client.Client(
                username=credentials.username,
                password=credentials.password,
                project_name=credentials.project_name,
                auth_url=credentials.auth_url,
                version='2.1')

    def __repr__(self):
        return 'OS Client'

    def flavors(self, name=None):
        if name is None:
            return self.client.flavors.list()
        else:
            return self.client.flavors.findall(name=name)

    def servers(self, server_id=None, name=None):
        try:
            if server_id:
                return self.client.servers.findall(id=server_id)
            elif name:
                return self.client.servers.findall(name=name)
            else:
                return self.client.servers.list()
        except EmptyCatalog as e:
            exc_error('[{}] Nova catalog exception: {}.', self, e)
            raise AuthorizationException
        except KeyStoneHttpNotFound as e:
            exc_error('[{}] Nova api failure: {}', self, e)
            raise HttpAccessException

    def server(self, server_id):
        return self.client.servers.get(server_id)

    def quotas(self):
        return self.client.quotas

    def keypairs(self, name=None):
        if name is None:
            return self.client.keypairs.list()
        else:
            return self.client.keypairs.findall(name=name)

    def keypair(self, name, public_key):
        return self.client.keypairs.create(name, public_key)

    def boot(self, name, image, flavor, sg_names=None, network_id=None,
             meta=None, poll_for_completion=False):
        nics = [{'net-id': network_id}] if network_id else None

        try:
            trace('Booting server: [name: {}] [image: {}] '
                  '[flavor: {}] [sg: {}] [nics: {}]',
                  name, image, flavor,
                  sg_names[0] if sg_names else '-', nics)
            instance = self.client.servers.create(
                name, image, flavor, security_groups=sg_names,
                nics=nics, meta=meta)
        except NovaForbidden as f:
            exc_error('[{}] Nova boot forbidden: {}.', self, f)
            raise MiniCloudException
        except NovaClientException as nce:
            exc_error('[{}] Nova boot exception: {}.', self, nce)
            raise MiniCloudException

        if poll_for_completion:
            while instance.status == 'BUILD':
                time.sleep(5)
                instance = self.server(instance.id)

        return instance

    def delete(self, server):
        self.client.servers.delete(server)


class OSClient(object):
    def __init__(self, auth_url, username, project_name, password,
                 user_domain_id, project_domain_id):

        # fix auth_url if it does not hold v3 - TODO(KRIS) any other way?
        if auth_url[-2:] != 'v3' and auth_url[-2:] != 'v2':
            auth_url += '/v3'
        # end of hack

        self._me = OSCredentials(auth_url, username, project_name, password,
                                 user_domain_id, project_domain_id)
        self._keystone = None
        self._v2 = None
        self._glance = None
        self._nova = None
        self._neutron = None
        self._authenticated = None
        self.session = None

        self.authenticate()

    def __repr__(self):
        return 'OS Client'

    def authenticated(self):
        return self._authenticated

    def authenticate(self):
        if self._authenticated is None:
            auth = keystone_v3.Password(
                auth_url=self._me.auth_url,
                username=self._me.username,
                password=self._me.password,
                project_name=self._me.project_name,
                user_domain_id=self._me.user_domain_id,
                project_domain_id=self._me.project_domain_id)

            # session.Session(auth=auth, verify='/path/to/ca.cert')
            self.session = keystone_session.Session(auth=auth, verify=False)
            self._authenticated = self.keystone().authentication_success
            try:
                # verify the authentication
                self._authenticated &= self.keystone().endpoints is not None
                assert self._authenticated
                _('OK', CLOSE)

            except KeyStoneHttpNotFound:
                _('... Reverting to v2', CLOSE)

                self._authenticated = self.keystone(v2=True).\
                    authentication_success
                _('... v2 Authentication OK', CLOSE)

                # verify the authentication
                # TODO(Kris) not sure why endpoint check does not work here
                self._authenticated &= \
                    self.keystone().get_token() is not None
                assert self._authenticated
                _('... v2 Token check OK', CLOSE)

            except KeyStoneConnectionFailure as e:
                output()
                warn('[{}] Could not connect to Keystone service: {}', self,
                     str(e))
                self._authenticated = False

        return self._authenticated, self.keystone().authentication_failure

    def keystone(self, v2=False):
        if not self._keystone or v2 and not self._v2:
            _('... Initializing Keystone client (' + ('v2)' if v2 else 'v3)'))
            if v2:
                self._keystone = Keystone(credentials=self._me)
            else:
                self._keystone = Keystone(self.session)
            self._v2 = v2
            __()
        return self._keystone

    def glance(self):
        if not self._glance:
            _('... Initializing Glance client ')
            if self._v2:
                self._glance = Glance(endpoint=self._keystone.image_url,
                                      token=self._keystone.auth_token)
            else:
                self._glance = Glance(self.session)
            __()
        return self._glance

    def nova(self):
        if not self._nova:
            _('... Initializing Nova client ')
            if self._v2:
                self._nova = Nova(credentials=self._me)
            else:
                self._nova = Nova(self.session)
            __()
        return self._nova

    def neutron(self):
        if not self._neutron:
            _('... Initializing Neutron client ')
            if self._v2:
                self._neutron = Neutron(credentials=self._me)
            else:
                self._neutron = Neutron(self.session)
            __()
        return self._neutron
