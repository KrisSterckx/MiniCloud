from minicloud.core.core_in import string_input, boolean_input
from minicloud.core.core_out import error, output
from minicloud.core.core_types import DoesNotExistException,\
    MiniCloudException

from entity_mgnt import EntityMgnt

__author__ = 'Kris Sterckx'


class InstanceMgnt(EntityMgnt):
    def __init__(self, minicloud_mgnt):
        super(InstanceMgnt, self).__init__(
            minicloud_mgnt.manager.instance_manager)
        self.minicloud_mgnt = minicloud_mgnt
        self.network_mgnt = minicloud_mgnt.network_mgnt

        self.cloud_manager = minicloud_mgnt.manager.cloud_manager
        self.cluster_manager = minicloud_mgnt.manager.cluster_manager
        self.network_manager = minicloud_mgnt.manager.network_manager
        self.router_manager = minicloud_mgnt.manager.router_manager
        self.sg_manager = minicloud_mgnt.manager.sg_manager

    def obtain_choices(self):
        class Choices(object):
            def __init__(self):
                pass

            TOPOLOGY = 1
            LIST = 2
            ADD = 3
            ROUTABLE = 4
            CONNECT = 5
            REMOVE = 6

            options_list = ['%s topology' % self.entity_name.title(),
                            'List %ss' % self.entity_name,
                            'Add %s' % self.entity_name,
                            'Make %s routable' % self.entity_name,
                            'Connect to %s' % self.entity_name,
                            'Remove %s' % self.entity_name,
                            'Exit']
        return Choices()

    def extra_entity_management(self, choice):
        if choice == self.obtain_choices().ROUTABLE:
            self.make_routable()
            return True
        elif choice == self.obtain_choices().CONNECT:
            self.connect()
            return True
        else:
            return False

    def obtain_entity_to_add(self):
        pass

    def add_entity(self, retry=False):
        from minicloud.model.instance import Instance
        name = string_input('Name')
        if self.minicloud_mgnt.manager.clusters_supported() and \
                len(self.cluster_manager.list()) > 1 and \
                boolean_input('\nDo you want to deploy this instance in a '
                              'predefined cluster'):
            cluster = self.obtain_entity(
                manager=self.cluster_manager,
                choose_from_display=True, allow_none=True)
            if cluster:
                cloud = self.manager.get_cloud(cluster)
            else:
                return None
        else:
            cloud = self.obtain_entity(
                'Which cloud do you want to boot an instance in?',
                manager=self.cloud_manager,
                choose_from_display=True,
                skip_questioning_if_only_one_entity=True,
                return_immediately_if_no_entity=True)
            if cloud is None:
                error('Please first create a Cloud.')
                return None
            else:
                cluster = self.cluster_manager.add_unnamed_cluster(cloud)

        flavor = self.obtain_entity(
            'Which flavor do you want to boot from?',
            manager=self.manager.flavor_manager,
            choose_from_display=True, return_immediately_if_no_entity=True)
        if not flavor:
            error('No flavor found.')
            return None

        image = self.obtain_entity(
            'Which image do you want to boot from?',
            manager=self.manager.image_manager,
            choose_from_display=True, return_immediately_if_no_entity=True)
        if not image:
            error('No image found.')
            return None

        sgs = self.sg_manager.list()
        public_ssh_sg = None
        for sg in sgs:
            if sg.name == 'public_ssh':
                public_ssh_sg = sg
                break

        if not public_ssh_sg and boolean_input(
                '\nNo public_ssh security group was found. '
                'Would you like to create it'):
            sg = self.sg_manager.create_ssh_sg_group(cloud)
            sgs.insert(0, sg)  # set it 1st

        sg = self.obtain_entity(
            'Which security group do you want to boot with?',
            manager=self.manager.sg_manager,
            choose_from_display=True, return_immediately_if_no_entity=True,
            entities=sgs)

        if not sg:
            error('No Security Group found.')
            return None

        network = self.obtain_entity(
            'Which network do you want to boot in?',
            self.network_manager.non_external,
            manager=self.network_manager,
            choose_from_display=True, return_immediately_if_no_entity=True)

        if not network:
            output()
            if boolean_input('No network found. Do you want to create one'):
                network = self.network_mgnt.new_network(cloud)
            else:
                return None

        output()
        make_routable = boolean_input(
            'Do you want this instance to be routable', default=False)

        if make_routable:
            external_network = self.obtain_external_network(network)
        else:
            external_network = None

        instance = Instance(
            name, cluster.name if cluster else None,
            flavor, image, sg, network, cloud=cloud)

        self.manager.add(instance)

        if make_routable:
            fip = self.make_instance_routable(instance, external_network)
            if fip:
                output('Instance is routable via {}.', fip)

        return instance

    @staticmethod
    def force_deep_topology():
        return True

    def get_entity_mgnt(self):
        return self.minicloud_mgnt.cloud_mgnt

    def topology(self, level, instance, deep_topology,
                 root_indent, root_prefix, prefix,
                 show_empty_entities=False, optimize_list=False):
        instance.get_fip(deep=True)
        return root_indent + root_prefix + instance.repr() + '\n', 1, True

    def make_routable(self):
        output('\nPlease enter the name of the instance '
               'you would like to make routable')
        try:
            instance = self.obtain_entity(
                filter_f=self.is_active_and_not_routable)
            if instance:
                fip = self.make_instance_routable(instance)
                if fip:
                    output('{} is publicly routable via {}',
                           instance.name, fip)
                    return

            output('No instance made routable.')

        except DoesNotExistException:
            output('Invalid instance')
        except MiniCloudException:
            error('Making instance routable failed.')

    def connect(self):
        output('\nPlease enter the name of the instance '
               'you would like to connect to.')
        try:
            fip = None
            instance = self.obtain_entity(filter_f=self.is_active)
            if instance:
                fip = instance.get_fip(deep=True)
                if fip is None:
                    if boolean_input(
                            'This instance is not publicly routable yet.\n'
                            'Do you want to make it routable'):
                        fip = self.make_instance_routable(instance)

            if fip is None:
                output('No instance connected to.')
                return

            output('{} is publicly routable via {}', instance.name, fip)
            output()

            suggested_username, suggested_password = \
                instance.suggested_credentials()

            output('Connecting to {}...', fip)
            username = string_input('Username', default=suggested_username)
            password = string_input('Password', default=suggested_password)

            # connect
            self.manager.connect_to_instance(instance, username, password)
            output()
            output('Successfully established a connection.\n'
                   'Returning to MiniCloud now.')

        except DoesNotExistException:
            output('No instance connected to.')
        except MiniCloudException:
            error('Connecting to the instance failed.')

    def obtain_external_network(self, network):
        router_existing = False
        routers = self.network_manager.get_routers(network)
        if routers:
            router_existing = True
            router = routers[0]
        else:
            router = self.make_network_routable(network)
            if not router:
                return None

        already_routed = False
        external_networks = self.network_manager.external_networks(router)
        if external_networks:
            already_routed = True
        else:
            if router_existing:
                output('The network is routed but not externally routed yet.')
            external_networks = self.network_manager.external_networks()
            if not external_networks:
                output('You unfortunately have no external networks.')
                if boolean_input('Do you want to create an external network'):
                    external_networks = [self.network_mgnt.new_network(
                        network.cloud, external=True)]
                else:
                    return None

        external_network = self.obtain_entity(
            'Which network do you want to route to',
            manager=self.network_manager,
            skip_questioning_if_only_one_entity=True,
            entities=external_networks)

        if not already_routed:
            output('Uplinking router to {}.', external_network.name)
            self.router_manager.uplink(router, external_network)

        return external_network

    def make_instance_routable(self, instance, external_network=None):
        fip = instance.get_fip(deep=True)
        if fip:
            output('The instance is already routable as {}', fip)
            return fip

        network = self.manager.get_instance_network(instance)
        if not external_network:
            external_network = self.obtain_external_network(network)

        if external_network:
            output('Waiting for instance to be active...')
            if instance.when_active():
                fip = self.manager.make_routable(instance, external_network)

        return fip

    def make_network_routable(self, network):
        router = None
        routers = self.router_manager.list()
        if routers and boolean_input(
                'Do you want to attach to existing router' +
                (' ' + routers[0].name) if len(routers) == 1 else ''):
            if len(routers) == 1:
                router = routers[0]
            else:
                router = self.obtain_entity(
                    'Please enter the name of the router to attach to',
                    manager=self.router_manager, entities=routers)

        elif boolean_input('Do you want to create a router'):
            router = self.network_mgnt.new_router(network.cloud)

        if router:
            output('Attaching network.')
            self.network_manager.attach_network_to_router(network, router)

        return router

    @staticmethod
    def is_active(instance):
        return instance.is_active()

    @staticmethod
    def is_active_and_not_routable(instance):
        return instance.is_active() and not instance.is_routable()
