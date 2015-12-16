from abc import ABCMeta, abstractmethod

from core_out import debug, error, info, output, trace
from core_utils import trace_enabled

__author__ = 'Kris Sterckx'


class EntityManager:
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def entity_name():
        return 'entity'

    def entity_title(self):
        return self.entity_name().title()

    def entities_title(self):
        return self.entity_title() + 's'

    def __repr__(self):
        return self.entity_title() + ' mgr'

    def list(self, deep_list=False, fetch_cache_only=False,
             trust_cache_when_filled=False,
             name=None, parent_name=None):
        return self.sort_list(self.unsorted_list(
            deep_list, fetch_cache_only, trust_cache_when_filled,
            name, parent_name))

    @abstractmethod
    def unsorted_list(self, deep_list=False, fetch_cache_only=False,
                      trust_cache_when_filled=False,
                      name=None, parent_name=None):
        return list()

    @abstractmethod
    def count(self, parent_name=None):
        return 0

    @abstractmethod
    def get(self, name):
        return None

    def get_entity(self, entity):
        if entity:
            return self.get(entity.name)
        else:
            return None

    def get_singleton_entity(self):
        _list = self.list()
        if len(_list) == 1:
            return _list[0]
        else:
            return None

    @abstractmethod
    def add(self, named_entity):
        pass

    @abstractmethod
    def update(self, entity, data):
        pass

    def deep_remove(self, entity):
        debug('[{}] deep_remove [{}]', self, entity.name)
        return self.undeclare_children(entity.name) and \
            self.remove(entity)

    def deep_undeclare(self, entity):
        debug('[{}] deep_undeclare [{}]', self, entity.name)
        return self.undeclare_children(entity.name) and \
            self.undeclare(entity)

    @abstractmethod
    def remove(self, entity):
        pass

    @abstractmethod
    def undeclare(self, entity):
        pass

    def reset(self):
        pass  # nothing to do by default

    @abstractmethod
    def clear(self, cleanup=True):
        pass

    def filtered_list(self, filter_f=None, deep_list=False, name_only=False,
                      items=None):
        _list = []
        if items is None:
            # explicit design choice to list all first as that way the cache
            # is correctly populated
            items = self.list(deep_list)
        for item in items:
            if not filter_f or filter_f(item):
                if name_only:
                    _list.append(item.name)
                else:
                    _list.append(item)
        return _list

    @staticmethod
    def sort_list(a_list):
        return sorted(a_list, key=lambda x: x.name)

    def list_entity_names(self, filter_f=None, entities=None):
        return self.filtered_list(filter_f, name_only=True, items=entities)

    @staticmethod
    def remove_eligible(entity):
        return True

    def get_child_manager(self):
        return None  # None by default

    def get_children(self, name):
        child_manager = self.get_child_manager()
        if child_manager:
            return child_manager.list(parent_name=name, fetch_cache_only=True)
        else:
            return []

    def has_children(self, name):
        child_manager = self.get_child_manager()
        if child_manager:
            return child_manager.count(parent_name=name)
        else:
            return 0

    def undeclare_children(self, name):
        trace('[{}] undeclare_children [{}]', self, name)
        for c in self.get_children(name):
            self.get_child_manager().deep_undeclare(c)
        return True

    def trace_dump(self, alist=None, max_count=5):
        if alist is None:
            alist = self.list()
        if trace_enabled() and len(alist) <= max_count:
            for i in alist:
                trace('[{}] list() -> {}', self, i.repr())


class EntityManagerImpl(EntityManager):
    def __init__(self, db=None, table=None, *args, **kwargs):
        from minicloud.model.entity import MiniCloudEntityStore
        super(EntityManagerImpl, self).__init__()
        if db and table:
            self._entity_store = MiniCloudEntityStore(db, table)
        else:
            error('[{}] No DB info', self, fatal=True, bug=True)

    def type_cast(self, entity):
        return entity

    def unsorted_list(self, deep_list=False, fetch_cache_only=False,
                      trust_cache_when_filled=False,
                      name=None, parent_name=None):
        info('[{}] unsorted_list(): fetch from store', self)
        return self.list_from_store(name, parent_name)

    def get(self, name):
        return self.type_cast(self.store_get(name))

    def add(self, named_entity, skip_check=False):
        return self.add_to_store(named_entity)

    def update(self, entity, data):
        return self.update_store(data)

    def remove(self, entity):
        self.remove_from_store(entity)
        return True

    def undeclare(self, entity):
        return self.remove(entity)

    def count(self, parent_name=None):
        if parent_name:
            cnt = 0
            for e in self._entity_store.all():
                if e.is_child(parent_name):
                    cnt += 1
            return cnt
        else:
            return self._entity_store.count()

    def clear(self, _=None):
        info('[{}] drop', self)
        c = self._entity_store.count()
        self._entity_store.drop_all()
        if c:
            output('{} {} were cleared.', c, self.entities_title(),
                   thru_silent_mode=True)

    # name persistent implementations by dedicated methods
    # helps dealing with inheritance

    def list_from_store(self, name=None, parent_name=None,
                        exclude_entity=None):
        if parent_name:
            raise NotImplemented

        _list = []
        for entity in self._entity_store.all():
            if (not name or name == entity['name']) and \
                    (exclude_entity is None or
                     exclude_entity.name != entity['name']):
                _list.append(self.type_cast(entity))
        return _list

    def add_to_store(self, entity):
        self._entity_store.upsert(entity)
        return entity

    def store_get(self, name):
        return self._entity_store.find_one(name)

    def update_store(self, data):
        self._entity_store.update(data)

    def remove_from_store(self, entity):
        return self._entity_store.delete(entity)
