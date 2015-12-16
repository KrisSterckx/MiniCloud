from abc import ABCMeta, abstractmethod

from minicloud.core.core_utils import _, __

__author__ = 'Kris Sterckx'


class DriverContext:
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def client(self):
        pass

    def authenticate(self):
        if self.client():
            return self.client().authenticate()
        else:
            return True, None

    def authenticated(self):
        if self.client():
            return self.client().authenticated()
        else:
            return True, None

    @abstractmethod
    def new_network(self, cloud, cloud_network):
        pass

    @abstractmethod
    def new_router(self, cloud, cloud_router, net_manager):
        pass

    @abstractmethod
    def new_instance(self, cloud, cloud_instance):
        pass

    def reread_instance(self, instance):
        instance.cloud_instance = self.instances(instance.name)[0]
        self.set_instance_runtime_data(instance)

    @abstractmethod
    def set_instance_runtime_data(self, instance):
        pass

    @abstractmethod
    def flavors(self, name=None):
        pass

    @abstractmethod
    def flavor(self, cloud_flavor=None):
        pass

    @abstractmethod
    def images(self, name=None):
        pass

    @abstractmethod
    def image(self, cloud_image=None):
        pass

    @abstractmethod
    def security_groups(self, name=None):
        pass

    @abstractmethod
    def create_security_group(self, sg):
        pass

    @abstractmethod
    def delete_security_group(self, sg):
        pass

    @abstractmethod
    def create_security_group_rule(self, sg, sg_rule):
        pass

    @abstractmethod
    def get_instance_cluster_name(self, cloud, cloud_instance):
        pass

    @abstractmethod
    def get_instance_device_id(self, instance):
        pass

    @abstractmethod
    def instances(self, name=None):
        pass

    @abstractmethod
    def boot(self, instance):
        pass

    @abstractmethod
    def kill(self, instance):
        pass

    @abstractmethod
    def routers(self, name=None, info=None, override_cache=False):
        pass

    def create_router(self, router):
        _('... Creating router')
        router.cloud_router = self.new_cloud_router(router)
        __()
        return router

    @abstractmethod
    def new_cloud_router(self, router):
        pass

    @abstractmethod
    def uplink_router(self, router, ext_network):
        pass

    @abstractmethod
    def unlink_router(self, router):
        pass

    @abstractmethod
    def delete_router(self, router):
        pass

    @abstractmethod
    def networks(self, name=None):
        pass

    @abstractmethod
    def subnets(self, cloud_network=None):
        pass

    def create_network(self, network):
        _('... Creating network')
        network.cloud_network = self.new_cloud_network(network)
        __()
        return network

    @abstractmethod
    def new_cloud_network(self, network):
        pass

    def create_subnets(self, network):
        _('... Creating subnet')
        network.cloud_subnets = self.new_cloud_subnets(network)
        __()
        return network

    @abstractmethod
    def new_cloud_subnets(self, network):
        pass

    @abstractmethod
    def find_attached_routers(self, network):
        pass

    @abstractmethod
    def attach_to_router(self, subnet, router):
        pass

    @abstractmethod
    def detach_from_router(self, subnet, router):
        pass

    @abstractmethod
    def delete_network(self, network_obj):
        pass

    @abstractmethod
    def ports(self, network=None, device_id=None, compute_only=False,
              non_compute_only=False, override_cache=False):
        pass

    @abstractmethod
    def new_public_ip(self, cloud, cloud_floating_ip):
        pass

    @abstractmethod
    def get_floating_ip(self, instance):
        pass

    @abstractmethod
    def floating_ips(self, instance=None, network=None):
        pass

    @abstractmethod
    def allocate_floating_ip(self, network, port=None):
        pass

    @abstractmethod
    def associate_floating_ip(self, fip, port=None):
        pass

    @abstractmethod
    def deallocate_floating_ip(self, fip):
        pass

    @abstractmethod
    def new_sg(self, cloud_sg, cloud):
        pass


class NetworkIp:
    def __init__(self, net_name, ip):
        self.net_name = net_name
        self.ip = ip
