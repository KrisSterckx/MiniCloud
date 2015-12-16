from cloud_manager import CloudManager
from cluster_manager import ClusterManager
from core_in import shell_variable
from core_out import debug, error, trace
from core_types import IntegrityException
from core_utils import _, __
from flavor_manager import FlavorManager
from image_manager import ImageManager
from instance_manager import InstanceManager
from network_manager import NetworkManager
from security_group_manager import SecurityGroupManager
from system import System
from router_manager import RouterManager

__author__ = 'Kris Sterckx'


class MiniCloud:
    the_cloud_manager = None

    SLOW_SYSTEM = shell_variable('WINDIR')  # slow on windows

    def __init__(self, db, cluster_support=True):
        if db:
            self.db = ('mysql+pymysql://' + db.username + ':' + db.password +
                       '@' + db.host + '/' + db.database)
        else:
            self.db = 'in_memory://null'

        # stores
        if self.SLOW_SYSTEM:
            _('Loading...', thru_silent_mode=True)
        self.system = System(self)
        self.cloud_manager = CloudManager(self)
        self.cluster_manager = ClusterManager(self)
        self.router_manager = RouterManager(self)
        self.network_manager = NetworkManager(self)
        self.flavor_manager = FlavorManager(self)
        self.image_manager = ImageManager(self)
        self.sg_manager = SecurityGroupManager(self)
        self.instance_manager = InstanceManager(self)
        if self.SLOW_SYSTEM:
            __(thru_silent_mode=True)

        self.driver_contexts = {}
        self.cluster_support = cluster_support

        debug("[{}] initialized.\n", self)

    @staticmethod
    def entity_name():
        return 'MiniCloud'

    def __repr__(self):
        return self.entity_name() + ' mgr'

    def clusters_supported(self):
        return self.cluster_support

    @property
    def managers(self):
        return (self.infra_managers + self.flavor_managers +
                self.deployment_managers)

    @property
    def deployment_managers(self):
        """deployment_managers

        :rtype: list
        """
        return [self.sg_manager, self.router_manager, self.network_manager,
                self.instance_manager]

    @property
    def flavor_managers(self):
        return [self.flavor_manager, self.image_manager]

    @property
    def infra_managers(self):
        """infra_managers

        :rtype: list
        """
        return [self.cloud_manager, self.cluster_manager]

    @classmethod
    def cloud_manager(cls):
        return cls.the_cloud_manager

    @classmethod
    def get_cloud(cls):
        clouds = cls.cloud_manager().list()
        if len(clouds) > 1:
            raise IntegrityException('More than one cloud is provisioned; '
                                     'need to be more specific')
        elif clouds:
            return clouds[0]
        else:
            return None

    def clear(self, cleanup=True, delete_cloud=False):
        self.network_manager.deallocate_all_public_ips(cleanup)
        for m in reversed(
                (self.infra_managers + self.deployment_managers)
                if delete_cloud else self.deployment_managers):
            m.clear(cleanup)

    def reset(self):
        for m in reversed(self.managers):
            m.reset()

    @staticmethod  # keep static, as is registered as function callback
    def never_clear_cache():
        cm = MiniCloud.cloud_manager()
        if cm:
            # never clear cache when no persistency OR stubbed cloud
            ncc = not cm.have_persistency() or cm.has_stub()

            trace('MiniCloud.never_clear_cache() yielding {} ({})', ncc,
                  'as no persistency' if not cm.have_persistency
                  else 'as stub cloud' if ncc else 'as no stub cloud')
            return ncc
        else:
            error('MiniCloud.never_clear_cache executed while '
                  'cloud manager not yet initialized', fatal=True, bug=True)
