"""
Abstract base class for things that need building.

These classes should be listed as the entry point [fassembler.project]
"""
import os
import sys
import socket
from cStringIO import StringIO
from fassembler.namespace import Namespace
from fassembler.text import indent, underline, dedent

class Project(object):
    """
    This represents an abstract project.

    Subclasses should describe the project built in the docstring.

    Subclasses should also define an actions attribute, which is a list
    of tasks.
    """

    name = None
    title = None
    actions = None
    settings = []

    def __init__(self, project_name, maker, logger, config):
        self.project_name = project_name
        self.maker = maker
        self.logger = logger
        self.config = config
        if self.name is None:
            raise NotImplementedError(
                "No name has been assigned to %r" % self)
        self.build_properties = {}

    @property
    def config_section(self):
        return self.name

    def confirm_settings(self):
        try:
            self.setup_config()
        except ValueError, e:
            ## FIXME: better API
            ## FIXME: find all errors
            raise

    def run(self):
        if self.actions is None:
            raise NotImplementedError(
                "The actions attribute has not been overridden in %r"
                % self)
        self.setup_config()
        self.bind_tasks()
        for task in self.actions:
            self.logger.set_section(self.name+'.'+task.name)
            self.logger.notify('== %s ==' % task.name, color='bold green')
            self.logger.indent += 2
            try:
                try:
                    task.run()
                finally:
                    self.logger.indent -= 2
            except:
                should_continue = self.maker.handle_exception(sys.exc_info(), can_continue=True)
                if not should_continue:
                    self.logger.fatal('Project %s aborted.' % self.title, color='red')
                    return

    def bind_tasks(self):
        for task in self.actions:
            task.bind(maker=self.maker, logger=self.logger, config=self.config,
                      project=self)
            task.confirm_settings()

    def make_description(self):
        """
        Returns the description of this project, in the context of the
        settings given.
        """
        self.setup_config()
        self.bind_tasks()
        out = StringIO()
        title = self.title or self.name
        title = '%s (%s)' % (title, self.project_name)
        print >> out, underline(title)
        doc = self.__doc__
        if doc == Project.__doc__:
            doc = '[No project description set]'
        print >> out, dedent(doc)
        print >> out
        print >> out, indent(underline('Settings', '='), '  ')
        if not self.settings:
            print >> out, indent('No settings', '    ')
        else:
            for setting in self.settings:
                print >> out, indent(str(setting), '    ')
        print >> out
        print >> out, indent(underline('Tasks', '='), '  ')
        for task in self.actions:
            desc = str(task)
            print >> out, indent(underline(task.title, '-'), '    ')
            print >> out, indent(desc, '    ')
            print >> out
        return out.getvalue()

    def create_namespace(self):
        ns = Namespace(self.config_section)
        ns['env'] = Environment(self.maker.base_path)
        ns['maker'] = self.maker
        ns['project'] = self
        ns['os'] = os
        ns.add_all_sections(self.config)
        ns['config'] = ns[self.config_section]
        return ns

    def setup_config(self):
        if not self.config.has_section(self.config_section):
            self.config.add_section(self.config_section)
        for setting in self.settings:
            if (not self.config.has_option(self.config_section, setting.name)
                and not self.config.has_option('DEFAULT', setting.name)):
                if not setting.has_default:
                    raise ValueError(
                        "The setting [%s] %s must be set" % (self.config_section, setting.name))
                self.config.set(self.config_section, setting.name, setting.default)

class Environment(object):

    def __init__(self, base_path):
        self.environ = os.environ
        self.base_path = base_path

    @property
    def hostname(self):
        return socket.gethostname().split('.')[0]

    @property
    def fq_hostname(self):
        return socket.gethostbyaddr(socket.gethostname())

class Setting(object):

    class _NoDefault(object):
        def __repr__(self):
            return '(no default)'
    NoDefault = _NoDefault()
    del _NoDefault

    def __init__(self, name, default=NoDefault, help=None):
        self.name = name
        self.default = default
        self.help = help

    @property
    def has_default(self):
        return self.default is not self.NoDefault

    def __str__(self):
        msg = '%s: (default: %r)' % (self.name, self.default)
        if self.help:
            msg += '\n' + indent(self.help, '  ')
        return msg
        
            
            
