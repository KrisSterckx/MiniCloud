from entity import ContextualEntity

__author__ = 'Kris Sterckx'


class SecurityGroup(ContextualEntity):
    def __init__(self, name, description=None, cloud=None, cloud_sg=None,
                 driver_context=None):
        super(SecurityGroup, self).__init__(name, driver_context)
        self.description = description
        self.cloud = cloud
        self.cloud_sg = cloud_sg
        self.sg_rules = []

    def add_rule(self, sg_rule):
        sg_rule.sg = self
        self.sg_rules.append(sg_rule)
