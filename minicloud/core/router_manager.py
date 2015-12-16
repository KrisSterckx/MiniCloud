from cloud_resource_manager import CloudResourceManager
from core_out import debug

__author__ = 'Kris Sterckx'


class RouterManager(CloudResourceManager):
    def __init__(self, minicloud):
        super(RouterManager, self).__init__(minicloud)
        debug("[{}] initialized.", self)

    @staticmethod
    def entity_name():
        return 'router'

    def entity(self, cloud, ctx, cloud_router):
        return ctx.new_router(cloud, cloud_router,
                              self.minicloud.network_manager)

    def get_entities(self, ctx, name=None, deep_list=False):
        debug('[{}] get_entities (deep_list={}).', self, deep_list)
        return ctx.routers(name, override_cache=deep_list)

    def create_entity(self, ctx, router):
        ctx.create_router(router)
        return router

    def reconfig_entity(self, ctx, router, data):
        external_network = data['ext_network']
        if external_network is not None:
            self.uplink_router(router, external_network, ctx)
        else:
            self.unlink_router(router, ctx)

    @staticmethod
    def uplink_router(router, ext_network, ctx):
        router.ext_network = ext_network
        ctx.uplink_router(router, ext_network)

    @staticmethod
    def unlink_router(router, ctx):
        router.ext_network = None
        ctx.unlink_router(router)

    def delete_entity(self, ctx, router):
        if router.ext_network:
            router.ext_network.unset_router(router)
        ctx.delete_router(router)
        return True

    ###

    def uplink(self, router, ext_network):
        self.update(router, dict(name=router.name,
                                 ext_network=ext_network))
        # this will eventually invoke reconfig_entity

    def unlink(self, router):
        self.update(router, dict(name=router.name, ext_network=None))
        # this will eventually invoke reconfig_entity
