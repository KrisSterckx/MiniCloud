__author__ = 'Kris Sterckx'


class SecurityGroupRule:

    def __init__(self, ip_protocol=None, port_min=None, port_max=None,
                 direction=None, cidr=None, cloud_sg_rule=None, sg=None):
        self.ip_protocol = ip_protocol
        self.port_min = port_min
        self.port_max = port_max
        self.direction = direction
        self.cidr = cidr
        self.cloud_sg_rule = cloud_sg_rule
        self.sg = sg
