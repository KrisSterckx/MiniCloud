from cloud_resource_manager import CloudResourceManager
from core_out import debug

__author__ = 'Kris Sterckx'


class ImageManager(CloudResourceManager):
    def __init__(self, minicloud):
        super(ImageManager, self).__init__(minicloud)
        debug("[{}] initialized.", self)

    @staticmethod
    def entity_name():
        return 'image'

    def entity(self, cloud, ctx, cloud_image):
        from minicloud.model.image import Image
        return Image(cloud_image.name, cloud, cloud_image, ctx)

    def get_entities(self, ctx, name=None, deep_list=False):
        return ctx.images(name)

    def create_entity(self, ctx, image):
        pass

    def delete_entity(self, ctx, image):
        return False

    def trust_cache_when_filled(self):
        return True   # Retrieved image in cache remain valid

    # override
    @staticmethod
    def sort_list(images):
        _list = list()
        _list.extend([i for i in images if 'cirros' in i.name.lower()])
        _list.extend([i for i in images if 'centos' in i.name.lower()])
        _list.extend([i for i in images if 'coreos' in i.name.lower()])
        _list.extend([i for i in images if 'fedora' in i.name.lower()])
        _list.extend([i for i in images if 'opensuse' in i.name.lower()])
        _list.extend([i for i in images if 'ubuntu' in i.name.lower()])
        # add all the rest
        _list += [i for i in images if i not in _list]
        return _list
