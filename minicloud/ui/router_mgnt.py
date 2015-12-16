from minicloud.core.core_in import string_input, boolean_input
from minicloud.core.core_out import trace

from entity_mgnt import EntityMgnt

__author__ = 'Kris Sterckx'


class RouterMgnt(EntityMgnt):
    def __init__(self, minicloud_mgnt):
        super(RouterMgnt, self).__init__(minicloud_mgnt.manager.router_manager)
        self.minicloud = minicloud_mgnt.manager
        self.minicloud_mgnt = minicloud_mgnt
        self.network_manager = self.minicloud.network_manager

    def update_supported(self):
        return True

    def obtain_entity_to_add(self):
        from minicloud.model.router import Router

        name = string_input('Name')
        cloud = self.obtain_entity(manager=self.minicloud.cloud_manager)
        if cloud:
            ext_net = None

            if boolean_input(
                    'Do you want to attach this router to an '
                    'external network'):
                ext_net = self.obtain_entity(
                    'Please enter the network name',
                    self.network_manager.external,
                    manager=self.network_manager,
                    skip_questioning_if_only_one_entity=True)

            return Router(name, cloud=cloud, ext_network=ext_net)
        else:
            return None

    def obtain_update_data(self, entity):
        data = None
        if entity.ext_network is None:
            if boolean_input(
                    'Do you want to attach this router '
                    'to an external network'):
                ext_net = self.obtain_entity(
                    'Please enter the network name',
                    self.network_manager.external,
                    manager=self.network_manager,
                    skip_questioning_if_only_one_entity=True)
                if ext_net:
                    data = dict(name=entity.name,
                                ext_network=ext_net)
        elif boolean_input(
                'Do you want to detach this router from its external network'):
            data = dict(name=entity.name, ext_network=None)
        return data

    @staticmethod
    def force_deep_topology():
        return False  # never deep fetch unless cache is empty

    def prebuild_topology(self, level, deep_topology, root_intent, prefix,
                          show_empty_entities):
        # topology for unrouted networks
        trace('[{}] prebuild_topology (deep_topology={}).',
              self, deep_topology)
        return self.topology(level, None, deep_topology, root_intent,
                             prefix, prefix, show_empty_entities)

    def get_network_list(self, router, deep_topology):
        trace('[{}] get_network_list', self)
        return self.minicloud.network_manager.get_networks_by_router(
            router, deep_topology)

    def get_network_mgnt(self):
        return self.minicloud_mgnt.network_mgnt

    def topology(self, level, router, deep_topology,
                 root_indent, root_prefix, prefix,
                 show_empty_entities=False, optimize_list=False):
        return self.build_topology(level, False,
                                   deep_topology, None,
                                   root_indent, root_prefix, prefix,
                                   router, router is None, True,
                                   RouterMgnt.get_network_list,
                                   RouterMgnt.get_network_mgnt,
                                   show_empty_entities,
                                   optimize_list)
