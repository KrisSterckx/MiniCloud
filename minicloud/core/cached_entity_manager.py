from entity_manager import EntityManager, EntityManagerImpl
from core_types import IntegrityException
from core_out import debug, error, info, output, trace
from core_utils import trace_enabled

from abc import abstractmethod

__author__ = 'Kris Sterckx'


class CachedEntityManager(EntityManager):
    def __init__(self, never_clear_cache_f=None, *args, **kwargs):
        super(CachedEntityManager, self).__init__(*args, **kwargs)

        self.cache_is_filled = False
        self.entity_cache = {}
        self.never_clear_cache_f = never_clear_cache_f

    @staticmethod
    def entity_name():
        return 'cached_entity'

    def set_never_clear_cache(self, f):
        self.never_clear_cache_f = f

    def never_clear_cache(self):
        return (self.never_clear_cache_f is not None and
                self.never_clear_cache_f())

    def unsorted_list(self, deep_list=False, fetch_cache_only=False,
                      trust_cache_when_filled=False,
                      name=None, parent_name=None):
        _list = []

        # redefine deep list :
        deep_list = deep_list and not trust_cache_when_filled and \
            not self.trust_cache_when_filled()

        if fetch_cache_only or self.cache_is_filled and not deep_list:
            if name:
                if name in self.entity_cache:
                    debug('[{}] list [name={}] is cache hit.',
                          self, name)

                    _list = self.entity_cache[name]

            elif parent_name:
                for e in self.entity_cache.values():
                    if e.is_child(parent_name):
                        _list.append(e)

                debug('[{}] list [parent_name={}] is yielding {} {}{} '
                      'from cache.', self, parent_name, len(_list),
                      self.entity_name(), 's' if len(_list) > 1 else '')
            else:
                _list = self.entity_cache.values()

                debug('[{}] list() is yielding {} {}{} from cache.',
                      self, len(_list), self.entity_name(),
                      's' if len(_list) > 1 else '')
        else:
            debug('[{}] list() is executing deep fetch{}.', self,
                  ' (deep_list)' if deep_list else '')

            _list = self.full_sync(deep_list)

        self.trace_dump(_list)
        return _list

    def count(self, parent_name=None):
        if not self.is_cache_filled():
            self.full_sync()

        if parent_name:
            cnt = 0
            for e in self.entity_cache.values():
                if e.is_child(parent_name):
                    cnt += 1
            return cnt
        else:
            return len(self.entity_cache)

    def get(self, name):
        return self.cached_get(name)

    def update_cache(self, name):
        return self.deep_fetch(name)

    def deep_fetch(self, name):
        return self.cached_get(
            name, override_cache=not self.never_clear_cache())

    def cached_get(self, name, override_cache=False):
        if override_cache or name not in self.entity_cache:
            if self.is_cache_filled() and not override_cache:
                debug('[{}] get({}) not found in cache', self, name)

                # this is it, it ain't there
                return None

            else:
                debug('[{}] get({}) not {} cache ({})',
                      self, name,
                      'searched in' if override_cache else 'found in',
                      'cache override' if override_cache else
                      'cache is filled' if self.is_cache_filled() else
                      'cache not filled')

            # alright, let's see whether we can fetch it
            entity = self.get_entity(name)
            if entity:
                if override_cache:
                    self.update_entity_cache(entity)
                    debug('[{}] get({}) found and updated.', self, name)
                else:
                    self.add_to_cache(entity, True)
                    debug('[{}] get({}) found and stored.', self, name)

            else:
                debug('[{}] get({}) has no entry found.', self, name)
                debug('[{}] still filling up cache now.', self)

                trace('[{}] get() -> full_sync', self)
                self.full_sync()
                return None

        else:
            # cache hit
            entity = self.entity_cache[name]
            debug('[{}] get({}) is cache hit: {}',
                  self, name, entity.repr())

        trace('[{}] get() -> {}', self, entity.repr())
        return entity

    def full_sync(self, deep_list=False, exclude_entity=None):
        if deep_list or not self.is_cache_filled():
            if trace_enabled():
                trace('[{}] -- full_sync() -- '
                      '[deep_list={}] [exclude_entity={}]',
                      self, deep_list,
                      exclude_entity if exclude_entity else 'none')
            else:
                info('[{}] full_sync()', self)

            if not exclude_entity:
                self.clear_cache()

            entity_list = self.list_entities(deep_list=deep_list,
                                             exclude_entity=exclude_entity)
            for entity in entity_list:
                self.add_to_cache(entity, False)

            self.set_cache_filled()

            trace('[{}] -- full_sync() -- (end)', self)
            return entity_list
        else:
            trace('[{}] full_sync() is no-op', self)
            return None

    def add(self, entity, skip_check=False):
        debug('[{}] --- adding {} ---', self, entity.repr())
        name = entity.name
        if name:
            if skip_check or not self.get(name):
                entity = self.add_entity(entity)
                self.add_to_cache(entity, True)
                debug('[{}] --- adding end ---', self)
                return entity
            else:
                error('Name %s already exists.' % name)
                raise IntegrityException
        else:
            error('Can\'t give empty name.')
            raise IntegrityException

    def update(self, entity, data):
        debug('[{}] update({}).', self, entity.name)
        self.update_entity(entity, data)
        return self.update_cache(entity.name)

    def remove(self, entity):
        debug('[{}] remove({}).', self, entity.name)
        return self.boolean_remove(entity, cleanup=True)

    def undeclare(self, entity):
        return self.boolean_remove(entity, cleanup=False)

    def boolean_remove(self, entity, cleanup=True):
        return self.boolean_entity_remove(entity, cleanup)

    def boolean_entity_remove(self, entity, cleanup=True):
        if entity:
            removed = self.remove_entity(entity) if cleanup else True
            if removed and entity.name in self.entity_cache:  # robustness
                del self.entity_cache[entity.name]
            return removed
        else:
            return False

    def add_to_cache(self, entity, complete_full_cache=False):
        self.entity_cache[entity.name] = entity
        trace('[{}] {} {} added to cache',
              self, entity.name, self.entity_name())
        if complete_full_cache:
            trace('[{}] proceeding with full_sync', self)
            self.full_sync(exclude_entity=entity)
        else:
            self.set_cache_filled()

    def update_entity_cache(self, entity):
        self.entity_cache[entity.name] = entity
        debug('[{}] {} {} updated in cache',
              self, entity.name, self.entity_name())

    def is_cache_filled(self):
        return self.cache_is_filled

    def set_cache_filled(self):
        if not self.is_cache_filled():
            self.cache_is_filled = True
            if trace_enabled():
                trace('[{}] cache is filled ({}).', self, ', '.
                      join(str(e)for e in self.entity_cache))
            else:
                debug('[{}] cache is filled.', self)

    def clear_cache(self):
        if self.is_cache_filled() and not self.never_clear_cache():
            self.entity_cache = {}
            self.cache_is_filled = False
            info('[{}] cache is cleared.', self)

    def reset(self):
        self.clear_cache()

    def clear(self, cleanup=True):
        dropped = 0
        info('[{}] drop', self)
        for entity in self.list(fetch_cache_only=not cleanup):
            info('[{}] About to drop [{}] ...', self, entity)
            if self.boolean_remove(entity, cleanup=cleanup):
                info('[{}] [{}] dropped!', self, entity)
                dropped += 1
        if dropped:
            output('{} {} were cleared.', dropped, self.entities_title(),
                   thru_silent_mode=True)
        return dropped

    def trust_cache_when_filled(self):
        # Can be set by entity manager, by default set ~ never-clear-cache flag
        return self.never_clear_cache()

    # METHODS THAT GO UNDERNEATH :

    def get_entity(self, name):
        trace('[{}] get_entity({})', self, name)
        entities = self.list_entities(name)
        if entities:
            trace('[{}] get_entity({}) -> {}', self, name, entities[0])
            return entities[0]
        else:
            return None

    @abstractmethod
    def list_entities(self, name=None, deep_list=False, parent_name=None,
                      exclude_entity=None):
        """

        :rtype: List
        """
        pass

    @abstractmethod
    def add_entity(self, entity):
        """

        :rtype: Entity
        """
        pass

    @abstractmethod
    def update_entity(self, entity, data):
        pass

    @abstractmethod
    def remove_entity(self, entity):
        pass


class CachedStoredEntityManager(CachedEntityManager, EntityManagerImpl):
    def __init__(self, db, table):
        from mini_cloud import MiniCloud

        super(CachedStoredEntityManager, self).__init__(db=db, table=table)
        self.set_never_clear_cache(MiniCloud.never_clear_cache)

    @staticmethod
    def have_persistency():
        from minicloud.model.entity import MiniCloudEntityStore
        return MiniCloudEntityStore.has_persistency()

    def undeclare(self, entity):
        # in Stored Entity Manager, undeclare is effective remove
        return self.boolean_remove(entity, cleanup=True)

    def list_entities(self, name=None, deep_list=False, parent_name=None,
                      exclude_entity=None):
        debug('[{}] fetching {} from store.', self,
              name if name else 'listing all ' + self.entity_name() + 's')
        return self.list_from_store(name, parent_name, exclude_entity)

    def add_entity(self, entity):
        return self.add_to_store(entity)

    def update_entity(self, entity, data):
        self.update_store(data)

    def remove_entity(self, entity):
        return self.remove_from_store(entity)
