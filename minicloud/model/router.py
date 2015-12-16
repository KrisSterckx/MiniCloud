from entity import ContextualEntity

__author__ = 'Kris Sterckx'


class Router(ContextualEntity):

    def __init__(self, name, cloud=None, cloud_router=None,
                 ext_network=None, driver_context=None):
        super(Router, self).__init__(name, driver_context)
        self.cloud = cloud
        self.cloud_router = cloud_router
        self.ext_network = ext_network

    def repr(self):
        return 'Router: %s' % self.name
