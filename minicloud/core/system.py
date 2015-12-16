from cached_entity_manager import CachedStoredEntityManager
from core_out import debug, trace

__author__ = 'Kris Sterckx'


class System(CachedStoredEntityManager):
    def __init__(self, minicloud):
        super(System, self).__init__(db=minicloud.db, table='system')
        debug("[{}] initialized.", self)

    @staticmethod
    def entity_name():
        return 'system'

    def set_setting_if_not_set(self, name, value):
        if self.get_setting(name) is None:
            self.set_setting(name, value)

    def set_setting(self, name, value):
        from minicloud.model.entity import NamedValue
        trace('[{}] set_setting ({}, {})', self, name, value)
        self.add(NamedValue(name=name, value=value), skip_check=True)

    def type_cast(self, entity):
        from minicloud.model.entity import NamedValue
        return NamedValue(_dict=entity) if entity else None

    def get_setting(self, name):
        trace('[{}] --- get_setting ({}) ---', self, name)
        setting = self.get(name)
        value = setting.value if setting else None
        trace('[{}] --- get_setting end ---', self)
        return value
