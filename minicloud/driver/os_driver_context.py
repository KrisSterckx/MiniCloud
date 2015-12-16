import time

from minicloud.model.network import Network
from minicloud.model.public_ip import PublicIp
from minicloud.model.router import Router
from minicloud.model.instance import Instance
from minicloud.model.cluster import Cluster
from minicloud.model.security_group import SecurityGroup

from minicloud.core.core_utils import _, __
from minicloud.core.core_out import error, debug, exc_error, trace
from minicloud.core.core_types import IntegrityException, InstanceNotReadyYet

from driver_context import DriverContext, NetworkIp

__author__ = 'Kris Sterckx'


class OSDriverContext(DriverContext):
    def __init__(self, os_client):
        super(OSDriverContext, self).__init__()
        self.os_client = os_client
        self.routers_cache = {}
        self.ports_cache = {}

    def __repr__(self):
        return 'OS driver ctx'

    def client(self):
        return self.os_client

    @property
    def _keystone(self):
        return self.os_client.keystone()

    @property
    def _nova(self):
        return self.os_client.nova()

    @property
    def _glance(self):
        return self.os_client.glance()

    @property
    def _neutron(self):
        return self.os_client.neutron()

    ###

    def get_ports_by_device_id(self, device_id, override_cache=False):
        if override_cache or device_id not in self.ports_cache:
            _('... Retrieving device ports from device ' + device_id[:6])
            ports = self._neutron.ports(device_id=device_id)
            __()

            self.fill_port_cache(device_id, ports)
            return ports
        else:
            return self.ports_cache[device_id]

    def fill_port_cache(self, device_id, ports):
        self.ports_cache[device_id] = ports

    def clear_port_cache(self, device_id):
        if device_id in self.ports_cache:
            del self.ports_cache[device_id]

    ###

    def flavors(self, name=None):
        _('... Retrieving flavors')
        flavors = self._nova.flavors(name=name)
        __()
        return flavors

    def flavor(self, cloud_flavor=None):
        _('... Retrieving flavor')
        flavor = self._nova.flavors(cloud_flavor['id'])
        __()

        if len(flavor) > 0:
            return flavor[0]
        else:
            error('Flavor {} not found!', cloud_flavor)
            return None

    ###

    def images(self, name=None):
        _('... Retrieving images')
        images = self._glance.images(name=name)
        __()
        return images

    def image(self, cloud_image=None):
        _('... Retrieving image')
        image = self._glance.images(cloud_image['id'])
        __()
        if len(image) > 0:
            return image[0]
        else:
            error('Image {} not found!', cloud_image)
            error('All retrieved images are: {}', self.images())
            return None

    ###

    def new_instance(self, cloud, cloud_instance):
        cluster_name = self.get_instance_cluster_name(cloud, cloud_instance)
        try:
            instance = Instance(
                cloud_instance.name,
                cluster_name,
                None, None, None, None, None,
                cloud_instance.flavor,
                cloud_instance.image,
                cloud_instance.security_groups[0]
                if hasattr(cloud_instance, 'security_groups') and
                cloud_instance.security_groups else None,
                None,  # ip
                cloud,
                cloud_instance,
                None, self)
        except Exception:
            exc_error('Got exception when constructing instance {}',
                      cloud_instance.name)
            raise InstanceNotReadyYet

        self.set_instance_runtime_data(instance)

        debug('new_instance(): instance {} added to cluster {}.',
              cloud_instance.name, cluster_name)
        return instance

    def get_instance_cluster_name(self, cloud, cloud_instance):
        if 'cluster' in cloud_instance.metadata:
            return cloud_instance.metadata['cluster']
        else:
            return Cluster.unnamed_cluster_name(cloud.name)

    def get_instance_device_id(self, instance):
        return instance.cloud_instance.id

    def instances(self, name=None):
        _('... Retrieving instance' + ((' ' + name) if name else 's'))
        instances = self._nova.servers(name=name)
        __()
        return instances

    def boot(self, instance):
        sg_names = [instance.cloud_sg['name']] if instance.cloud_sg else []

        _('... Booting instance')
        instance.cloud_instance = self._nova.boot(
            instance.name,
            instance.cloud_image, instance.cloud_flavor, sg_names,
            instance.cloud_network['id'],
            {'cluster': instance.cluster_name} if instance.cluster_name
            else None)
        __()

        self.set_instance_runtime_data(instance)

    def set_instance_runtime_data(self, instance):
        net_ip = self._get_networks_ip(instance.cloud_instance)
        instance.ip = net_ip[0].ip if net_ip \
            else None  # right after boot, nova doesnt know yet
        instance.network_name = net_ip[0].net_name if net_ip else None  # same
        instance.status = instance.cloud_instance.status

    def kill(self, instance):
        _('... Killing instance')
        self._nova.delete(instance.cloud_instance)
        debug('[{}] {} deleted.', self, str(instance))
        __()

    @staticmethod
    def _get_networks_ip(server):
        _list = []
        network_names = server.addresses.keys()
        if network_names:
            for net in network_names:
                _list.append(NetworkIp(net, server.addresses[net][0]['addr']))
        return _list

    ###

    def new_router(self, cloud, cloud_router, net_manager):
        cloud_net_id = cloud_router['external_gateway_info']['network_id'] \
            if cloud_router['external_gateway_info'] else None
        cloud_net = self._neutron.networks(net_id=cloud_net_id)[0] \
            if cloud_net_id else None
        cloud_net_name = cloud_net['name'] if cloud_net else None
        network = net_manager.get(cloud_net_name) if cloud_net_name else None
        return Router(cloud_router['name'],
                      cloud,
                      cloud_router,
                      network,
                      self)

    def routers(self, name=None, info=None, override_cache=False):
        if self.routers_cache is None or override_cache:
            _('... Retrieving router' +
              ((' ' + name) if name else
               (('s (' + info + ')') if info else 's')))
            self.routers_cache = {}
            for cloud_router in self._neutron.routers():
                self.routers_cache[cloud_router['id']] = cloud_router
            __()
            return self.routers_cache.values()
        elif name:
            return self._neutron.routers(name)
        else:
            return self._neutron.routers()

    def new_cloud_router(self, router):
        cloud_router = self._neutron.create_router(
            router.name, router.ext_network.cloud_network['id']
            if router.ext_network else None)
        self.routers_cache[cloud_router['id']] = cloud_router
        return cloud_router

    def uplink_router(self, router, ext_network):
        _('... Uplinking router')
        self._neutron.uplink_router(router.cloud_router['id'],
                                    ext_network.cloud_network['id'])
        self.routers_cache[router.cloud_router['id']] = router.cloud_router
        __()

    def unlink_router(self, router):
        _('... Unlinking router')
        self._neutron.unlink_router(router.cloud_router['id'])
        self.routers_cache[router.cloud_router['id']] = router.cloud_router
        __()

    def delete_router(self, router):
        if self.routers_cache:
            del self.routers_cache[router.cloud_router['id']]
        self._neutron.delete_router(router.cloud_router['id'])
        debug('[{}] {} deleted.', self, str(router))

    ###

    def new_network(self, cloud, cloud_network):
        cloud_subnets = self.subnets(cloud_network)
        external = cloud_network['router:external']
        router = None  # leave lazy
        return Network(cloud_network['name'],
                       external=external, router=router,
                       cloud=cloud, cloud_network=cloud_network,
                       cloud_subnets=cloud_subnets, driver_context=self)

    def networks(self, name=None):
        _('... Retrieving network' + ((' ' + name) if name else 's'))
        networks = self._neutron.networks(name)
        __()
        return networks

    def subnets(self, cloud_network=None):
        _('... Retrieving subnet' +
          ((' for network ' + cloud_network['name']) if cloud_network
           else 's'))
        subnets = self._neutron.subnets(cloud_network['id'])
        __()
        return subnets

    def new_cloud_network(self, network):
        return self._neutron.create_network(network.name, network.external)

    def new_cloud_subnets(self, network):
        for cidr in network.cidrs:
            return self._neutron.create_subnet(network.cloud_network['id'],
                                               cidr)

    def find_attached_routers(self, network):
        routers = list()
        for r in self.routers(info='for network ' + network['name']):
            is_external = network['router:external']
            if is_external:
                if (r['external_gateway_info'] and
                        r['external_gateway_info']['network_id'] ==
                        network['id']):
                    routers.append(r)
            elif self.ports(network=network, device_id=r['id']):
                routers.append(r)
        return routers

    def attach_to_router(self, subnet, router):
        if router is None:
            error('attach_to_router: there is no router')
            raise IntegrityException

        if subnet is None:
            error('attach_to_router: there is no subnet')
            raise IntegrityException

        _('... Attaching to router')
        self._neutron.add_router_interface(router['id'], subnet['id'])

        self.clear_port_cache(router['id'])
        __()

    def detach_from_router(self, subnet, router):
        trace('[{}] detach_from_router [{}] [{}]', self, subnet, router)
        if router is None:
            error('detach_to_router: there is no router')
            raise IntegrityException

        if subnet is None:
            error('detach_to_router: there is no subnet')
            raise IntegrityException

        _('... Detaching from router')
        self._neutron.remove_router_interface(router['id'], subnet['id'])
        debug('[{}] {} detached from {}.', self, str(subnet), str(router))

        self.clear_port_cache(router['id'])
        __()

    def delete_network(self, network_obj):
        trace('[{}] delete_network [{}]', self, network_obj.name)
        # first delete all ports
        self.delete_ports(network_obj.cloud_network, standalone_only=True)
        # then detach
        routers = network_obj.routers(True)
        if routers == -1:
            routers = self.find_attached_routers(network_obj.cloud_network)
            cloud_routers = True
        else:
            cloud_routers = False
        trace('[{}] delete_network: {} routers found', self, len(routers))
        for router in routers:
            for subnet in network_obj.cloud_subnets:
                # TODO(Kris) need to find which subnet bound to which router
                self.detach_from_router(subnet,
                                        router if cloud_routers else
                                        router.cloud_router)
        # then delete the network
        self._neutron.delete_network(network_obj.cloud_network['id'])
        debug('[{}] {} deleted.', self, str(network_obj))

    ###

    def ports(self, network=None, device_id=None, compute_only=False,
              standalone_only=False, no_dhcp=False,
              override_cache=False):
        trace('[{}] ports() [network={}] [device_id={}] {}', self,
              network['name'] if network else 'none',
              device_id[:6] if device_id else 'none',
              '[compute_only]' if compute_only else
              '[standalone_only]' if standalone_only else '')
        _('... Retrieving ports')

        external = network['router:external'] if network else False
        if compute_only and external:
            return list()

        if device_id:
            ports = self.get_ports_by_device_id(device_id, override_cache)

            if network:
                ports = self.filter_ports_by_network(ports, network['id'])

            if compute_only:
                ports = self.filter_ports_by_compute_only(ports)

        elif network:
            ports = self._neutron.ports(network['id'],
                                        standalone_only=standalone_only)
            if compute_only:
                ports = self.filter_ports_by_compute_only(ports)

            if no_dhcp:
                ports = self.filter_ports_by_no_dhcp(ports)

        elif standalone_only:
            ports = self._neutron.ports(standalone_only=True)

        else:
            raise NotImplementedError

        __()

        trace('[{}] ports() returning {} ports.', self, len(ports))
        return ports

    def delete_ports(self, network,
                     compute_only=False,
                     standalone_only=False):
        trace('[{}] delete_ports [{}]', self, network['name'])
        for port in self.ports(network,
                               compute_only=compute_only,
                               standalone_only=standalone_only,
                               no_dhcp=True):
            self._neutron.delete_port(port['id'])
            debug('[{}] Port [{}] deleted', self, port['id'])

    @staticmethod
    def filter_ports_by_network(ports, network_id):
        port_list = []
        for port in ports:
            if port['network_id'] == network_id:
                port_list.append(port)
        return port_list

    @staticmethod
    def filter_ports_by_compute_only(ports):
        compute_ports = []
        for port in ports:
            if 'compute' in str(port['device_owner']):
                compute_ports.append(port)
        return compute_ports

    @staticmethod
    def filter_ports_by_no_dhcp(ports):
        filtered_ports = []
        for port in ports:
            if 'dhcp' not in str(port['device_owner']):
                filtered_ports.append(port)
        return filtered_ports

    ###

    def new_public_ip(self, cloud, cloud_floating_ip):
        network_id = cloud_floating_ip['floating_network_id']
        ip = cloud_floating_ip['floating_ip_address']
        fixed_ip = cloud_floating_ip['fixed_ip_address']
        port_id = cloud_floating_ip['port_id']
        name = ip  # by lack of name
        return PublicIp(name, network_id, ip, fixed_ip, port_id,
                        cloud, cloud_floating_ip, self)

    def get_floating_ip(self, instance):
        fip = self.floating_ips(instance)
        if fip:
            return fip[0]['floating_ip_address']
        else:
            return None

    def floating_ips(self, instance=None, network=None):
        if instance:
            override_cache = False
            while True:
                ports = self.ports(device_id=instance.id,
                                   override_cache=override_cache)
                if ports:
                    break
                else:
                    debug('{} has no ports, refreshing in sec.', instance.name)

                    override_cache = True
                    time.sleep(1)

            _('... Retrieving public ips')
            fips = self._neutron.floating_ips(
                # TODO - fix, take first port for now
                ports[0]['fixed_ips'][0]['ip_address'])
            __()
            if fips:
                debug('[{}] instance {} has public ip {}.', self,
                      instance.name, fips[0])
            else:
                debug('[{}] instance {} has no public ip.', self,
                      instance.name)
        else:
            # TODO same for network

            _('... Retrieving public ips')
            fips = self._neutron.floating_ips()
            __()

        return fips

    def allocate_floating_ip(self, network, port=None):
        _('... Allocating public ip')
        fip = self._neutron.allocate_floating_ip(
            network['id'], port['id'])['floating_ip_address']
        __()
        return fip

    def associate_floating_ip(self, fip, port=None):
        _('... Associating public ip')
        self._neutron.associate_floating_ip(fip, port['id'])
        __()

    def deallocate_floating_ip(self, fip):
        _('... Deallocating public ip')
        self._neutron.deallocate_floating_ip(fip)
        __()
        debug('[{}] {} deallocated.', self, str(fip))

    ###

    def new_sg(self, cloud_sg, cloud):
        return SecurityGroup(cloud_sg['name'], cloud_sg['description'],
                             cloud, cloud_sg, self)

    def security_groups(self, name=None):
        _('... Retrieving neutron sg\'s')
        sgs = self._neutron.security_groups(name=name)
        __()
        return sgs

    def create_security_group(self, sg):
        _('... Creating neutron sg')
        sg = self._neutron.create_sg(sg.name, sg.description)
        __()
        return sg

    def delete_security_group(self, sg):
        _('... Deleting neutron sg')
        sg = self._neutron.delete_sg(sg.cloud_sg['id'])
        __()
        debug('[{}] {} deleted.', self, str(sg))
        return sg

    def create_security_group_rule(self, cloud_sg, sg_rule):
        _('... Creating neutron sg rule')
        sgr = self._neutron.create_sg_rule(
            cloud_sg['id'],
            sg_rule.ip_protocol, sg_rule.port_min, sg_rule.port_max,
            sg_rule.direction, sg_rule.cidr)
        __()
        return sgr
