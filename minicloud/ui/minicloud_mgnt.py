from minicloud.core.core_types import DatabaseException,\
    DatabaseFatalException, DatabaseCredentials, IntegrityException
from minicloud.core.core_in import boolean_input, choice_input_list,\
    shell_input

from minicloud.core.core_out import end, echo, error, info, info_n, output,\
    output_n, trace
from minicloud.core.core_utils import _, __

from entity_mgnt import EntityMgnt
from cloud_mgnt import CloudMgnt
from cluster_mgnt import ClusterMgnt
from router_mgnt import RouterMgnt
from network_mgnt import NetworkMgnt
from instance_mgnt import InstanceMgnt

__author__ = 'Kris Sterckx'


class MiniCloudMgnt(EntityMgnt):

    def __init__(self, interactive_mode=True, skip_header=False,
                 in_memory_db=False, cluster_support=False):

        if not skip_header:
            output_n('Welcome to MiniCloud!')

        self.interactive_mode = interactive_mode
        self.love_gimmicks = False

        if in_memory_db:
            output('** You are running MiniCloud with in-memory database '
                   'management.')
            output('** That means all volatile content will be lost after '
                   'executing the program.\n')

        super(MiniCloudMgnt, self).__init__(
            self.setup_minicloud(in_memory_db, cluster_support))
        self.cloud_mgnt = CloudMgnt(self)
        self.cluster_mgnt = ClusterMgnt(self)
        self.router_mgnt = RouterMgnt(self)
        self.network_mgnt = NetworkMgnt(self)
        self.instance_mgnt = InstanceMgnt(self)
        self.first_topology = True

    def in_interactive_mode(self):
        return self.interactive_mode

    def in_batch_mode(self):
        return not self.interactive_mode

    def obtain_choices(self):
        if self.manager.cluster_support:
            class Choices:
                def __init__(self):
                    pass

                CLOUD_TOPOLOGY = 1
                CLOUD_MGNT = 2
                CLUSTER_MGNT = 3
                ROUTER_MGNT = 4
                NETWORK_MGNT = 5
                INSTANCE_MGNT = 6
                DESTROY_ALL = 7

                options_list = ['Cloud topology',
                                'Cloud management',
                                'Cluster management',
                                'Router management',
                                'Network management',
                                'Instance management',
                                'Clear/Wipe cloud',
                                'Exit (keep data)']
            return Choices()
        else:
            class Choices:
                def __init__(self):
                    pass

                CLOUD_TOPOLOGY = 1
                CLOUD_MGNT = 2
                ROUTER_MGNT = 3
                NETWORK_MGNT = 4
                INSTANCE_MGNT = 5
                DESTROY_ALL = 6

                options_list = ['Cloud topology',
                                'Cloud management',
                                'Router management',
                                'Network management',
                                'Instance management',
                                'Clear/Wipe cloud',
                                'Exit (keep data)']
            return Choices()

    def manage_entities(self):
        while True:
            choices = self.obtain_choices()
            choice = choice_input_list('MiniCloud', choices.options_list)

            if choice == choices.CLOUD_TOPOLOGY:
                self.topologize()
            elif choice == choices.CLOUD_MGNT:
                self.cloud_mgnt.manage_entities()
            elif self.manager.cluster_support and \
                    choice == choices.CLUSTER_MGNT:
                self.cluster_mgnt.manage_entities()
            elif choice == choices.ROUTER_MGNT:
                self.router_mgnt.manage_entities()
            elif choice == choices.NETWORK_MGNT:
                self.network_mgnt.manage_entities()
            elif choice == choices.INSTANCE_MGNT:
                self.instance_mgnt.manage_entities()
            elif choice == choices.DESTROY_ALL:
                self.clear()
            else:
                end()

    @staticmethod
    def obtain_db_credentials(db_host, db_username, db_password, db_name):
        return DatabaseCredentials(
            shell_input('Database host', db_host, default='localhost'),
            shell_input('Database username', db_username, default='minicloud'),
            shell_input('Database password', db_password, default='password'),
            shell_input('Database name', db_name, default='minicloud'))

    def setup_minicloud(self, in_memory_db=False, cluster_support=False):
        from minicloud.core.mini_cloud import MiniCloud
        database = None
        info_n('[MiniCloud] Setting up MiniCloud ...')

        if not in_memory_db:
            database = MiniCloudMgnt.obtain_db_credentials(
                'MINICLOUD_DB_HOST', 'MINICLOUD_DB_USERNAME',
                'MINICLOUD_DB_PASSWORD', 'MINICLOUD_DB_NAME')

        try:
            mc = MiniCloud(database, cluster_support)

            if self.love_gimmicks:
                import datetime
                if mc.system.get_setting('first_use') is None:
                    mc.system.set_setting(
                        'first_use',
                        datetime.datetime.now().strftime('%d-%m-%Y'))
                    info('[MiniCloud] This is the first use of MiniCloud!')
                else:
                    info('[MiniCloud] The first use of MiniCloud was {}!',
                         mc.system.get_setting('first_use'))

            return mc

        except DatabaseException as e:
            fatal = isinstance(e, DatabaseFatalException)

            output()
            connection_exception = "[Errno 111] Connection refused"
            if connection_exception in str(e):
                error('Failed to connect to database: {}',
                      connection_exception)
            else:
                error('Received a database exception:\n{}', str(e))

            if not fatal:
                output()
                output('Please make sure you have a sql server running, '
                       'a MiniCloud db is provisioned')
                output('and user access is set up. '
                       'See the supplied DB_SETUP.sh script.')
                output()
                output('Alternatively you may want to run MiniCloud with '
                       '--memory option for in-memory')
                output('database management.')

            exit(1)

    def obtain_entity_to_add(self):
        pass

    def get_topology(self, indent=''):
        deep_topology = False
        show_empty_compute_entities = False
        show_empty_network_entities = True

        if self.in_interactive_mode() and not boolean_input(
                'Default topology parameters' + (' (DEEP fetch)'
                                                 if deep_topology else '')):
            deep_topology = self.force_deep_topology()
            show_empty_compute_entities = boolean_input(
                'Show empty compute entities', show_empty_compute_entities)
            show_empty_network_entities = boolean_input(
                'Show empty network entities', show_empty_network_entities)

        self.first_topology = False

        cloud = self.manager.get_cloud()
        if not cloud:
            output('You have no clouds. Please configure a cloud first.',
                   thru_silent_mode=True)
            return '', 0, False

        info_n('[MiniCloud] building topology for {}', cloud.name)
        return self.build_topology(
            0, False, deep_topology, cloud.name, indent, '', '',
            show_empty_compute_entities=show_empty_compute_entities,
            show_empty_network_entities=show_empty_network_entities)

    def topology(self, level, entity, deep_topology,
                 root_indent, root_prefix, prefix,
                 show_empty_entities=False, optimize_list=False):
        pass

    def build_topology(self, level, hidden_level, deep_topology, root,
                       root_indent, root_prefix, prefix,
                       entity=None, skip_head=False, skip_prebuild=False,
                       list_entities=None, entity_mgnt=None,
                       show_empty_compute_entities=True,
                       show_empty_network_entities=True,
                       use_cached_list_for_entities=False):
        _('Building topology...', thru_silent_mode=True)

        trace('[{}] --- build_topology ({}) ---', self,
              entity.name if entity else '')
        s = ''
        root_prefix = root_indent + root_prefix  # do not change order
        prefix = root_indent + prefix  # do not change order
        head = root_prefix + root + '\n'
        head_next = root_prefix + '|\n'
        sn, nc, built = self.router_mgnt.build_topology(
            level + 1, False,
            deep_topology, 'Networking', prefix, '+---', '    ',
            show_empty_entities=show_empty_network_entities)
        trace('[{} mgnt] build_topology: nc={}.', self.entity_title(), nc)

        cline = '|' if nc else ' '
        sc, cc, built = self.cloud_mgnt.build_topology(
            level + 1, False,
            deep_topology, 'Compute', prefix, '+---', cline + '   ',
            show_empty_entities=show_empty_compute_entities)
        trace('[{} mgnt] build_topology: cc={}.', self.entity_title(), cc)

        if cc:
            s = head + head_next + sc
            if nc:
                s += prefix + '|\n' + sn
        elif nc:
            s = head + head_next + sn

        trace('[{}] --- build_topology end ---', self)
        __(thru_silent_mode=True)

        return s, cc + nc, True

    # no longer in use, but as such the method is a valid op
    def reset(self):
        echo('Reset\'ing.')
        self.manager.reset()
        self.first_topology = True
        echo('Done.')

    def add_cloud(self):
        self.cloud_mgnt.add()

    def show_cloud(self):
        clouds = self.cloud_mgnt.manager.list()
        if clouds:
            for cloud in clouds:
                echo('\n--- cloud ---')
                echo(self.cloud_mgnt.manager.get(cloud.name).deep_repr())
        else:
            echo('There is no cloud. Abort.')

    def clear(self, cloud=None):
        if cloud:
            raise NotImplementedError  # can't clear one particular cloud

        elif not self.cloud_mgnt.manager.list():
            echo('There is no cloud. Abort.')

        elif (boolean_input(
            '** CAUTION ** : This operation is a irreversible WIPE ALL!\n'
            'Are you POSITIVE you want to clear the entire cloud',
                False) and boolean_input(
                'You are ABSOLUTELY positive (all entities will be DESTROYED)',
                False) and boolean_input(
                'Please CONFIRM one more time (you KNOW what you\'re doing?)',
                False)):
            echo('Wiping your cloud...')
            self.manager.clear()
            echo('All entities are destroyed and all data cleared.')

        else:
            echo('Aborted.')

    def remove_cloud(self):
        if self.in_interactive_mode():
            self.cloud_mgnt.remove()
        else:
            try:
                cloud = self.manager.get_cloud()
                if cloud:
                    cloud = self.cloud_mgnt.manager.get(cloud.name)
                    if self.cloud_mgnt.remove_entity(cloud):
                        echo('Cloud removed.')
                else:
                    echo('There is no cloud. Abort.')

            except IntegrityException as e:
                output(str(e))
