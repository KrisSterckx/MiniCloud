from entity import ContextualEntity

__author__ = 'Kris Sterckx'


class Network(ContextualEntity):
    def __init__(self, name, cidrs=None, external=False,
                 router=None, cloud=None, cloud_network=None,
                 cloud_subnets=None, driver_context=None):
        super(Network, self).__init__(name, driver_context)
        self.cidrs = (cidrs if cidrs else
                      list(cloud_sub['cidr'] for cloud_sub in cloud_subnets))
        self.external = external
        self.cloud = cloud
        self.router = None
        self.cloud_network = cloud_network
        self.cloud_subnets = cloud_subnets
        self.vm_list = None
        if router:
            self.set_router(router)

    def repr(self):
        cidrs = ', '.join(cidr for cidr in self.cidrs)
        if self.external or self.vm_list is None:
            return 'Network: %s %s%s' % \
                (self.name, '(external) ' if self.external else '',
                 '[' + cidrs + ']' if self.cidrs else '')
        else:
            return 'Network: %s %s%s (%s instance%s)' % \
                (self.name, '(external) ' if self.external else '',
                 '[' + cidrs + ']' if self.cidrs else '',
                 len(self.vm_list), '' if len(self.vm_list) == 1 else 's')

    def routers(self, report_when_not_initialized=False):
        if self.router is None:
            return -1 if report_when_not_initialized else []
        else:
            return self.router.values()

    def set_router(self, router):
        if self.router is None:
            self.router = {}
        if router and router.name not in self.router:
            self.router[router.name] = router
        return self.router

    def unset_router(self, router=None):
        router = router or self.routers()[0]
        if self.router:
            del self.router[router.name]

    def prefix_length(self, subnet_idx=0):
        return int(self.cidrs[subnet_idx].split('/')[1])

    @staticmethod
    def check_cidr(cidr):
        #
        # This is not a full check, but it checks /something/
        #
        if '/' not in cidr:
            return False
        net = cidr.split('/')[0]
        prefix_len = int(cidr.split('/')[1])
        if '.' in net:
            return 1 <= prefix_len <= 32
        elif ':' in net:
            return 1 <= prefix_len <= 64
        else:
            return False
