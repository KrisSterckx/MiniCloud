from core_out import debug
from cloud_resource_manager import CloudResourceManager

__author__ = 'Kris Sterckx'


class FlavorManager(CloudResourceManager):
    def __init__(self, minicloud):
        super(FlavorManager, self).__init__(minicloud)
        debug("[{}] initialized.", self)

    @staticmethod
    def entity_name():
        return 'flavor'

    def entity(self, cloud, ctx, cloud_flavor):
        from minicloud.model.flavor import Flavor
        return Flavor(cloud_flavor.name, cloud, cloud_flavor, ctx)

    def get_entities(self, ctx, name=None, deep_list=False):
        return ctx.flavors(name)

    def create_entity(self, ctx, flavor):
        pass

    def delete_entity(self, ctx, flavor):
        return False

    def trust_cache_when_filled(self):
        return True   # Retrieved flavor in cache remain valid

    # override
    @staticmethod
    def sort_list(flavors):
        _list = list()
        _list.extend([f for f in flavors if 'tiny' in f.name])
        _list.extend([f for f in flavors if 'small' in f.name])
        _list.extend([f for f in flavors if 'medium' in f.name])
        _list.extend([f for f in flavors if 'large' in f.name and
                      'xlarge' not in f.name])
        _list.extend([f for f in flavors if 'xlarge' in f.name])
        # add all the rest
        _list += [i for i in flavors if i not in _list]
        return _list
