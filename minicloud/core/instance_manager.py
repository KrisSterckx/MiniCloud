import time

from cloud_resource_manager import CloudResourceManager
from core_out import assert_equals, debug, end, error, output, trace, warn
from core_types import IntegrityException, MiniCloudException, \
    InstanceNotReadyYet

__author__ = 'Kris Sterckx'


class InstanceManager(CloudResourceManager):
    def __init__(self, minicloud):
        super(InstanceManager, self).__init__(minicloud)
        self.network_manager = self.minicloud.network_manager
        self.flavor_manager = self.minicloud.flavor_manager
        self.image_manager = self.minicloud.image_manager
        self.sg_manager = self.minicloud.sg_manager
        debug("[{}] initialized.", self)

    @staticmethod
    def entity_name():
        return 'instance'

    def entity(self, cloud, ctx, cloud_instance):
        try:
            return ctx.new_instance(cloud, cloud_instance)

        except InstanceNotReadyYet:
            debug('Instance {} is not ready yet.' % cloud_instance.name)
            return None

    def get_entities(self, ctx, name=None, deep_list=False):
        return ctx.instances(name)

    def create_entity(self, ctx, instance):
        ctx.boot(instance)
        self.network_manager.add_instance(instance)
        debug('[{}] booted {} in {}.', self,
              instance, instance.network.repr())
        return instance

    def delete_entity(self, ctx, instance):
        self.network_manager.remove_instance(instance)
        ctx.kill(instance)
        return True

    def clear(self, cleanup=True):
        if super(InstanceManager, self).clear(cleanup=cleanup) and cleanup:
            warn('[{}] SLEEPING so servers will be fully destroyed...',
                 self)
            time.sleep(10)

    # new public functions

    def get_server_ports(self, instance):
        """

        :rtype: list
        """
        if instance.ports is None:
            ctx = self.get_context(instance)
            instance.ports = ctx.ports(
                network=instance.cloud_network,
                device_id=ctx.get_instance_device_id(instance),
                compute_only=True)
        return instance.ports

    def get_instance_flavor(self, instance):
        trace('[{}] get_instance_flavor [{}].', self, instance.name)
        if instance.flavor is None:
            warn('[{}] get_instance_flavor: don\'t remove this block.',
                 self)
            cloud_flavor = self.get_context(instance).flavor(
                instance.cloud_flavor)
            instance.flavor = self.flavor_manager.entity(
                instance.cloud, instance.driver_context, cloud_flavor) \
                if cloud_flavor else None
        return instance.flavor

    def get_instance_image(self, instance):
        trace('[{}] get_instance_image [{}].', self, instance.name)
        if instance.image is None:
            warn('[{}] get_instance_image: don\'t remove this block.',
                 self)
            cloud_image = self.get_context(instance).image(
                instance.cloud_image)
            instance.image = self.image_manager.entity(
                instance.cloud, instance.driver_context,
                cloud_image) if cloud_image else None
        return instance.image

    def get_instance_network(self, instance):
        """

        :rtype: Network
        """
        if instance.network is None:
            instance.network = self.network_manager.get(instance.network_name)
            instance.cloud_network = instance.network.cloud_network \
                if instance.network else None
        return instance.network

    def make_routable(self, instance, external_network,
                      ignore_deep_check=False):
        trace('[{}] make_routable ({}, {})', self, instance, external_network)
        if not instance.get_fip():
            if not ignore_deep_check:
                if instance.get_fip(deep=True):
                    return instance.get_fip()
            # unless exited
            self.allocate_floating_ip(instance, external_network)
        # finally
        return instance.get_fip()

    def allocate_floating_ip(self, instance, external_network):
        trace('[{}] allocate_floating_ip ({}, {})', self,
              instance, external_network)
        ports = self.get_server_ports(instance)
        trace('[{}] found {} ports.', self, len(ports) if ports else 0)
        if assert_equals(1, len(ports), 'number of ports', warn_only=True):
            instance.set_fip(
                self.network_manager.allocate_public_ip(
                    external_network, ports[0]))
        else:
            warn('[{}] allocate_floating_ip exited without result!', self)
        return instance.get_fip()

    @staticmethod
    def connect_to_instance(instance, username, password):
        if instance.is_stubbed():
            return

        fip = instance.get_fip(deep=True)
        if fip is None:
            error('Instance {} has no FIP allocated to.' % instance.name)
            raise IntegrityException

        try:
            from paramiko import SSHClient, AutoAddPolicy
        except ImportError as import_e:
            class SSHClient:
                def __init__(self):
                    pass

            class AutoAddPolicy:
                def __init__(self):
                    pass

            error('Can\'t import a critical module {}.', import_e.message)
            error('Please give: pip install paramiko')
            end()

        try_c = 1
        while try_c >= 0:
            try:
                ssh_client = SSHClient()
                ssh_client.set_missing_host_key_policy(AutoAddPolicy())
                ssh_client.connect(fip, username=username, password=password)
                return

            except Exception as e:
                if try_c:
                    output('Retrying...')
                    try_c -= 1
                else:
                    error('SSH error connecting to instance {}: {}',
                          instance.name, e)
                    error('There may be a Security Group constraint?')
                    raise MiniCloudException

    def in_use(self, cluster_name):
        return bool(self.get_instances_by_cluster(cluster_name))

    def get_instances_by_cluster(self, cluster_name, deep_list=False):
        # TODO - optimize
        instances = list()
        for instance in self.list(deep_list):
            if instance.cluster_name == cluster_name:
                instances.append(instance)
        trace('[{}] get_instances_by_cluster: {} instances',
              self, len(instances))
        return instances

    def get_instances_by_network(self, network_name, deep_list=False):
        # TODO - optimize
        instances = list()
        for instance in self.list(deep_list):
            if instance.network_name == network_name:
                instances.append(instance)
        trace('[{}] get_instances_by_network: {} instances',
              self, len(instances))
        return instances

    def get_instance_by_ip(self, ip):
        debug('[{}] get_instance_by_ip ({}).', self, ip)
        # TODO - optimize
        for instance in self.list():
            if instance.ip == ip:
                return instance
        return None

    def get_instance_by_cloud_instance_id(self, cloud_instance_id):
        trace('[{}] get_instance_by_cloud_instance_id ({}).', self,
              str(cloud_instance_id))
        # TODO - optimize
        for instance in self.list():
            if instance.cloud_instance.id == cloud_instance_id:
                return instance
        return None
