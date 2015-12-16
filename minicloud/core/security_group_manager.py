from cloud_resource_manager import CloudResourceManager
from core_out import debug

__author__ = 'Kris Sterckx'


class SecurityGroupManager(CloudResourceManager):
    def __init__(self, minicloud):
        super(SecurityGroupManager, self).__init__(minicloud)
        debug("[{}] initialized.", self)

    @staticmethod
    def entity_name():
        return 'security_group'

    def entity_title(self):
        return 'Security Group'

    def entity(self, cloud, ctx, cloud_sg):
        return ctx.new_sg(cloud_sg, cloud)

    def get_entities(self, ctx, name=None, deep_list=False):
        return ctx.security_groups(name)

    def create_entity(self, ctx, sg):
        sg.cloud_sg = ctx.create_security_group(sg)
        for sg_rule in sg.sg_rules:
            ctx.create_security_group_rule(sg.cloud_sg, sg_rule)
        return sg

    def delete_entity(self, ctx, sg):
        ctx.delete_security_group(sg)
        return True

    # override
    @staticmethod
    def sort_list(sgs):
        _list = list()
        _list.extend([sg for sg in sgs if 'public_ssh' in sg.name.lower()])
        _list.extend([sg for sg in sgs if 'public_ssh' not in sg.name.lower()])
        return _list

    def create_ssh_sg_group(self, cloud):
        from minicloud.model.security_group import SecurityGroup
        from minicloud.model.security_group_rule import SecurityGroupRule

        sg = SecurityGroup('public_ssh', 'sg for ssh access', cloud)
        sg.add_rule(SecurityGroupRule('tcp', 22, 22, 'ingress',
                                      '0.0.0.0/0'))
        return self.add(sg)
