from entity import ContextualEntity

__author__ = 'Kris Sterckx'


class Image(ContextualEntity):

    def __init__(self, name, cloud=None,
                 cloud_image=None, driver_context=None):
        super(Image, self).__init__(name, driver_context)
        self.cloud = cloud
        self.cloud_image = cloud_image
