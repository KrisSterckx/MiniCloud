from entity import ContextualChildEntity

from minicloud.core.core_out import debug, error, info
from minicloud.core.core_types import IntegrityException
from minicloud.core.core_utils import pop_first

import time

__author__ = 'Kris Sterckx'


class Instance(ContextualChildEntity):

    def __init__(self, name,
                 cluster_name=None,
                 flavor=None,
                 image=None,
                 sg=None,
                 network=None,
                 # until here passed as user input when spinning VM
                 network_name=None,
                 cloud_flavor=None,
                 cloud_image=None,
                 cloud_sg=None,
                 ip=None,
                 cloud=None,
                 cloud_instance=None,
                 cloud_instance_status=None,
                 driver_context=None):
        super(self.__class__, self).__init__(name, driver_context)
        self.cluster_name = cluster_name
        self.flavor = flavor
        self.image = image
        self.sg = sg
        self.network = network
        # ---
        self.network_name = network_name \
            if network_name else network.name if network else None
        self.cloud_flavor = cloud_flavor \
            if cloud_flavor else flavor.cloud_flavor if flavor else None
        self.cloud_image = cloud_image \
            if cloud_image else image.cloud_image if image else None
        self.cloud_sg = cloud_sg \
            if cloud_sg else sg.cloud_sg if sg else None
        self.ip = ip
        self.cloud_network = network.cloud_network if network else None
        self.cloud = cloud
        self.cloud_instance = cloud_instance
        self.status = cloud_instance_status
        self.ports = None
        self.fip = None

    def repr(self):
        return 'Instance: %s [%s] (%s) [%s] %s[%s]' % \
               (self.name,
                self.ip,
                self.network_name,
                (self.cloud_sg.name if self.cloud_sg and hasattr(self.cloud_sg,
                                                                 'name')
                 else self.cloud_sg['name'] if self.cloud_sg else ''),
                ('[' + self.get_fip() + '] ') if self.get_fip() else '',
                self.status)

    def parent_name(self):
        return self.cluster_name

    def reread(self):
        info('[{}] reread.', self)
        self.driver_context.reread_instance(self)
        return self

    def get_fip(self, deep=False):
        """

        :rtype: PublicIp
        """
        debug('[{}] get_fip({}).', self, deep)

        if self.fip:
            debug('[{}] get_fip() instance already has fip.', self)
            return pop_first(self.fip)
        else:
            if deep:
                fip = self.driver_context.get_floating_ip(self.cloud_instance)
                self.set_fip(fip)
                return fip
            else:
                return None

    def set_fip(self, fip):
        self.fip = list()
        if fip:
            debug('[{}] set_fip({}).', self, str(fip))
            self.fip.append(fip)

    @property
    def ip_with_prefix(self):
        if self.network:
            return (self.ip + '/' + self.network.prefix_length()) \
                if self.network else self.ip
        else:
            return None

    def is_stubbed(self):
        return self.cloud.is_stubbed()

    def check_status(self, status='ACTIVE', negative_check=False, deep=False):
        if not negative_check and self.status == status or \
                negative_check and self.status != status:
            return True

        return self.reread().check_status(status, negative_check) if deep \
            else False

    def when_active(self):
        while True:
            if self.check_status('BUILD', True, True):
                break
            else:
                time.sleep(1)
        return self.status == 'ACTIVE'

    def is_active(self, deep=False):
        return self.check_status(deep=deep)

    def is_routable(self, deep=False):
        routable = self.get_fip(deep) is not None
        debug('[{}] is {}.', self, 'routable' if routable else 'not routable')
        return routable

    def suggested_credentials(self):
        suggested_username = None
        suggested_password = None

        if self.image is None:
            error('[{}] No image!', self)
            raise IntegrityException

        elif self.image.name.lower().__contains__('cirr'):
            suggested_username = 'cirros'
            suggested_password = 'cubswin:)'

        return suggested_username, suggested_password
