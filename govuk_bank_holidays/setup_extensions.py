import distutils.log
import os
import subprocess

import setuptools


class MessagesCommand(setuptools.Command):
    user_options = []

    def __init__(self, *args, **kwargs):
        setuptools.Command.__init__(self, *args, **kwargs)
        self.domain = 'messages'
        self.cwd = os.getcwd()
        self.root_path = os.path.join(os.path.dirname(__file__), os.pardir)
        self.app_path = 'govuk_bank_holidays'
        self.locale_path = os.path.join(self.app_path, 'locale')
        self.pot_name = '%s.pot' % self.domain
        self.po_name = '%s.po' % self.domain
        self.mo_name = '%s.mo' % self.domain
        self.pot_path = os.path.join(self.locale_path, self.pot_name)
        self.locales = [
            path
            for path in os.listdir(self.locale_path)
            if os.path.isfile(os.path.join(self.locale_path, path, 'LC_MESSAGES', self.po_name))
        ]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.chdir(self.root_path)
        self.run_command()
        os.chdir(self.cwd)

    def run_command(self):
        raise NotImplementedError


class MakeMessages(MessagesCommand):
    description = 'update localisation messages files'

    def find_source_files(self):
        return [os.path.join(self.app_path, 'i18n.py')]

    def run_command(self):
        self.announce('Writing intermediate POT file', level=distutils.log.INFO)
        xgettext = ['xgettext', '-d', self.domain, '-o', self.pot_path,
                    '--language=Python', '--from-code=UTF-8',  '--no-wrap']
        subprocess.check_call(xgettext + self.find_source_files())

        msgmerge = ['msgmerge', '--no-wrap', '--previous', '--update']
        for locale in self.locales:
            self.announce('Writing PO file for %s locale' % locale, level=distutils.log.INFO)
            po_path = os.path.join(self.locale_path, locale, 'LC_MESSAGES', self.po_name)
            subprocess.check_call(msgmerge + [po_path, self.pot_path])


class CompileMessages(MessagesCommand):
    description = 'compile localisation messages files'

    def run_command(self):
        msgfmt = ['msgfmt', '--check']
        for locale in self.locales:
            self.announce('Compiling PO file for %s locale' % locale, level=distutils.log.INFO)
            po_path = os.path.join(self.locale_path, locale, 'LC_MESSAGES', self.po_name)
            mo_path = os.path.join(self.locale_path, locale, 'LC_MESSAGES', self.mo_name)
            subprocess.check_call(msgfmt + ['--output-file', mo_path, po_path])


command_classes = {
    'makemessages': MakeMessages,
    'compilemessages': CompileMessages,
}
