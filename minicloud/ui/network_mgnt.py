from minicloud.core.core_in import string_input, boolean_input
from minicloud.core.core_out import output, error
from minicloud.core.core_types import MiniCloudException,\
    DoesNotExistException, IntegrityException

from entity_mgnt import EntityMgnt

__author__ = 'Kris Sterckx'


class NetworkMgnt(EntityMgnt):
    def __init__(self, minicloud_mgnt):
        super(NetworkMgnt, self).__init__(
            minicloud_mgnt.manager.network_manager)
        self.minicloud = minicloud_mgnt.manager
        self.minicloud_mgnt = minicloud_mgnt
        self.router_manager = minicloud_mgnt.manager.router_manager
        self.instance_manager = minicloud_mgnt.manager.instance_manager

    def obtain_choices(self):
        class Choices:
            def __init__(self):
                pass

            TOPOLOGY = 1
            LIST = 2
            ADD = 3
            ATTACH = 4
            DETACH = 5
            PUBLIC_IPS = 6
            REMOVE_PUBLIC_IP = 7
            REMOVE = 8

            options_list = ['%s topology' % self.entity_name.title(),
                            'List %ss' % self.entity_name,
                            'Add %s' % self.entity_name,
                            'Attach %s to a router' % self.entity_name,
                            'Detach %s from router' % self.entity_name,
                            'List public IPs',
                            'Remove public IP',
                            'Remove %s' % self.entity_name,
                            'Exit']
        return Choices()

    def extra_entity_management(self, choice):
        if choice == self.obtain_choices().ATTACH:
            self.attach()
            return True
        elif choice == self.obtain_choices().DETACH:
            self.detach()
            return True
        elif choice == self.obtain_choices().PUBLIC_IPS:
            self.public_ips()
            return True
        elif choice == self.obtain_choices().REMOVE_PUBLIC_IP:
            self.remove_public_ip()
            return True
        else:
            return False

    def obtain_entity_to_add(self):
        from minicloud.model.network import Network

        name = string_input('Name')
        # external = boolean_input('Do you want this network to be external '
        #                          '(mind policies!)', default=False)
        external = False
        cidrs = [self.obtain_cidr()]
        if boolean_input('Do you want to add another cidr', default=False):
            cidrs.append(self.obtain_cidr())
        cloud = self.obtain_entity(
            manager=self.minicloud.cloud_manager)

        if cloud:
            router = None
            if not external:
                if self.router_manager.list():
                    router = self.obtain_entity(
                        'Router to attach to, if any (else give none)',
                        manager=self.router_manager)
                elif boolean_input(
                        'Do you want this network to be connected to a router',
                        default=False):
                    router = self.new_router(cloud)

            return Network(name, cidrs, external, router, cloud)
        else:
            return None

    def attach(self):
        try:
            network = self.obtain_entity(
                '\nWhich network would you like to attach',
                self.manager.non_external)

            if network:
                router = None
                routers = self.manager.get_routers(network)
                if routers:
                    error('This network is already attached to router {}. '
                          'Multiple router support is not supported at '
                          'this stage.',
                          routers[0])
                else:
                    router = self.obtain_entity(
                        'Which router would you like to attach to',
                        manager=self.router_manager,
                        return_immediately_if_no_entity=True,
                    )

                    if not router:
                        if boolean_input('Do you want to create a new router'):
                            router = self.new_router(network.cloud)

                if router:
                    self.manager.attach_network_to_router(network, router)
                    output('Network attached.')
                    return

            output('No network attached.')
        except DoesNotExistException:
            output('No network attached.')
        except MiniCloudException:
            error('Attaching the network failed.')

    def detach(self, network=None):
        try:
            if network is None:
                network = self.obtain_entity(
                    '\nWhich network would you like to detach',
                    self.manager.non_external)

            if network:
                routers = self.manager.get_routers(network)
                if len(routers) == 1:
                    self.manager.detach_network_from_router(
                        network, routers[0])
                    output('Network detached.')
                    return

                elif len(routers) > 1:
                    error('Multiple routers detected which '
                          'is not implemented yet, sorry.')
                else:
                    error('Can\'t detach as there is no router attached.')

            output('No network detached.')
        except DoesNotExistException:
            output('No network detached.')
        except MiniCloudException:
            error('Detaching the network failed.')

    def check_for_remove(self, network):
        if network.external:
            error('You can\'t delete this network as it is external.')
            return False
        else:
            routers = self.manager.get_routers(network)
            if routers:
                output('The network is attached to router {}. Detaching it.',
                       routers[0].name)
                self.detach(network)
            return True

    def new_network(self, cloud, external=False):
        from minicloud.model.network import Network
        net_name = string_input('Network name')
        if external:
            cidr = '169.169.10.1/24'  # fixed for now
        else:
            cidr = self.obtain_cidr()
        network = Network(net_name, [cidr], external, None, cloud)
        while True:
            try:
                return self.manager.add(network)
            except IntegrityException as e:
                if not boolean_input('Would you like to re-enter'):
                    raise e

    def new_router(self, cloud):
        from minicloud.model.router import Router
        router = Router(string_input('Router name'), cloud)
        while True:
            try:
                return self.router_manager.add(router)
            except IntegrityException as e:
                if not boolean_input('Would you like to re-enter'):
                    raise e

    def public_ips(self):
        try:
            ext_net = self.obtain_entity(
                'Which network do you want to see public IP listed from',
                self.manager.external)

            if ext_net:
                pips = self.manager.get_public_ips(ext_net)
                if pips:
                    output('\nPublic IP\'s:')
                    for pip in pips:
                        if pip.fixed_ip:
                            instance = self.instance_manager.\
                                get_instance_by_ip(pip.fixed_ip)
                            output('  {}\tin use by \'{}\'',
                                   pip.ip, instance.name)
                        else:
                            output('  {}\tfree', pip.ip)
                else:
                    output('\nNo public IP is allocated.')

        except MiniCloudException:
            error('Listing public IPs failed.')

    def remove_public_ip(self):
        try:
            ext_net = self.obtain_entity(
                'Network on which the public IP resides',
                self.manager.external)

            if ext_net:
                pips = self.manager.get_public_ips(ext_net)
                if pips:
                    pip_dict = self.dictionarize(pips)
                    pip = self.obtain_entity_name(
                        'Select a public IP (or give \'none\'',
                        pip_dict.keys(),
                        allow_none=True)

                    if pip:
                        self.manager.deallocate_public_ip(
                            pip_dict[pip], entity=ext_net.cloud, )
                        output('Public IP removed.')
                        return

            output('No public IP removed.')
        except MiniCloudException:
            error('Removing public IP failed.')

    @staticmethod
    def force_deep_topology():
        return False  # never deep fetch unless cache is empty

    def get_entity_mgnt(self):
        return self.minicloud_mgnt.router_mgnt

    def topology(self, level, network, deep_topology,
                 root_indent, root_prefix, prefix,
                 show_empty_entities=False, optimize_list=False):
        self.minicloud.network_manager.get_vm_count(network)
        return root_indent + root_prefix + network.repr() + '\n', 1, True

    ###

    @staticmethod
    def obtain_cidr():
        from minicloud.model.network import Network

        while True:
            cidr = string_input('CIDR')
            if cidr == 'none':
                return None
            elif not Network.check_cidr(cidr):
                error('This is not a valid CIDR. '
                      'Please enter again, or give \'none\'')
            else:
                break
        return cidr
