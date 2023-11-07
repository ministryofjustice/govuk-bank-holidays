#!/usr/bin/env python
import argparse
import itertools
import json
import logging
import pathlib
import sys


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    parser = argparse.ArgumentParser(description='Update locally-cached bank holidays from GOV.UK')
    parser.parse_args()

    try:
        import govuk_bank_holidays
        logging.debug('govuk_bank_holidays.__version__ = %s', govuk_bank_holidays.__version__)
    except ImportError:
        root_path = pathlib.Path(__file__).parent.parent
        sys.path.insert(0, str(root_path.absolute()))

    cached_data = update_cache()
    check_divisions(cached_data)
    check_i18n(cached_data)


def update_cache():
    import requests
    from govuk_bank_holidays.bank_holidays import BankHolidays

    logging.info('Updating cached bank holidays')
    root_path = pathlib.Path(__file__).parent.parent
    cached_path = root_path / 'govuk_bank_holidays' / 'bank-holidays.json'
    with cached_path.open() as f:
        cached_data = json.load(f)
    event_count = sum(len(events['events']) for events in cached_data.values())
    logging.info('Cached bank holidays event count is %d', event_count)

    logging.info('Downloading bank holidays from %s', BankHolidays.source_url)
    latest_data = requests.get(BankHolidays.source_url).json()
    for division, latest_events in latest_data.items():
        cached_events_dict = dict(
            (event['date'], event)
            for event in cached_data.get(division, dict(events=[]))['events']
        )
        latest_events_dict = dict(
            (event['date'], event)
            for event in latest_events['events']
        )
        for date, event in latest_events_dict.items():
            cached_events_dict[date] = event
        cached_data[division] = dict(
            division=division,
            events=list(cached_events_dict.values()),
        )
    new_event_count = sum(len(events['events']) for events in cached_data.values())
    if new_event_count == event_count:
        logging.info('Cached bank holidays event count is unchanged')
    else:
        logging.info('New cached bank holidays event count is %d', new_event_count)

    with cached_path.open('w') as f:
        json.dump(cached_data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    return cached_data


def check_divisions(cached_data):
    from govuk_bank_holidays.bank_holidays import BankHolidays

    logging.info('Checking cached bank holiday divisions')
    cached_divisions = set(cached_data.keys())
    expected_divisions = set(BankHolidays.ALL_DIVISIONS)
    missing_divisions = expected_divisions - cached_divisions
    if missing_divisions:
        logging.warning(
            'Some expected divisions are missing in cached bank holidays: %s',
            ', '.join(missing_divisions),
        )
    unexpected_divisions = cached_divisions - expected_divisions
    if unexpected_divisions:
        logging.warning(
            'Unexpected divisions found, absent from BankHolidays.ALL_DIVISIONS: %s',
            ', '.join(unexpected_divisions),
        )


def check_i18n(cached_data):
    from govuk_bank_holidays.i18n import translatable_messages

    logging.info('Checking cached bank holidays for inclusion in translation module')
    event_messages = set()
    events = itertools.chain.from_iterable(events['events'] for events in cached_data.values())
    for event in events:
        event_messages.add(event['title'])
        if event.get('notes'):
            event_messages.add(event['notes'])
    untranslatable_messages = event_messages - translatable_messages
    if untranslatable_messages:
        untranslatable_messages = '\n- '.join(untranslatable_messages)
        logging.warning(
            f'Translation markers missing from govuk_bank_holidays.i18n:\n- {untranslatable_messages}',
        )


if __name__ == '__main__':
    main()
