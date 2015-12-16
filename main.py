import argparse
import sys

from minicloud.core.core_utils import enable_debug, enable_info, enable_trace,\
    set_silent_mode

__author__ = 'Kris Sterckx'


class Main(object):

    program = './MiniCloud.sh'
    cmd = '''
In command execution mode, supported commands are:
   configure     Configure a cloud
   show          Show cloud configuration
   topology      Display cloud topology
   wipe          Wipe the entire cloud
   unconfigure   Unconfigure a cloud
'''
    usage = '''./MiniCloud.sh [flags] [--execute [-i] <cmd>]

By default, MiniCloud runs interactively.
''' + cmd
    cmd_usage = '''./MiniCloud.sh --execute [-i] <cmd>
''' + cmd

    def __init__(self):
        parser = argparse.ArgumentParser(prog=Main.program, usage=Main.usage)
        parser.add_argument("-i", "--info", help="(flag) run in info mode",
                            action="store_true")
        parser.add_argument("-d", "--debug", help="(flag) run in debug mode",
                            action="store_true")
        parser.add_argument("-t", "--trace", help="(flag) run in trace mode",
                            action="store_true")
        parser.add_argument('-e', '--execute',
                            help='execute command <cmd>',
                            action="store_true")
        args = parser.parse_args(sys.argv[1:2])

        self.interactive = True
        self.info = args.info
        self.debug = args.debug
        self.trace = args.trace
        self.cmd = ''

        if args.execute:
            self.execute()
        else:
            self.proceed()

        set_silent_mode(bool(self.cmd) and not self.interactive)

        if self.info:
            enable_info()
        if self.debug:
            enable_debug()
        if self.trace:
            enable_trace()

        if not self.cmd:
            self.mc().manage_entities()
        elif self.cmd == 'configure':
            self.mc().add_cloud()
        elif self.cmd == 'show':
            self.mc().show_cloud()
        elif self.cmd == 'topology':
            self.mc().topologize()
        elif self.cmd == 'wipe':
            self.mc().clear()
        elif self.cmd == 'unconfigure':
            self.mc().remove_cloud()
        else:
            print('ERROR: Don\'t know command: %s' % self.cmd)

    def proceed(self, idx=2):
        parser = argparse.ArgumentParser(prog=self.program,
                                         usage=self.usage)
        parser.add_argument('-e', '--execute', help='execute command (<cmd>)',
                            action="store_true")
        args = parser.parse_args(sys.argv[idx:idx+1])
        if args.execute:
            self.execute(idx+1)

    def execute(self, idx=2):
        parser = argparse.ArgumentParser(prog=self.program,
                                         usage=self.cmd_usage)
        parser.add_argument("-i", "--interactive",
                            help="(flag) run in interactive mode where it can",
                            action="store_true")
        parser.add_argument('command', help="command to execute")
        #                    no store_true here !
        args = parser.parse_args(sys.argv[idx:])
        self.cmd = args.command
        self.interactive = args.interactive

    def mc(self):
        from minicloud.ui.minicloud_mgnt import MiniCloudMgnt
        return MiniCloudMgnt(self.interactive, True)


Main()
