from minicloud.core.core_in import string_input
from minicloud.core.core_out import error

from entity_mgnt import EntityMgnt

__author__ = 'Kris Sterckx'


class ClusterMgnt(EntityMgnt):
    def __init__(self, minicloud_mgnt):
        super(ClusterMgnt, self).__init__(
            minicloud_mgnt.manager.cluster_manager)
        self.minicloud = minicloud_mgnt.manager
        self.minicloud_mgnt = minicloud_mgnt
        self.show_unnamed_cluster = False

    def show_unnamed_cluster(self):
        return self.minicloud.clusters_supported()

    def obtain_entity_to_add(self):
        from minicloud.model.cluster import Cluster

        name = string_input('Name', default='demo')
        if not Cluster.is_valid_name(name):
            error('This is a reserved name.')
            return None
        cloud_name = self.obtain_entity_name(
            manager=self.minicloud.cloud_manager)
        return Cluster(name, cloud_name) if cloud_name else None

    @staticmethod
    def force_deep_topology():
        return False  # never deep fetch unless cache is empty

    def get_instance_list(self, cluster, deep_topology):
        return self.minicloud.instance_manager.get_instances_by_cluster(
            cluster.name, deep_topology)

    def get_instance_mgnt(self):
        return self.minicloud_mgnt.instance_mgnt

    def topology(self, level, cluster, deep_topology,
                 root_indent, root_prefix, prefix,
                 show_empty_entities=False, optimize_list=False):
        is_hidden_cluster = cluster.is_unnamed() \
            if not self.show_unnamed_cluster else False
        s, n, built = self.build_topology(
            level + 1,  # it's decreasing a level (obtaining instances)
            is_hidden_cluster,
            deep_topology, None,
            root_indent, '' if is_hidden_cluster else root_prefix,
            '' if is_hidden_cluster else prefix,
            cluster, cluster is None or is_hidden_cluster, True,
            ClusterMgnt.get_instance_list,
            ClusterMgnt.get_instance_mgnt,
            show_empty_entities,
            optimize_list)
        # NOT SURE STILL NEEDED ?
        # if is_hidden_cluster and n == 0:
        #     built = False  # skip it
        return s, n, built
