from abc import ABCMeta, abstractmethod

from minicloud.core.core_in import string_input, choice_input_list,\
    boolean_input
from minicloud.core.core_out import echo, echo_no_newline, error, new_line,\
    output, trace
from minicloud.core.core_utils import trace_enabled
from minicloud.core.core_types import IntegrityException, InUseException, \
    DoesNotExistException, MiniCloudException

__author__ = 'Kris Sterckx'


class EntityMgnt(object):
    __metaclass__ = ABCMeta

    def __init__(self, manager):
        self.manager = manager
        self.entity_name = manager.entity_name()

    def entity_title(self):
        return self.entity_name.title()

    def entities_title(self):
        return self.entity_title() + 's'

    def __repr__(self):
        return self.entity_title() + ' mgnt'

    def manage_entities(self):
        choices = self.obtain_choices()
        while True:
            choice = choice_input_list(self.entities_title(),
                                       choices.options_list)

            if choice == choices.TOPOLOGY:
                self.topologize()
            elif choice == choices.LIST:
                self.list()
            elif choice == choices.ADD:
                self.add()
            elif self.update_supported() and choice == choices.UPDATE:
                self.update()
            elif choice == choices.REMOVE:
                self.remove()
            else:
                if not self.extra_entity_management(choice):
                    break
        pass

    def obtain_choices(self):
        if self.update_supported():

            class Choices:
                def __init__(self):
                    pass

                TOPOLOGY = 1
                LIST = 2
                ADD = 3
                UPDATE = 4
                REMOVE = 5

                options_list = ['%s topology' % self.entity_name.title(),
                                'List %ss' % self.entity_name,
                                'Add %s' % self.entity_name,
                                'Update %s' % self.entity_name,
                                'Remove %s' % self.entity_name,
                                'Exit']
            return Choices

        else:
            class Choices:
                def __init__(self):
                    pass

                TOPOLOGY = 1
                LIST = 2
                ADD = 3
                REMOVE = 4

                options_list = ['%s topology' % self.entity_name.title(),
                                'List %ss' % self.entity_name,
                                'Add %s' % self.entity_name,
                                'Remove %s' % self.entity_name,
                                'Exit']
            return Choices()

    # extra added by child classes
    def extra_entity_management(self, choice):
        return False  # break

    def list(self, deep_list=False):
        try:
            all_e = self.manager.list(deep_list)
            if not all_e:
                echo('You currently have no {}s provisioned.',
                     self.entity_name)
            else:
                echo('You currently have {} {}{} provisioned:',
                     len(all_e), self.entity_name,
                     's' if len(all_e) > 1 else '')
                for e in all_e:
                    echo(e.repr())
        except MiniCloudException:
            error('List failed.')

    @abstractmethod
    def obtain_entity_to_add(self):
        return None  # to be implemented by derived classes

    def obtain_update_data(self, entity):
        return None  # to be implemented by derived classes if supported

    @abstractmethod
    def topology(self, level, entity, deep_topology,
                 root_indent, root_prefix, prefix,
                 show_empty_entities=False, optimize_list=False):
        return '', 0, False

    def add(self):
        output()
        output('Please enter the data of the {} you would like to add.',
               self.entity_name)
        try:
            if self.add_entity():
                echo('{} added.', self.entity_name.title())
            else:
                echo('No {} added.', self.entity_name)

        except MiniCloudException:
            error('Adding the {} failed.', self.entity_name)

    def add_entity(self, retry=False):
        entity = self.obtain_entity_to_add()
        if entity:
            try:
                return self.manager.add(entity)

            except IntegrityException:
                error('You can\'t add this {} as it breaks data integrity.',
                      self.entity_name)
                if retry and boolean_input('Would you like to re-enter'):
                    return self.add_entity()
        else:
            return None

    def update_supported(self):
        return False  # NOT supported by default; Need to set explicitly True.

    def update(self):
        if not self.update_supported():
            output('Not supported, sorry.')
            return

        # else
        output()
        output('Please enter the name of the {} you would like to update.',
               self.entity_name)
        try:
            if self.update_entity():
                echo('{} updated.', self.entity_name.title())
            else:
                echo('No {} updated.', self.entity_name)
        except DoesNotExistException:
            echo('No {} updated.', self.entity_name)
        except IntegrityException:
            error('You can\'t update this {} as it breaks data integrity.',
                  self.entity_name)
        except MiniCloudException:
            error('Updating the {} failed.', self.entity_name)

    def update_entity(self):
        entity = self.obtain_entity()
        if entity:
            data = self.obtain_update_data(entity)
            if data:
                return self.manager.update(entity, data)
        return False

    def remove(self):
        output()
        output('Please enter the name of the {} you would like to remove.',
               self.entity_name)
        try:
            if self.remove_entity():
                echo('{} removed.', self.entity_name.title())
            else:
                echo('No {} removed.', self.entity_name)
        except DoesNotExistException:
            echo('No {} removed.', self.entity_name)
        except IntegrityException:
            error('You can\'t remove this {} as it breaks data integrity.',
                  self.entity_name)
        except InUseException:
            error('You can\'t remove this {} as it is in use.',
                  self.entity_name)
        except MiniCloudException:
            error('Removing the {} failed.', self.entity_name)

    def remove_entity(self, entity=None):
        if not entity:
            entity = self.obtain_entity(filter_f=self.manager.remove_eligible)
        if entity:
            return (self.check_for_remove(entity) and
                    self.manager.deep_remove(entity))
        else:
            error('This entity does not exist')
            return False

    def check_for_remove(self, entity):
        nbr_children = self.manager.has_children(entity.name)
        if nbr_children > 0:
            return boolean_input(
                'Entity ' + entity.name + ' has data contained '
                '(counting ' + str(nbr_children) + ' dependencies).\n'
                'Still delete all data in cascade'
                ' (without destroying the cloud)', default=False)
        else:
            return True

    @staticmethod
    def force_deep_topology():
        return boolean_input('Force deep fetch', False)

    @staticmethod
    def show_empty_entities():
        return boolean_input('Show empty entities', False)

    def deep_list(self):
        return self.list(True)

    def get_topology(self, indent=''):
        return self.build_topology(
            0, False,
            self.force_deep_topology(),
            self.entities_title(), indent, '', '',
            show_empty_entities=self.show_empty_entities())

    def topologize(self):
        s, n, topo_built = self.get_topology(6 * ' ')

        new_line(thru_silent_mode=True)
        if topo_built and n:
            echo_no_newline(s)
        else:
            echo('There is no topology to show.')

    def prebuild_topology(self, level, deep_topology, root_intent, prefix,
                          show_empty_entities):
        return '', 0, False

    def get_entity_mgnt(self):
        return self

    def get_entity_manager(self):
        return self.get_entity_mgnt().manager

    # === don't override ===
    def _get_entity_mgnt(self):
        return self.get_entity_mgnt()

    def _get_entity_list(self, entity, deep_topology):
        return self.get_entity_manager().list(deep_topology)
    # === don't override, end ===

    @staticmethod
    def topology_add_title():
        return True  # could be overruled

    def build_topology(self, level, hidden_level, deep_topology, root,
                       root_indent, root_prefix, prefix,
                       entity=None, skip_head=False, skip_prebuild=False,
                       list_entities=_get_entity_list,
                       entity_mgnt=_get_entity_mgnt,
                       show_empty_entities=True,
                       use_cached_list_for_entities=False):

        trace('[{}] --- build_topology ({}) ---', self,
              entity.name if entity else '')
        head, s, cnt, built = '', '', 0, False

        if not skip_head:
            head = entity.repr() if entity \
                else root if root else self.entities_title()
            head = root_indent + root_prefix + head + '\n'

        fetch_optimized = False
        if skip_prebuild:
            trace('[{}] build_topology: skipped prebuild.', self)
        else:
            s, cnt, prebuilt = self.prebuild_topology(
                level, deep_topology, root_indent, prefix, show_empty_entities)
            fetch_optimized = prebuilt  # optimize when topo is prebuilt
            trace('[{}] build_topology: {}.', self,
                  ('prebuilt to ' + s) if prebuilt else 'prebuilt was void')
            if trace_enabled() and prebuilt:
                s += ' [level {}] (built is True as ' \
                     'prebuilt is True)\n'.format(level)
            built |= prebuilt

        if use_cached_list_for_entities:
            trace('[{}] build_topology: building list, optimized.', self)
            entities_list = list_entities(self, entity, False)
        else:
            trace('[{}] build_topology: building list '
                  '(deep_topology={}).', self, deep_topology)
            entities_list = list_entities(self, entity, deep_topology)

        trace('[{}] {} entities iterated at.', self, len(entities_list))

        it = 0
        for e in reversed(entities_list):
            it += 1
            if trace_enabled():
                s += ' [level {}] (iteration {} for entity {})'.format(
                    level, it, str(e))
            trace('[{}] build_topology: iteration for <{}>.', self, e)
            s2, n, topo_built = entity_mgnt(self).topology(
                level + 1,
                e, deep_topology,
                root_indent + prefix, '+---', '|   ' if cnt else '    ',
                show_empty_entities, fetch_optimized)

            trace('[{}] build_topology: iteration for <{}> returned: {}, {}',
                  self, e, n, topo_built)
            built |= topo_built
            if trace_enabled() and topo_built:
                s += ' (built is True as topo_built is True)\n'
            if show_empty_entities or n > 0:
                if topo_built and not hidden_level:
                    reason = ('\n [level {}]'
                              ' (iteration {} for entity {},'
                              ' added as {})'.format(
                                  level, it, str(e),
                                  ('n=' + str(n) if n > 0
                                   else 'show_empty_entities'
                                   if show_empty_entities
                                   else '?')) if trace_enabled() else '')
                    s = root_indent + prefix + '|' + reason + '\n' + s2 + s
                else:
                    if hidden_level:
                        reason = ' [level {}] (hidden level)\n'.format(
                            level - 1)
                    else:
                        reason = (' [level {}] (newline skipped as'
                                  ' no/empty topo built'
                                  ' for {})\n'.format(level, str(e)))
                    s = (reason if trace_enabled() else '') + s2 + s

            if n > 0 or show_empty_entities or topo_built:
                cnt += 1
            fetch_optimized = True  # next iteration, do smarter

        if built or show_empty_entities or cnt:
            s = head + s
        else:
            trace('[{}] head is lost [{}] ({})', self, head,
                  'built is False' if not built
                  else 'show_empty_ent and cnt both are false/0')

        trace('[{}] --- build_topology end ({}, {}) ---',
              self, cnt, built)
        return s, cnt, built or show_empty_entities

    def obtain_entity_name(self, input_string=None, choices=None,
                           filter_f=None, manager=None,
                           choose_from_display=False, allow_none=False,
                           skip_questioning_if_only_one_entity=False,
                           return_immediately_if_no_entity=False,
                           allow_non_existing_name=False,
                           entities=None):
        if not manager:
            manager = self.manager
        if choices:
            names = choices
            choose_from_display = True
        else:
            names = manager.list_entity_names(filter_f, entities)
        if return_immediately_if_no_entity and not names:
            return None
        if skip_questioning_if_only_one_entity and names and len(names) == 1:
            return names[0]
        if not input_string:
            input_string = manager.entity_title() + ' name'
        if choose_from_display:
            if allow_non_existing_name:
                error('[obtain_entity_name] Function is illegally called')
                return None
            output()  # skip line first, is nicer

        if names and choose_from_display:
            name_idx = choice_input_list(
                input_string, names, add_none=allow_none,
                zero_based_return=True, skip_line=False)
            if name_idx == len(names):
                return None
            else:
                return names[name_idx]

        else:
            if names:
                if len(names) == 1:
                    def_name = names[0]
                else:
                    def_name = 'show'
            else:
                def_name = 'none'

            while True:
                name = string_input(input_string, default=def_name)
                if name == 'show':
                    if len(name) > 0:
                        for n in names:
                            output(n)
                        output('or give \'none\' to return.')
                    else:
                        output('Nothing to show.')
                elif name == 'none':
                    return None
                else:
                    if name in names:
                        break
                    else:
                        if allow_non_existing_name:
                            return name
                        else:
                            output('{} is not a valid {}, pls re-enter '
                                   'or give \'none\'.',
                                   name, manager.entity_name())
        return name

    def obtain_entity(self, input_string=None, filter_f=None,
                      manager=None, choose_from_display=False,
                      allow_none=False,
                      skip_questioning_if_only_one_entity=False,
                      return_immediately_if_no_entity=False,
                      entities=None):
        if not manager:
            manager = self.manager
        name = self.obtain_entity_name(input_string, None,
                                       filter_f, manager,
                                       choose_from_display, allow_none,
                                       skip_questioning_if_only_one_entity,
                                       return_immediately_if_no_entity,
                                       False,
                                       entities)
        return manager.get(name) if name else None

    @staticmethod
    def dictionarize(entities):
        entity_dict = {}
        for entity in entities:
            entity_dict[entity.name] = entity
        return entity_dict
