import distutils.log
import json
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


class UpdateCachedHolidays(setuptools.Command):
    description = 'update locally-cached bank holidays from GOV.UK'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import requests
        from govuk_bank_holidays.bank_holidays import BankHolidays

        self.announce('Updating cached bank holidays', level=distutils.log.INFO)
        root_path = pathlib.Path(__file__).parent.parent
        cached_path = root_path / 'govuk_bank_holidays' / 'bank-holidays.json'
        with cached_path.open() as f:
            cached_data = json.load(f)
        latest_data = requests.get(BankHolidays.source_url).json()
        for division, latest_events in latest_data.items():
            cached_events_dict = dict((event['date'], event) for event in cached_data[division]['events'])
            latest_events_dict = dict((event['date'], event) for event in latest_events['events'])
            for date, event in latest_events_dict.items():
                cached_events_dict[date] = event
            cached_data[division] = dict(
                division=division,
                events=list(cached_events_dict.values()),
            )
        with cached_path.open('w') as f:
            json.dump(cached_data, f, ensure_ascii=False, indent=2)
            f.write('\n')


command_classes = {
    'makemessages': MakeMessages,
    'compilemessages': CompileMessages,
    'updatecachedholidays': UpdateCachedHolidays,
}
