from __future__ import print_function

import sys

__author__ = 'Kris Sterckx'


silent_mode = False


def set_silent_mode(flag=True):
    global silent_mode
    silent_mode = flag


def is_silent_mode(thru_silent_mode=False):
    global silent_mode
    return silent_mode and not thru_silent_mode


def pop_first(alist):
    if len(alist) > 0:
        return alist[0]
    else:
        return None


class Box:
    def __init__(self):
        pass


__m = Box()
__m.stack = list()
__m.info = False
__m.debug = False
__m.trace = False


def enable_info():
    __m.info = True
    set_silent_mode(False)


def enable_debug():
    __m.info = True
    __m.debug = True
    set_silent_mode(False)


def enable_trace():
    __m.info = True
    __m.debug = True
    __m.trace = True
    set_silent_mode(False)


def info_enabled():
    return __m.info


def debug_enabled():
    return __m.debug


def trace_enabled():
    return __m.trace


def _(text, close=False, thru_silent_mode=False):
    if is_silent_mode(thru_silent_mode):
        return

    if info_enabled():
        print('%sINFO: %s' % (' ' if debug_enabled() else '', text))
    else:
        __m.stack.append(text)  # push

        sys.stdout.write(text)
        sys.stdout.flush()

    if close:
        __(thru_silent_mode)


def __(closing_text=None, thru_silent_mode=False):
    if is_silent_mode(thru_silent_mode):
        return

    if closing_text:
        _(closing_text, thru_silent_mode)

    if not info_enabled():  # or any lower prio tracing
        text = __m.stack.pop()  # pop
        backspaces = '\b' * len(text)
        spaces = ' ' * len(text)

        sys.stdout.write(backspaces)
        sys.stdout.write(spaces)
        sys.stdout.write(backspaces)
        sys.stdout.flush()

    if closing_text:
        __(thru_silent_mode)
