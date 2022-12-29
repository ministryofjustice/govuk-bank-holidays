import distutils.log
import os
import pathlib
import subprocess

import setuptools


class MessagesCommand(setuptools.Command):
    user_options = []
    domain = 'messages'

    def __init__(self, *args, **kwargs):
        setuptools.Command.__init__(self, *args, **kwargs)

        self.root_path = pathlib.Path(__file__).parent.parent
        self.locale_path = self.root_path / 'govuk_bank_holidays' / 'locale'

        self.pot_name = f'{self.domain}.pot'
        self.po_name = f'{self.domain}.po'
        self.mo_name = f'{self.domain}.mo'

        self.pot_path = self.locale_path / self.pot_name
        self.locales = [
            str(path)
            for path in self.locale_path.iterdir()
            if (self.locale_path / path / 'LC_MESSAGES' / self.po_name).is_file()
        ]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        cwd = os.getcwd()
        os.chdir(self.root_path)
        self.run_command()
        os.chdir(cwd)

    def run_command(self):
        raise NotImplementedError


class MakeMessages(MessagesCommand):
    description = 'update localisation messages files'
    source_files = ['govuk_bank_holidays/i18n.py']

    def run_command(self):
        self.announce('Writing intermediate POT file', level=distutils.log.INFO)
        xgettext = ['xgettext', '-d', self.domain, '-o', self.pot_path,
                    '--language=Python', '--from-code=UTF-8', '--no-wrap']
        subprocess.check_call(xgettext + self.source_files)

        msgmerge = ['msgmerge', '--no-wrap', '--previous', '--update']
        for locale in self.locales:
            self.announce(f'Writing PO file for {locale} locale', level=distutils.log.INFO)
            po_path = self.locale_path / locale / 'LC_MESSAGES' / self.po_name
            subprocess.check_call(msgmerge + [po_path, self.pot_path])


class CompileMessages(MessagesCommand):
    description = 'compile localisation messages files'

    def run_command(self):
        msgfmt = ['msgfmt', '--check']
        for locale in self.locales:
            self.announce(f'Compiling PO file for {locale} locale', level=distutils.log.INFO)
            po_path = self.locale_path / locale / 'LC_MESSAGES' / self.po_name
            mo_path = self.locale_path / locale / 'LC_MESSAGES' / self.mo_name
            subprocess.check_call(msgfmt + ['--output-file', mo_path, po_path])


command_classes = {
    'makemessages': MakeMessages,
    'compilemessages': CompileMessages,
}
