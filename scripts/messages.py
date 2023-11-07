#!/usr/bin/env python
import argparse
import logging
import pathlib
import subprocess
import sys


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    parser = argparse.ArgumentParser(description='Manage gettext localisation messages')
    sub_parsers = parser.add_subparsers()
    description = 'Update localisation message files from source code'
    sub_parser = sub_parsers.add_parser('update', help=description, description=description)
    sub_parser.set_defaults(command='update')
    description = 'Compile gettext binary localisation message files'
    sub_parser = sub_parsers.add_parser('compile', help=description, description=description)
    sub_parser.set_defaults(command='compile')

    args = parser.parse_args()
    if not hasattr(args, 'command'):
        parser.print_help()
        sys.exit(1)

    domain = 'messages'
    source_files = ['govuk_bank_holidays/i18n.py']

    root_path = pathlib.Path(__file__).parent.parent
    locale_path = root_path / 'govuk_bank_holidays' / 'locale'
    if not locale_path.is_dir():
        logging.error('This script mst be run from the repository root')
        sys.exit(1)

    pot_name = f'{domain}.pot'
    po_name = f'{domain}.po'
    mo_name = f'{domain}.mo'

    pot_path = locale_path / pot_name
    locales = [
        str(path)
        for path in locale_path.iterdir()
        if (locale_path / path / 'LC_MESSAGES' / po_name).is_file()
    ]

    if args.command == 'update':
        logging.info('Writing intermediate POT file')
        xgettext = [
            'xgettext',
            '--default-domain', domain,
            '--output', pot_path,
            '--language', 'Python',
            '--from-code', 'UTF-8',
            '--no-wrap',
            '--verbose',
        ]
        subprocess.run(xgettext + source_files, check=True)

        msgmerge = [
            'msgmerge',
            '--no-wrap',
            '--previous',
            '--update',
            '--verbose',
        ]
        for locale in locales:
            logging.info('Writing PO file for %s locale', locale)
            po_path = locale_path / locale / 'LC_MESSAGES' / po_name
            subprocess.run(msgmerge + [po_path, pot_path], check=True)

    if args.command == 'compile':
        msgfmt = ['msgfmt', '--check', '--verbose']
        for locale in locales:
            logging.info('Compiling PO file for %s locale', locale)
            po_path = locale_path / locale / 'LC_MESSAGES' / po_name
            mo_path = locale_path / locale / 'LC_MESSAGES' / mo_name
            subprocess.run(msgfmt + ['--output-file', mo_path, po_path], check=True)


if __name__ == '__main__':
    main()
