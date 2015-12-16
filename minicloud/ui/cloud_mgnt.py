from minicloud.core.core_in import string_input, choice_input_list,\
    boolean_input, shell_variable
from minicloud.core.core_out import error

from entity_mgnt import EntityMgnt

__author__ = 'Kris Sterckx'


class CloudMgnt(EntityMgnt):
    def __init__(self, minicloud_mgnt):
        super(CloudMgnt, self).__init__(minicloud_mgnt.manager.cloud_manager)
        self.minicloud = minicloud_mgnt.manager
        self.minicloud_mgnt = minicloud_mgnt

    def obtain_entity_to_add(self):
        pass

    def add_entity(self, retry=False):
        from minicloud.model.cloud import Cloud, StubCloud
        # -- minicloud custom ones --
        def_os_deployment_name = shell_variable(
            'OS_DEPLOYMENT_NAME', 'DevStack')
        def_os_deployment_type = shell_variable(
            'OS_DEPLOYMENT_TYPE', 'OpenStack')
        def_os_deployment_version = shell_variable(
            'OS_DEPLOYMENT_VERSION', 'master')
        def_os_deployment_location = shell_variable(
            'OS_DEPLOYMENT_LOCATION', 'localhost')

        # -- standard openstack ones --
        def_os_auth_url = shell_variable(
            'OS_AUTH_URL', 'http://localhost/identity')
        def_project_name = shell_variable(
            'OS_PROJECT_NAME', shell_variable('OS_TENANT_NAME', 'admin'))
        def_username = shell_variable(
            'OS_USERNAME', 'admin')
        def_password = shell_variable(
            'OS_PASSWORD', 'admin')
        def_user_domain_id = shell_variable(
            'OS_USER_DOMAIN_ID', 'default')
        def_project_domain_id = shell_variable(
            'OS_PROJECT_DOMAIN_ID', 'default')

        if not self.minicloud_mgnt.interactive_mode:
            cloud = Cloud(def_os_deployment_name, def_os_deployment_type,
                          def_os_deployment_version,
                          def_os_deployment_location,
                          def_os_auth_url, def_project_name,
                          def_username, def_password,
                          def_user_domain_id, def_project_domain_id)

        elif boolean_input(
                'Do you want a REAL cloud to be added (Y), '
                'or a STUB for dev-test (n)'):
            cloud = Cloud(
                string_input('Name', default=def_os_deployment_name),
                string_input('Type', default=def_os_deployment_type),
                string_input('Version', default=def_os_deployment_version),
                string_input('Location', default=def_os_deployment_location),
                string_input('Path', default=def_os_auth_url),
                string_input('Tenant', default=def_project_name),
                string_input('Username', default=def_username),
                string_input('Password', default=def_password),
                string_input('User Domain Id', default=def_user_domain_id),
                string_input('Project Domain Id',
                             default=def_project_domain_id))
        else:
            cloud = StubCloud()

        # authenticate
        if not cloud.authenticate():
            error('This cloud could not be authenticated.')
            return None

        return self.manager.add(cloud)

    def update_supported(self):
        return True  # Override the default False

    def obtain_update_data(self, entity):
        options_list = ['Location \t({})' % entity.location,  # 1
                        'Path \t({})' % entity.path,  # 2
                        'Tenant \t({})' % entity.tenant,  # 3
                        'Username \t({})' % entity.username,  # 4
                        'Password \t({})' % entity.password  # 5
                        ]
        field = choice_input_list('What would you like to update',
                                  options_list,
                                  add_none=True, default_last=True)
        data = None
        if field < 6:
            if field == 1:
                data = dict(
                    name=entity.name, location=string_input('New location'))
            elif field == 2:
                data = dict(
                    name=entity.name, path=string_input('New path'))
            elif field == 3:
                data = dict(
                    name=entity.name, tenant=string_input('New tenant'))
            elif field == 4:
                data = dict(
                    name=entity.name, username=string_input('New username'))
            elif field == 5:
                data = dict(
                    name=entity.name, password=string_input('New password'))
        return data

    @staticmethod
    def force_deep_topology():
        return False  # never deep fetch unless cache is empty

    def get_cluster_list(self, cloud, deep_topology):
        clusters = self.minicloud.cluster_manager.list()
        cl = []
        for c in clusters:
            if c.cloud_name == cloud.name:
                cl.append(c)
        return cl

    def get_cluster_mgnt(self):
        return self.minicloud_mgnt.cluster_mgnt

    def topology(self, level, cloud, deep_topology,
                 root_indent, root_prefix, prefix,
                 show_empty_entities=False, optimize_list=False):
        if cloud.authenticated():
            return self.build_topology(
                level, False,
                deep_topology, None,
                root_indent, root_prefix, prefix,
                cloud, cloud is None, True,
                CloudMgnt.get_cluster_list,
                CloudMgnt.get_cluster_mgnt,
                show_empty_entities)
        else:
            return (root_indent + root_prefix + cloud.repr() +
                    ': UNAUTHENTICATED\n'), 0, False
