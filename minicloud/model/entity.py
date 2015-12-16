from abc import abstractmethod

import hashlib
import sqlalchemy

from minicloud.core.core_out import assert_equals, assert_not_none,\
    error, fail, info, output, trace
from minicloud.core.core_types import DatabaseException, DatabaseFatalException

__author__ = 'Kris Sterckx'

# http://dataset.readthedocs.org/en/latest/
try:
    import dataset
except ImportError:
    fail('Please install dataset.')


class Entity(object):
    HASH = 'hash'

    def __init__(self, name):
        self.store_name(name)

        info('[{}: {}] created!', str(self.__class__.__name__), self.name)

    @abstractmethod
    def store_name(self, name):
        pass

    @property
    def name(self):
        error('name not set for entity ' + str(self.__class__.__name__),
              fatal=True, bug=True)
        return 'fixme'  # keep editors happy

    @staticmethod
    def gen_hash(s):
        # hash to 8 digit integer
        return int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % 10**8

    @property
    def hash(self):
        # default implementation but optimize me when being used (store hash)
        return self.gen_hash(self.name)

    def __repr__(self):
        return str(self.__class__.__name__) + ': ' + self.name

    # representation (can be overruled)
    def repr(self):
        return str(self)


class StoredEntity(Entity):
    def __init__(self, _store):
        self._store = _store

        super(StoredEntity, self).__init__(_store['name'])

    def store(self):
        return self._store

    def store_name(self, name):
        # not needed to store name again, however store its hash
        self._store[Entity.HASH] = self.gen_hash(name)

    @property
    def name(self):
        return self.get('name')

    @property
    def hash(self):
        return self.get(Entity.HASH)  # optimize

    def get(self, attr):
        try:
            return self._store[attr]
        except KeyError:
            return None


class StoredChildEntity(StoredEntity):
    def __init__(self, _dict):
        super(StoredChildEntity, self).__init__(_dict)

    @abstractmethod
    def parent_name(self):
        pass

    def is_child(self, parent_name):
        return self.parent_name() == parent_name


class NamedValue(StoredEntity):
    def __init__(self, name=None, value=None, _dict=None):
        super(NamedValue, self).__init__(dict(name=name, value=value)
                                         if not _dict else _dict)

    def repr(self):
        return '{%s,%s}' % (self.name, self.value)

    @property
    def value(self):
        return self.get('value')


class ContextualEntity(Entity):
    def __init__(self, name, driver_context):
        self._name = None
        self.driver_context = driver_context

        super(ContextualEntity, self).__init__(name)

    @property
    def name(self):
        return self._name

    def store_name(self, name):
        self._name = name

    def context(self):
        return self.driver_context

    def set_context(self, ctx):
        self.driver_context = ctx


class ContextualChildEntity(ContextualEntity):
    def __init__(self, name, driver_context):
        super(ContextualChildEntity, self).__init__(name, driver_context)

    @abstractmethod
    def parent_name(self):
        pass

    def is_child(self, parent_name):
        return self.parent_name() == parent_name


class ContextualStoredEntity(StoredEntity):
    def __init__(self, _store, driver_context=None):
        super(ContextualStoredEntity, self).__init__(_store)
        self.driver_context = driver_context

    def context(self):
        return self.driver_context

    def set_context(self, ctx):
        self.driver_context = ctx


class ContextualStoredChildEntity(StoredChildEntity):
    def __init__(self, _store, driver_context=None):
        super(ContextualStoredChildEntity, self).__init__(_store)
        self.driver_context = driver_context

    def context(self):
        return self.driver_context

    def set_context(self, ctx):
        self.driver_context = ctx

    @abstractmethod
    # still abstract (keep editors happy)
    def parent_name(self):
        pass


class EntityStore(object):
    def __init__(self, store):
        self._store = store
        self._prepare()

    def __repr__(self):
        # if self._store:
        #     return ', '.join(entity.__repr__() for entity in self._store)
        # else:
        return str(self.__class__.__name__)

    def _prepare(self):
        if self._store is not None:
            try:
                # configure explicitly that hash is integer
                # - dataset is not able to deduce it ...
                self._store.create_column(
                    Entity.HASH, dataset.types.Types.integer)

            except sqlalchemy.exc.OperationalError as e:
                raise DatabaseException(str(e))

    def all(self):
        try:
            if not self._store:
                return list()
            else:
                return self._store

        except sqlalchemy.exc.InternalError as e:
            raise DatabaseException(e.message)

    def insert(self, entity):
        if self._store is not None:
            self._store.insert(entity.store())

    def update(self, row):
        if self._store is not None:
            self._store.update(row, [Entity.HASH])

    def upsert(self, entity):
        try:
            if self._store is not None:
                self._store.upsert(entity.store(), [Entity.HASH])
        except sqlalchemy.exc.InternalError as e:
            raise DatabaseFatalException(str(e))

    def delete(self, entity):
        cnt = self.count()
        if self._store:
            # keep key aligned with Entity.HASH
            self._store.delete(hash=entity.hash)

            del_cnt = cnt - self.count()
            if del_cnt == 1:
                info('[{}] {} deleted.', self, entity.name)
                return True
            elif del_cnt == 0:
                error('[{}] NO entity deleted!', self)
                return False
            else:
                error('[{}] {} entities deleted!', self, del_cnt)
                return True

        return False

    def find_one(self, name):
        if self._store:
            # keep key aligned with Entity.HASH
            entity = self._store.find_one(hash=Entity.gen_hash(name))
            # if this ever happens not being equal, the code to be updated
            assert_equals(name, entity.name, 'entity name')
            return entity
        else:
            return None

    def find(self, name):
        if self._store:
            # keep key aligned with Entity.HASH
            return self._store.find(hash=Entity.gen_hash(name))
        else:
            return list()

    def count(self):
        if self._store:
            return self._store.count()
        else:
            return 0

    def drop_all(self):
        if self._store:
            self._store.drop()


class MiniCloudEntityStore(EntityStore):

    persistency = None  # don't know yet

    def __init__(self, db, table):

        assert_not_none(db)

        trace('[{}] initialized with db:', self)
        trace('[{}] {}', '...', db)  # shorten class name

        db_conn = {'system': None, 'clouds': None, 'clusters': None}

        if MiniCloudEntityStore.persistency in (None, True):

            MiniCloudEntityStore.persistency = False

            if 'sql' in db:
                try:
                    db_conn = dataset.connect(db)

                    MiniCloudEntityStore.persistency = True

                except ImportError as e:
                    error(e.message)
                    output()
                    error('Can\'t import a critical module. Please install or')
                    error('give --memory option for in-memory db management.')
                    exit(1)

        super(MiniCloudEntityStore, self).__init__(db_conn[table])

        trace('[{}] initialized successfully.', self)

    @classmethod
    def has_persistency(cls):
        return MiniCloudEntityStore.persistency
