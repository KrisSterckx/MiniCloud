from cached_entity_manager import CachedStoredEntityManager
from core_out import debug

__author__ = 'Kris Sterckx'


class ClusterManager(CachedStoredEntityManager):
    def __init__(self, minicloud):
        super(ClusterManager, self).__init__(db=minicloud.db, table='clusters')
        self.minicloud = minicloud
        debug("[{}] initialized.", self)

    @staticmethod
    def entity_name():
        return 'cluster'

    def type_cast(self, entity):
        from minicloud.model.cluster import Cluster
        return Cluster(_dict=entity) if entity else None

    @staticmethod
    def unnamed_cluster_name(cloud):
        from minicloud.model.cluster import Cluster
        return Cluster.unnamed_cluster_name(cloud.name)

    def unnamed_cluster(self, cloud, skip=False):
        from minicloud.model.cluster import Cluster
        cluster_name = self.unnamed_cluster_name(cloud)
        cluster = self.add(Cluster(cluster_name, cloud.name), skip)
        cluster.cloud = cloud

        return cluster

    def add_unnamed_cluster(self, cloud):
        return self.unnamed_cluster(cloud, True)

    def get_child_manager(self):
        return self.minicloud.instance_manager
