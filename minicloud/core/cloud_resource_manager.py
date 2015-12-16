from abc import abstractmethod

from cached_entity_manager import CachedEntityManager
from core_types import MiniCloudException, IntegrityException
from core_out import debug, error, trace

__author__ = 'Kris Sterckx'


#
# A Manager managing non-persisted resources on a Cloud manager,
# possibly bound to a Cluster
#

class CloudResourceManager(CachedEntityManager):
    def __init__(self, minicloud):
        from mini_cloud import MiniCloud

        super(CloudResourceManager, self).__init__()
        self.minicloud = minicloud
        self.set_never_clear_cache(MiniCloud.never_clear_cache)

    @property
    def username(self):
        return self.minicloud.username

    @property
    def tenant(self):
        return self.minicloud.tenant

    @property
    def password(self):
        return self.minicloud.password

    @property
    def cloud_manager(self):
        return self.minicloud.cloud_manager

    @property
    def cluster_manager(self):
        return self.minicloud.cluster_manager

    def get_context(self, entity):
        return entity.context() if entity.context() else \
            self.get_entity_driver_context(entity)

    def list_entities(self, name=None, deep_list=False, parent_name=None,
                      exclude_entity=None):

        # debug('[{}] list_entities(name={}, deep_list={})',
        #       self,
        #       name if name is not None else 'None',
        #       deep_list)

        try:
            clouds = self.cloud_manager.list()
            trace('[{}] list_entities(): clouds = {}.', self, ', '.join(
                str(e) for e in clouds))

            if clouds:
                entities = []
                for cloud in clouds:
                    ctx = cloud.context()
                    if ctx and ctx.authenticated():
                        cloud_entities = self.get_entities(
                            ctx, name, deep_list)

                        for cloud_entity in cloud_entities:
                            entity = self.entity(cloud, ctx, cloud_entity)
                            if (exclude_entity is None or
                                    exclude_entity.name != entity.name):
                                if entity and (not parent_name or
                                               entity.is_child(parent_name)):
                                    entities.append(entity)

                trace('[{}] list_entities(): entities = {}.', self, ', '.join(
                    str(e) for e in entities))

                return entities
            else:
                error('[{}] No clouds!', self)
                raise IntegrityException

        except MiniCloudException:
            error('[{}] Failed to list {}s.', self, self.entity_name())
            return list()

    def add_entity(self, entity):
        try:
            ctx = self.get_context(entity)
            if ctx and ctx.authenticated():
                self.create_entity(ctx, entity)
                entity.set_context(ctx)
                debug('[{}] {} added.', self, entity.repr())
                return entity
            else:
                raise IntegrityException

        except MiniCloudException as e:
            error('[{}] Failed to create {} \'{}\'.',
                  self, self.entity_name(), entity.name)
            raise e

    def update_entity(self, entity, data):
        try:
            ctx = self.get_context(entity)
            if ctx and ctx.authenticated():
                self.reconfig_entity(ctx, entity, data)
                debug('[{}] {} {} updated.', self,
                      entity.name, self.entity_name())
            else:
                raise IntegrityException

        except MiniCloudException as e:
            error('[{}] Failed to update {} \'{}\'.',
                  self, self.entity_name(), entity.name)
            raise e

    def remove_entity(self, entity):
        try:
            ctx = self.get_context(entity)
            if ctx and ctx.authenticated():
                if self.delete_entity(ctx, entity):
                    debug('[{}] {} {} removed.', self,
                          entity.name, self.entity_name())
                    return True
                else:
                    return False
            else:
                error('[{}] Could not authenticate.')
                raise IntegrityException

        except MiniCloudException as e:
            error('[{}] Failed to delete {} \'{}\'.',
                  self, self.entity_name(), entity.name)
            raise e

    # START TO OVERRULE

    @abstractmethod
    def entity(self, cloud, ctx, cloud_entity):
        pass

    @abstractmethod
    def get_entities(self, ctx, name=None, deep_list=False):
        return list()

    @abstractmethod
    def create_entity(self, ctx, entity):
        return entity

    def reconfig_entity(self, ctx, entity, data):
        # no-op by default
        return entity

    @abstractmethod
    def delete_entity(self, ctx, entity):
        pass

    # END TO OVERRULE

    # PRIMITIVES

    def get_entity_driver_context(self, entity):

        if not entity.context():

            if entity.cloud:
                cloud = entity.cloud
                trace('get_entity_driver_context: entity has cloud: {}',
                      cloud)

            elif hasattr(entity, 'cluster_name') and entity.cluster_name and \
                    self.cluster_manager.get(entity.cluster_name):
                cluster = self.cluster_manager.get(entity.cluster_name)
                cloud = self.get_cloud(cluster)
                entity.cloud = cloud
                trace('get_entity_driver_context: '
                      'cloud according cluster_name: {}', cloud)

            else:
                cloud = self.cloud_manager.get_singleton_entity()
                if cloud:
                    # ok, singleton
                    entity.cloud = cloud
                    trace('get_entity_driver_context: '
                          'singleton cloud found: {}', cloud)
                else:
                    error('No driver context can be selected for {}.',
                          entity.name)
                    raise IntegrityException

            entity.set_context(cloud.context())

        return entity.context()

    def get_cloud(self, cluster):
        if not cluster.cloud:
            cluster.cloud = self.cloud_manager.get(cluster.cloud_name)
        return cluster.cloud
