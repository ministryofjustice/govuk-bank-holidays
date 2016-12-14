# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import json
import logging
import os

import requests
import six

__all__ = ('BankHolidays',)
logger = logging.getLogger(__name__)


class BankHolidays(object):
    """
    Tool to load UK bank holidays from GOV.UK
    C.f. https://www.gov.uk/bank-holidays
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

    def __init__(self):
        try:
            data = requests.get(self.source_url).json()
        except (requests.RequestException, ValueError):
            logger.warning('Using backup bank holiday data')
            data = self.load_backup_data()

        def map_holiday(holiday):
            try:
                return {
                    'title': holiday['title'],
                    'date': datetime.datetime.strptime(holiday['date'], '%Y-%m-%d').date(),
                    'notes': holiday.get('notes', ''),
                    'bunting': bool(holiday.get('bunting')),
                }
            except (KeyError, ValueError):
                logger.warning('Holiday could not be parsed')
                logger.debug(holiday, exc_info=True)

        self.data = {
            division: sorted(filter(None, map(map_holiday, item.get('events', []))),
                             key=lambda e: e['date'])
            for division, item in six.iteritems(data)
        }

    def __iter__(self):
        """
        Iterates over the current year's holidays that are common to all divisions
        :return: list of dicts with titles, dates, etc
        """
        return iter(self.get_holidays(year=datetime.date.today().year))

    def get_holidays(self, division=None, year=None):
        """
        Gets a list of all known bank holidays, optionally filtered by division and/or year
        :param division: see division constants; defaults to common holidays
        :param year: defaults to all available years
        :return: list of dicts with titles, dates, etc
        """
        if division:
            holidays = self.data[division]
        else:
            holidays = self.data[self.ENGLAND_AND_WALES]
            dates_in_common = six.moves.reduce(
                set.intersection,
                (set(map(lambda holiday: holiday['date'], division_holidays))
                 for division, division_holidays in six.iteritems(self.data))
            )
            holidays = filter(lambda holiday: holiday['date'] in dates_in_common, holidays)
        if year:
            holidays = filter(lambda holiday: holiday['date'].year == year, holidays)
        return list(holidays)

    def get_next_holiday(self, division=None, date=None):
        """
        Returns the next known bank holiday
        :param division: see division constants; defaults to common holidays
        :param date: search starting from this date; defaults to today
        :return: dict
        """
        date = date or datetime.date.today()
        for holiday in self.get_holidays(division=division):
            if holiday['date'] > date:
                return holiday

    def is_holiday(self, date, division=None):
        """
        True if the date is a known bank holiday
        :param date: the date to check
        :param division: see division constants; defaults to common holidays
        :return: bool
        """
        return date in (holiday['date'] for holiday in self.get_holidays(division=division))
