import datetime
import functools
import gettext
import json
import logging
import operator
import os

import requests

__all__ = ('BankHolidays', )
logger = logging.getLogger(__name__)


class BankHolidays:
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

    # direction contants
    FUTURE = 'future'
    PAST = 'past'

    @classmethod
    def load_backup_data(cls):
        with open(os.path.join(os.path.dirname(__file__),
                               'bank-holidays.json')) as f:
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
                logger.debug('Downloading bank holidays from %s' %
                             self.source_url)
                data = requests.get(self.source_url).json()
            except (requests.RequestException, ValueError):
                logger.warning('Using backup bank holiday data')
                data = self.load_backup_data()

        if locale:
            trans = gettext.translation('messages',
                                        fallback=True,
                                        languages=[locale],
                                        localedir=os.path.join(
                                            os.path.dirname(__file__),
                                            'locale'))
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
                    'title':
                    _(holiday['title']),
                    'date':
                    datetime.datetime.strptime(holiday['date'],
                                               '%Y-%m-%d').date(),
                    'notes':
                    _(holiday.get('notes', '')),
                    'bunting':
                    bool(holiday.get('bunting')),
                }
            except (KeyError, ValueError):
                logger.warning('Holiday could not be parsed')
                logger.debug(holiday, exc_info=True)

        self.data = {
            division: sorted([
                holiday for holiday in map(map_holiday, item.get('events', []))
                if holiday
            ],
                             key=operator.itemgetter('date'))
            for division, item in data.items()
        }

    def __iter__(self):
        """
        Iterates over the current year's holidays that are common to *all* divisions
        :return: list of dicts with titles, dates, etc
        """
        start = datetime.date(datetime.date.today().year, 1, 1)
        end = datetime.date(datetime.date.today().year, 12, 31)

        return self.holidays(start=start, end=end)

    def _date_or_today(self, date=None):
        """
        Returns the current date when date is omitted
        """
        return date or datetime.date.today()

    def _get_common_holidays(self):
        """
        Returns an iterable of the common holidays
        """
        dates_in_common = functools.reduce(
            set.intersection,
            (set(map(operator.itemgetter('date'), division_holidays))
             for _, division_holidays in self.data.items()))

        holidays = filter(lambda holiday: holiday['date'] in dates_in_common,
                          self.data[self.ENGLAND_AND_WALES])

        return list(holidays)

    def holidays(self,
                 division=None,
                 start=datetime.date.today(),
                 end=None,
                 direction=FUTURE):
        """
        Returns a generator for holidays
        by division
        from a specific date
        direction future or past
        """
        dataset = self.data.get(
            division) if division else self._get_common_holidays()

        def valid_future_dates(e):
            return e['date'] >= start if end is None else e[
                'date'] >= start and e['date'] <= end

        def valid_past_dates(e):
            return e['date'] <= start if end is None else e[
                'date'] <= start and e['date'] >= end

        source = filter(valid_future_dates,
                        dataset) if direction == self.FUTURE else filter(
                            valid_past_dates, reversed(dataset))

        for day in source:
            yield day

    def work_days(self,
                  division=None,
                  start=datetime.date.today(),
                  end=None,
                  direction=FUTURE):
        """
        Returns a generator for working days
        """
        _holidays = map(
            operator.itemgetter('date'),
            self.holidays(division=division,
                          direction=direction,
                          start=start,
                          end=end))
        day = 0

        while True:
            day += 1
            delta = datetime.timedelta(days=day)
            current = start + delta if direction == self.FUTURE else start - delta

            if current.weekday(
            ) not in self.weekend and current not in _holidays:
                yield current

    def get_holidays(self, division=None, year=None):
        """
        Returns an iterable of holidays
        current year when year is omitted
        """
        current_year = year if year is not None else datetime.date.today().year
        start = datetime.date(current_year, 1, 1)
        end = datetime.date(current_year, 12, 31)

        return list(self.holidays(division=division, start=start, end=end))

    def is_holiday(self, date, division=None):
        """
        True if the date is a known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param date: the date to check
        :param division: see division constants; defaults to common holidays
        :return: bool
        """
        return date in map(operator.itemgetter('date'),
                           self.holidays(division=division, start=date))

    def is_work_day(self, date, division=None):
        """
        True if the date is not a weekend or a known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param date: the date to check
        :param division: see division constants; defaults to common holidays
        :return: bool
        """
        return date.weekday() not in self.weekend and not self.is_holiday(
            date, division=division)

    def get_next_holiday(self, division=None, date=None):
        """
        Returns the next known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see division constants; defaults to common holidays
        :param date: search starting from this date; defaults to today
        :return: dict or None
        """
        return next(
            self.holidays(division=division,
                          start=self._date_or_today(date=date)))

    def get_prev_holiday(self, division=None, date=None):
        """
        Returns the previous known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see division constants; defaults to common holidays
        :param date: search starting from this date; defaults to today
        :return: dict or None
        """
        return next(
            self.holidays(division=division,
                          start=self._date_or_today(date=date),
                          direction=self.PAST))

    def get_next_work_day(self, division=None, date=None):
        """
        Returns the next work day, skipping weekends and bank holidays
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see division constants; defaults to common holidays
        :param date: search starting from this date; defaults to today
        :return: datetime.date; NB: get_next_holiday returns a dict
        """
        return next(
            self.work_days(division=division,
                           start=self._date_or_today(date=date),
                           direction=self.FUTURE))

    def get_prev_work_day(self, division=None, date=None):
        """
        Returns the previous work day, skipping weekends and bank holidays
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see division constants; defaults to common holidays
        :param date: search starting from this date; defaults to today
        :return: datetime.date; NB: get_next_holiday returns a dict
        """
        return next(
            self.work_days(division=division,
                           start=self._date_or_today(date=date),
                           direction=self.PAST))
