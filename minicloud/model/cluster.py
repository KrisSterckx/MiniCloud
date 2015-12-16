from entity import ContextualStoredChildEntity

__author__ = 'Kris Sterckx'


class Cluster(ContextualStoredChildEntity):
    __UNNAMED_CLUSTER__ = 'UNNAMED'

    def __init__(self, name=None, cloud_name=None, _dict=None):
        super(Cluster, self).__init__(
            dict(name=name, cloud_name=cloud_name) if not _dict else _dict)
        self.cloud = None

    @property
    def cloud_name(self):
        return self.get('cloud_name')

    def parent_name(self):
        return self.cloud_name

    @staticmethod
    def unnamed_cluster_name(cloud_name):
        return cloud_name + '.' + Cluster.__UNNAMED_CLUSTER__

    @staticmethod
    def is_unnamed_name(name):
        return Cluster.__UNNAMED_CLUSTER__ in name

    @staticmethod
    def is_valid_name(name):
        return not Cluster.is_unnamed_name(name)

    def is_unnamed(self):
        return Cluster.is_unnamed_name(self.name)
