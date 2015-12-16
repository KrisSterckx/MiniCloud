from minicloud.core.core_out import debug
from minicloud.model.network import Network
from minicloud.model.public_ip import PublicIp
from minicloud.model.router import Router
from minicloud.model.instance import Instance
from minicloud.model.security_group import SecurityGroup

from driver_context import DriverContext

__author__ = 'Kris Sterckx'


class StubNamedEntity(object):
    def __init__(self, name, id=1, description='none'):
        self._id = id
        self._name = name
        self._description = description

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    @property
    def description(self):
        return self._description


class StubNetwork(StubNamedEntity):
    def __init__(self, name, id, cidr, external):
        super(StubNetwork, self).__init__(name, id)
        self._cidr = cidr
        self._external = external

    @property
    def cidrs(self):
        return [self._cidr]

    @property
    def external(self):
        return self._external


class StubInstance(StubNamedEntity):
    def __init__(self, name, id, network, ip, state, cluster):
        super(StubInstance, self).__init__(name, id)
        self._network = network
        self._ip = ip
        self._state = state
        self._cluster = cluster

    @property
    def network(self):
        return self._network

    @property
    def ip(self):
        return self._ip

    @property
    def state(self):
        return self._state

    @property
    def cluster(self):
        return self._cluster


class StubFloatingIp(StubNamedEntity):
    def __init__(self, name, id, network, ip, port, fixed_ip):
        super(StubFloatingIp, self).__init__(name, id)
        self._network = network
        self._ip = ip
        self._port = port
        self._fixed_ip = fixed_ip

    @property
    def network(self):
        return self._network

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    @property
    def fixed_ip(self):
        return self._fixed_ip


class StubDriverContext(DriverContext):

    cloud_instance_count = 0

    def __init__(self):
        super(StubDriverContext, self).__init__()

    def client(self):
        return None

    @staticmethod
    def new_flavor():
        return StubNamedEntity('m1.stubby')

    def flavors(self, name=None):
        flavors = [self.new_flavor()]
        return flavors

    def flavor(self, cloud_flavor=None):
        return None

    class Image:
        def __init__(self, name):
            self._name = name

        @property
        def name(self):
            return self._name

    @staticmethod
    def new_image():
        return StubNamedEntity('Cirry')

    def images(self, name=None):
        images = [self.new_image()]
        return images

    def image(self, cloud_image=None):
        return None

    def new_instance(self, cloud, cloud_instance):
        return Instance(
            cloud_instance.name,
            cloud_instance.cluster,
            cloud_instance.flavor,
            cloud_instance.image,
            cloud_instance.security_groups[0],
            cloud_instance.network,
            None,
            cloud_instance.flavor,
            cloud_instance.image,
            cloud_instance.security_groups[0]
            if cloud_instance.security_groups else None,
            cloud_instance.ip,
            cloud,
            cloud_instance,
            cloud_instance.state,
            self)

    def set_instance_runtime_data(self, instance):
        pass

    def get_instance_cluster_name(self, cloud, cloud_instance):
        return cloud_instance['cluster']

    def get_instance_device_id(self, instance):
        return 1

    def instances(self, name=None):
        return []

    @staticmethod
    def _new_cloud_instance(name, cluster_name, network):
        StubDriverContext.cloud_instance_count += 1

        net_subnet = network.cidrs[0].split('/')[0]
        net_quads = net_subnet.split('.')
        net = net_quads[0] + '.' + net_quads[1] + '.' + net_quads[2] + '.'
        return StubInstance(
            name,
            StubDriverContext.cloud_instance_count,
            network,
            # TODO count globally for now
            net + str(StubDriverContext.cloud_instance_count + 1),
            'ACTIVE',
            cluster_name)

    def boot(self, instance):
        instance.cloud_instance = self._new_cloud_instance(
            instance.name, instance.cluster_name, instance.network)
        instance.ip = instance.cloud_instance.ip
        instance.status = instance.cloud_instance.state

        debug('[StubDriverContext] booted instance {}.',
              instance.cloud_instance)

    def kill(self, instance):
        pass

    def new_network(self, cloud, cloud_network):
        return Network(cloud_network.name, cloud_network.cidrs,
                       False, None, cloud, cloud_network, None, self)

    def new_router(self, cloud, cloud_router, net_manager):
        return Router(cloud_router.name, cloud, cloud_router,
                      driver_context=self)

    def routers(self, name=None, info=None, override_cache=False):
        return []

    def new_cloud_router(self, router):
        return StubNamedEntity(router.name)

    def uplink_router(self, router, ext_network):
        pass

    def unlink_router(self, router):
        pass

    def delete_router(self, router):
        pass

    def networks(self, name=None):
        return []

    def new_cloud_network(self, network):
        return StubNetwork(network.name, 1, network.cidrs[0], network.external)

    def subnets(self, cloud_network=None):
        return []

    def new_cloud_subnets(self, network):
        return []

    def find_attached_routers(self, network):
        return []

    def attach_to_router(self, subnet, router):
        pass

    def detach_from_router(self, subnet, router):
        pass

    def delete_network(self, network_obj):
        pass

    @staticmethod
    def _new_cloud_port():
        return StubNamedEntity('stubbyport')

    def ports(self, network=None, device_id=None, compute_only=False,
              non_compute_only=False, override_cache=False):
        if device_id is not None:
            return [self._new_cloud_port()]
        else:
            # can't do
            raise NotImplementedError

    # FIPs

    def get_floating_ip(self, instance):
        return None

    fip_cnt = 0

    def _new_fip(self):
        self.fip_cnt += 1
        return '169.169.10.' + str(self.fip_cnt + 1)

    # TODO - not yet used
    def new_public_ip(self, cloud, cloud_floating_ip):
        network_id = cloud_floating_ip.network().id
        ip = cloud_floating_ip.ip()
        fixed_ip = cloud_floating_ip.fixed_ip()
        port_id = cloud_floating_ip.port().id
        name = ip  # by lack of name
        return PublicIp(name, network_id, ip, fixed_ip, port_id,
                        cloud, cloud_floating_ip, self)

    def floating_ips(self, instance=None, network=None):
        return []  # TODO assume no floating ips allocated, always

    def allocate_floating_ip(self, network, port=None):
        return self._new_fip()

    def associate_floating_ip(self, fip, port=None):
        pass

    def deallocate_floating_ip(self, fip):
        pass

    # SGs

    def new_sg(self, cloud_sg, cloud=None):
        return SecurityGroup(cloud_sg.name, cloud_sg.description,
                             cloud, cloud_sg, self)

    def security_groups(self, name=None):
        return [self.new_sg(
            StubNamedEntity('default', 1, 'Default SG'))]

    def create_security_group(self, sg):
        return StubNamedEntity(sg.name, 2, sg.description)

    def create_security_group_rule(self, cloud_sg, sg_rule):
        return StubNamedEntity('this cool rule', 1)

    def delete_security_group(self, sg):
        pass
