from entity import ContextualEntity

__author__ = 'Kris Sterckx'


class Flavor(ContextualEntity):

    def __init__(self, name, cloud=None,
                 cloud_flavor=None, driver_context=None):

        super(Flavor, self).__init__(name, driver_context)
        self.cloud = cloud
        self.cloud_flavor = cloud_flavor
