from cloud_resource_manager import CloudResourceManager
from core_out import debug, warn

__author__ = 'Kris Sterckx'


class NetworkManager(CloudResourceManager):
    def __init__(self, minicloud):
        super(NetworkManager, self).__init__(minicloud)
        self.router_manager = self.minicloud.router_manager
        debug("[{}] initialized.", self)

    @staticmethod
    def entity_name():
        return 'network'

    def entity(self, cloud, ctx, cloud_network):
        return ctx.new_network(cloud, cloud_network)

    def get_entities(self, ctx, name=None, deep_list=False):
        return ctx.networks(name)

    def create_entity(self, ctx, network):
        ctx.create_network(network)
        ctx.create_subnets(network)
        for router in network.routers():
            for subnet in network.cloud_subnets:
                # TODO() not every subnet will always be bound to every router
                ctx.attach_to_router(subnet, router.cloud_router)
        return network

    def delete_entity(self, ctx, network):
        if not network.external:
            ctx.delete_network(network)
            debug('[{}] {} deleted.', self, str(network))
            return True
        else:
            warn('External networks cannot be deleted via MiniCloud.')
            return False

    ##

    @staticmethod
    def non_external(network):
        return not network.external

    @staticmethod
    def external(network):
        return network.external

    @staticmethod
    def remove_eligible(network):
        return not NetworkManager.external(network)

    def get_routers(self, network, deep_fetch=False):
        from minicloud.model.router import Router

        if deep_fetch or network.router is None:
            cloud_routers = self.get_context(
                network).find_attached_routers(network.cloud_network)
            for cloud_router in cloud_routers:
                router = self.router_manager.get(cloud_router['name'])
                if router is None:
                    warn('Constructing Router from network_manager:get_router')
                    router = Router(cloud_router['name'],
                                    self.cloud_manager, cloud_router)
                    self.router_manager.add(router)
                network.set_router(router)

        return network.routers()

    def external_networks(self, router=None, deep_fetch=False):
        external_networks = self.filtered_list(self.external, deep_fetch)
        if router:
            networks = list()
            for network in external_networks:
                for net_router in self.get_routers(network, deep_fetch):
                    if net_router.name == router.name:
                        networks.append(network)
            return networks
        else:
            return external_networks

    def non_external_networks(self, deep_fetch=False):
        return self.filtered_list(self.non_external, deep_fetch)

    def get_networks_by_router(self, router, deep_fetch=False):
        networks = []
        for network in self.list(deep_fetch):
            if router:
                for net_router in self.get_routers(network, deep_fetch):
                    if net_router.name == router.name:
                        networks.append(network)
            else:
                if len(self.get_routers(network, deep_fetch)) == 0:
                    # Not attached to router
                    networks.append(network)
        return networks

    def attach_network_to_router(self, network, router):
        debug('[{}] attaching {} to router.', self, network)
        for subnet in network.cloud_subnets:
            self.get_context(network).attach_to_router(
                subnet, router.cloud_router)
        network.set_router(router)

    def detach_network_from_router(self, network, router=None):
        debug('[{}] detaching {} from router.', self, network)
        routers = []
        if router:
            routers.append(router)
        else:
            routers = self.get_routers(network)
        for router in routers:
            network.unset_router()
            for subnet in network.cloud_subnets:
                self.get_context(network).detach_from_router(
                    subnet, router.cloud_router)

    def allocate_public_ip(self, network, port_id=None):
        debug('[{}] allocate_public_ip ({}, {})', self, network, port_id)
        # check for public ip no longer in use, first
        for pip in self.get_public_ips(network):
            debug('[{}] found pip ({})', self, pip)

            if not pip.fixed_ip:
                # can reuse existing public ip
                if port_id:
                    debug('[{}] associating pip to port', self)
                    self.get_context(network).associate_floating_ip(
                        pip.cloud_floating_ip, port_id)
                return pip.ip
        # else
        debug('[{}] could not reuse any public ip.', self)
        return self.get_context(network).allocate_floating_ip(
            network.cloud_network, port_id)

    def add_instance(self, instance):
        self.vm_list(instance.network).append(instance)

    @staticmethod
    def remove_instance(instance):
        if instance.network and instance.network.vm_list:
            instance.network.vm_list.remove(instance)

    def vm_list(self, network):
        if network.vm_list is None:
            network.vm_list = []
            for instance in self.minicloud.instance_manager.list():
                if instance.network_name == network.name:
                    network.vm_list.append(instance)

        return network.vm_list

    def get_vm_count(self, network):
        # noinspection PyTypeChecker
        return len(self.vm_list(network))

    def get_public_ips(self, network):
        debug('[{}] get_public_ips ({})', self, network)
        public_ips = []
        ctx = self.get_context(network)
        for fip in ctx.floating_ips(network=network.cloud_network):
            public_ips.append(ctx.new_public_ip(network.cloud, fip))
        debug('[{}] get_public_ips : found {}.', self, len(public_ips))
        return public_ips

    def deallocate_all_public_ips(self, cleanup=True):
        debug('[{}] deallocate_all_public_ips ({})', self, cleanup)
        if cleanup:
            for ext_net in self.external_networks():
                ctx = self.get_context(ext_net)
                for fip in ctx.floating_ips(network=ext_net.cloud_network):
                    self.deallocate_public_ip(cloud_fip=fip, ctx=ctx)
        debug('[{}] deallocate_all_public_ips completed.', self)

    @staticmethod
    def deallocate_public_ip(public_ip=None, cloud_fip=None,
                             ctx=None, entity=None):
        ctx = ctx or entity.driver_context
        ctx.deallocate_floating_ip(
            public_ip.cloud_floating_ip if public_ip else cloud_fip)
