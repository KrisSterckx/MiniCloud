from __future__ import print_function

import traceback
import sys

from core_utils import debug_enabled, info_enabled, trace_enabled, \
    is_silent_mode

__author__ = 'Kris Sterckx'


def output_no_newline(msg=None,
                      val1=None, val2=None, val3=None, val4=None, val5=None,
                      thru_silent_mode=False):
    output(msg, val1, val2, val3, val4, val5, '', thru_silent_mode)


def output(msg=None, val1=None, val2=None, val3=None, val4=None, val5=None,
           end=None, thru_silent_mode=False):
    if is_silent_mode(thru_silent_mode):
        pass
    elif msg is not None:
        if val1 is not None:
            if val2 is not None:
                if val3 is not None:
                    if val4 is not None:
                        if val5 is not None:
                            print(msg.format(val1, val2, val3, val4, val5),
                                  end=end)
                        else:
                            print(msg.format(val1, val2, val3, val4), end=end)
                    else:
                        print(msg.format(val1, val2, val3), end=end)
                else:
                    print(msg.format(val1, val2), end=end)
            else:
                print(msg.format(val1), end=end)
        else:
            print(msg, end=end)
    else:
        print(end=end)


def output_n(msg='', val1=None, val2=None, val3=None, val4=None, val5=None,
             end=None, thru_silent_mode=False):
    new_line(thru_silent_mode)
    output(msg, val1, val2, val3, val4, val5, end, thru_silent_mode)


def echo(msg='', val1=None, val2=None, val3=None, val4=None, val5=None,
         end=None):
    output(msg, val1, val2, val3, val4, val5, end, True)


def echo_no_newline(msg='', val1=None, val2=None, val3=None, val4=None,
                    val5=None):
    output(msg, val1, val2, val3, val4, val5, '', True)


def echo_n(msg='', val1=None, val2=None, val3=None, val4=None, val5=None,
           end=None):
    new_line(True)
    output(msg, val1, val2, val3, val4, val5, end, True)


def new_line(thru_silent_mode=False):
    if not is_silent_mode(thru_silent_mode):
        print()


def log(msg='', val1=None, val2=None, val3=None, val4=None, val5=None):
    output('  LOG: ' + msg if debug_enabled() else 'LOG: ' + msg,
           val1, val2, val3, val4, val5)


def log_n(msg='', val1=None, val2=None, val3=None, val4=None, val5=None):
    new_line()
    log(msg, val1, val2, val3, val4, val5)


def trace(msg='', val1=None, val2=None, val3=None, val4=None, val5=None):
    if trace_enabled():
        output('TRACE: ' + msg, val1, val2, val3, val4, val5)


def trace_n(msg='', val1=None, val2=None, val3=None, val4=None, val5=None):
    if trace_enabled():
        new_line()
        output('TRACE: ' + msg, val1, val2, val3, val4, val5)


def debug(msg='', val1=None, val2=None, val3=None, val4=None, val5=None):
    if debug_enabled():
        output('DEBUG: ' + msg, val1, val2, val3, val4, val5)


def debug_n(msg='', val1=None, val2=None, val3=None, val4=None, val5=None):
    if debug_enabled():
        new_line()
        debug(msg, val1, val2, val3, val4, val5)


def exc_debug(msg='', val1=None, val2=None, val3=None, val4=None, val5=None):
    if debug_enabled():
        debug_n(msg, val1, val2, val3, val4, val5)
        traceback.print_tb(sys.exc_info()[2])


def info(msg='', val1=None, val2=None, val3=None, val4=None, val5=None):
    if info_enabled():
        output(' INFO: ' + msg if debug_enabled() else 'INFO: ' + msg,
               val1, val2, val3, val4, val5)


def info_n(msg='', val1=None, val2=None, val3=None, val4=None, val5=None):
    if info_enabled():
        new_line()
        info(msg, val1, val2, val3, val4, val5)


def warn(msg='', val1=None, val2=None, val3=None, val4=None, val5=None):
    warn_indicator = ' WARN: ' if info_enabled() else 'WARN: '
    output(warn_indicator + msg if debug_enabled() else 'WARN: ' + msg,
           val1, val2, val3, val4, val5, thru_silent_mode=True)


def warn_n(msg='', val1=None, val2=None, val3=None, val4=None, val5=None):
    new_line()
    warn(msg, val1, val2, val3, val4, val5)


def error(msg='', val1=None, val2=None, val3=None, val4=None, val5=None,
          fatal=False, bug=False):
    output('ERROR: ' + msg, val1, val2, val3, val4, val5,
           thru_silent_mode=True)
    if fatal:
        fail(bug=bug)


def error_n(msg='', val1=None, val2=None, val3=None, val4=None, val5=None,
            fatal=False):
    new_line()
    error(msg, val1, val2, val3, val4, val5, fatal)


def exc_error(msg='', val1=None, val2=None, val3=None, val4=None, val5=None,
              fatal=False):
    if debug_enabled():
        error(msg, val1, val2, val3, val4, val5, fatal)
        traceback.print_tb(sys.exc_info()[2])

    else:
        error_n(msg, val1, val2, val3, val4, val5, fatal)


def assert_equals(expected, actual, expected_type_of_goods=None,
                  warn_only=False):
    return assert_or_fail(
        actual == expected,
        str(expected) + ((' ' + expected_type_of_goods)
                         if expected_type_of_goods
                         else '') +
        ' expected but got ' + str(actual), warn_only)


def assert_or_fail(assert_condition, msg=None, warn_only=False):
    if assert_condition:
        return True
    elif warn_only:
        warn(msg)
        return False
    else:
        fail(msg, True)


def assert_not_none(obj):
    return assert_or_fail(obj is not None)


def assert_true(assert_condition):
    return assert_or_fail(assert_condition)


def fail(msg=None, bug=False):
    if msg:
        error(msg)
    if bug:
        error('This is a bug and is embarrassing.')
        error('Please report to the author.')
    exit(1)


def end(exit_status=0):
    output()
    output('Thanks for using MiniCloud.')
    output('Have a nice day.')
    exit(exit_status)
