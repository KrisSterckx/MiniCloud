from cached_entity_manager import CachedStoredEntityManager
from core_out import debug, info

__author__ = 'Kris Sterckx'


class CloudManager(CachedStoredEntityManager):
    def __init__(self, minicloud):
        super(CloudManager, self).__init__(db=minicloud.db, table='clouds')
        self.minicloud = minicloud
        debug("[{}] initialized.", self)

        # set global ref
        from mini_cloud import MiniCloud
        MiniCloud.the_cloud_manager = self

    @staticmethod
    def entity_name():
        return 'cloud'

    @staticmethod
    def is_stub_cloud(cloud):
        return cloud.is_stubbed()

    def add(self, named_entity, skip_check=False):
        entity = super(CloudManager, self).add(named_entity)
        if self.is_stub_cloud(entity):
            CloudManager.stub_cloud_cache = entity
        # add unnamed cluster
        self.minicloud.cluster_manager.add_unnamed_cluster(entity)
        return entity

    def remove(self, entity):
        removed = super(CloudManager, self).remove(entity)
        if removed and self.is_stub_cloud(entity):
            CloudManager.stub_cloud_cache = 0
        return removed

    def type_cast(self, entity):
        from minicloud.model.cloud import Cloud
        return Cloud(_dict=entity) if entity else None

    def get_child_manager(self):
        return self.minicloud.cluster_manager

    stub_cloud_cache = None  # either None (don't know), 0 (no) or stub cloud

    def get_first_stub_cloud(self):
        if CloudManager.stub_cloud_cache is None:
            # note :
            # one can never get here with a filled cache, which avoids endless
            # loop in list() call ... as when cache is not filled, the
            # never_clear_cache is not invoked
            for cloud in self.list(trust_cache_when_filled=True):
                if self.is_stub_cloud(cloud):
                    CloudManager.stub_cloud_cache = cloud
                    info('[{}] has STUB cloud!', self)
                    return cloud
            # no stub found , set to 0
            CloudManager.stub_cloud_cache = 0

        return CloudManager.stub_cloud_cache

    def has_stub(self):
        fsc = self.get_first_stub_cloud()
        has_stub = fsc is not None and fsc != 0
        return has_stub

    def has_children(self, name):
        # clouds have clusters but empty clusters don't count, so check for
        # grand children instead
        for cluster in self.get_children(name):
            if self.get_child_manager().has_children(cluster.name):
                return True
        return False
