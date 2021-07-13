import datetime
import functools
import gettext
import json
import logging
import os

import requests

__all__ = ('BankHolidays',)
logger = logging.getLogger(__name__)


class BankHolidays(object):
    """
    Tool to load UK bank holidays from GOV.UK (see https://www.gov.uk/bank-holidays)

    NB: Bank holidays vary between parts of the UK so GOV.UK provide separate lists for different "divisions".
    Methods of this class will default to only considering bank holidays common to *all* divisions
    unless a specific division is provided.
    """
    source_url = 'https://www.gov.uk/bank-holidays.json'

    # division constants
    ENGLAND_AND_WALES = 'england-and-wales'
    SCOTLAND = 'scotland'
    NORTHERN_IRELAND = 'northern-ireland'

    @classmethod
    def load_backup_data(cls):
        with open(os.path.join(os.path.dirname(__file__), 'bank-holidays.json')) as f:
            return json.load(f)

    def __init__(self, locale=None, weekend=(5, 6), use_cached_holidays=False):
        """
        Load UK bank holidays
        :param locale: the locale into which holidays should be translated; defaults to no translation
        :param weekend: days of the week that are never work days; defaults to Saturday and Sunday
        :param use_cached_holidays: use the cached local copy of the holiday list
        """
        self.weekend = set(weekend)
        if use_cached_holidays:
            data = self.load_backup_data()
        else:
            try:
                logger.debug('Downloading bank holidays from %s' % self.source_url)
                data = requests.get(self.source_url).json()
            except (requests.RequestException, ValueError):
                logger.warning('Using backup bank holiday data')
                data = self.load_backup_data()

        if locale:
            trans = gettext.translation('messages', fallback=True, languages=[locale],
                                        localedir=os.path.join(os.path.dirname(__file__), 'locale'))
        else:
            trans = gettext.NullTranslations()
        trans = trans.ugettext if hasattr(trans, 'ugettext') else trans.gettext

        def _(text):
            if not text:
                return text
            return trans(text)

        def map_holiday(holiday):
            try:
                return {
                    'title': _(holiday['title']),
                    'date': datetime.datetime.strptime(holiday['date'], '%Y-%m-%d').date(),
                    'notes': _(holiday.get('notes', '')),
                    'bunting': bool(holiday.get('bunting')),
                }
            except (KeyError, ValueError):
                logger.warning('Holiday could not be parsed')
                logger.debug(holiday, exc_info=True)

        self.data = {
            division: sorted(filter(None, map(map_holiday, item.get('events', []))),
                             key=lambda e: e['date'])
            for division, item in data.items()
        }

    def __iter__(self):
        """
        Iterates over the current year's holidays that are common to *all* divisions
        :return: list of dicts with titles, dates, etc
        """
        return iter(self.get_holidays(year=datetime.date.today().year))

    def get_holidays(self, division=None, year=None):
        """
        Gets a list of all known bank holidays, optionally filtered by division and/or year
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see division constants; defaults to common holidays
        :param year: defaults to all available years
        :return: list of dicts with titles, dates, etc
        """
        if division:
            holidays = self.data[division]
        else:
            holidays = self.data[self.ENGLAND_AND_WALES]
            dates_in_common = functools.reduce(
                set.intersection,
                (
                    set(map(lambda holiday: holiday['date'], division_holidays))
                    for division, division_holidays in self.data.items()
                )
            )
            holidays = filter(lambda holiday: holiday['date'] in dates_in_common, holidays)
        if year:
            holidays = filter(lambda holiday: holiday['date'].year == year, holidays)
        return list(holidays)

    def is_holiday(self, date, division=None):
        """
        True if the date is a known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param date: the date to check
        :param division: see division constants; defaults to common holidays
        :return: bool
        """
        return date in (holiday['date'] for holiday in self.get_holidays(division=division))

    def is_work_day(self, date, division=None):
        """
        True if the date is not a weekend or a known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param date: the date to check
        :param division: see division constants; defaults to common holidays
        :return: bool
        """
        return date.weekday() not in self.weekend and date not in (
            holiday['date'] for holiday in self.get_holidays(division=division)
        )

    def get_next_holiday(self, division=None, date=None):
        """
        Returns the next known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see division constants; defaults to common holidays
        :param date: search starting from this date; defaults to today
        :return: dict or None
        """
        date = date or datetime.date.today()
        for holiday in self.get_holidays(division=division):
            if holiday['date'] > date:
                return holiday

    def get_prev_holiday(self, division=None, date=None):
        """
        Returns the previous known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see division constants; defaults to common holidays
        :param date: search starting from this date; defaults to today
        :return: dict or None
        """
        date = date or datetime.date.today()
        for holiday in reversed(self.get_holidays(division=division)):
            if holiday['date'] < date:
                return holiday

    def get_next_work_day(self, division=None, date=None):
        """
        Returns the next work day, skipping weekends and bank holidays
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see division constants; defaults to common holidays
        :param date: search starting from this date; defaults to today
        :return: datetime.date; NB: get_next_holiday returns a dict
        """
        date = date or datetime.date.today()
        one_day = datetime.timedelta(days=1)
        holidays = set(holiday['date'] for holiday in self.get_holidays(division=division))
        while True:
            date += one_day
            if date.weekday() not in self.weekend and date not in holidays:
                return date

    def get_prev_work_day(self, division=None, date=None):
        """
        Returns the previous work day, skipping weekends and bank holidays
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see division constants; defaults to common holidays
        :param date: search starting from this date; defaults to today
        :return: datetime.date; NB: get_next_holiday returns a dict
        """
        date = date or datetime.date.today()
        one_day = datetime.timedelta(days=1)
        holidays = set(holiday['date'] for holiday in self.get_holidays(division=division))
        while True:
            date -= one_day
            if date.weekday() not in self.weekend and date not in holidays:
                return date
