from entity import ContextualEntity

__author__ = 'Kris Sterckx'


class PublicIp(ContextualEntity):

    def __init__(self, name, network_id=None,
                 ip=None, fixed_ip=None,
                 port_id=None, cloud=None,
                 cloud_floating_ip=None,
                 driver_context=None):
        super(PublicIp, self).__init__(name, driver_context)
        self.network_id = network_id
        self.ip = ip
        self.fixed_ip = fixed_ip
        self.port_ip = port_id
        self.cloud = cloud
        self.cloud_floating_ip = cloud_floating_ip
