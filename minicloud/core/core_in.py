from __future__ import print_function

import sys
import os
import copy

from core_out import output, output_no_newline

__author__ = 'Kris Sterckx'


def string_input(value_name, termination=' :', default=None,
                 allow_empty=False):
    while True:
        if default:
            output_no_newline('{}{} [{}] ', value_name, termination, default,
                              thru_silent_mode=True)
        else:
            output_no_newline('{}{} ', value_name, termination,
                              thru_silent_mode=True)
        value = sys.stdin.readline().strip()
        if default and not value:
            value = default
        output_no_newline('\r', thru_silent_mode=True)
        # empty check
        if allow_empty or value:
            break
        else:
            output('Empty is now allowed.', thru_silent_mode=True)

    return value


def numerical_input(value_name, min_value, max_value, default=True,
                    default_value=None):
    if default:
        def_value = min_value if not default_value else default_value
    else:
        def_value = None

    while True:
        try:
            value = int(string_input(value_name, default=def_value))
            if min_value <= value <= max_value:
                break
        except (ValueError, NameError):
            pass
        output('Please pick a number between {} and {}', min_value, max_value,
               thru_silent_mode=True)
    return value


def shell_variable(value_name, default=None):
    shell_value = os.environ.get(value_name)
    if shell_value:
        return shell_value
    else:
        return default


def shell_input(value_name, shell_var, default=None):
    value = os.environ.get(shell_var)
    if value:
        return value
    else:
        return string_input(value_name + ' (' + shell_var + ' is undefined)',
                            default=default)


def boolean_input(question, default=True):
    resp = string_input(question, '? (Y/n)' if default else '? (y/N)',
                        allow_empty=True).lower()
    if not resp:
        return default
    else:
        return 'y' in resp


def boolean_error(question, default=True):
    return boolean_input('ERROR: ' + question, default)


def choice_input_list(header=None, choices=None, add_none=False,
                      zero_based_display=False,
                      zero_based_return=False,
                      default=True, default_last=False, skip_line=True):
    input_list = choices
    if not input_list:
        return None

    display_offset = 0 if zero_based_display else 1
    return_offset = 0 if zero_based_display and zero_based_return \
        else 0 if not zero_based_display and not zero_based_return \
        else -1 if not zero_based_display and zero_based_return \
        else 1

    if add_none:
        input_list = copy.deepcopy(choices)
        input_list.append('None of the above.')

    if skip_line:
        output(thru_silent_mode=True)
    if header:
        output('[ {} ]', header, thru_silent_mode=True)
    for count, choice in enumerate(input_list):
        output('[{}] : {}', count + display_offset, choice,
               thru_silent_mode=True)

    min = display_offset
    max = len(input_list) - 1 + display_offset

    return numerical_input(
        'Make a choice', min, max, default,
        max if default and default_last else None) + return_offset


def choice_input(*args):
    return choice_input_list(args)
