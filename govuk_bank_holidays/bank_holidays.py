import datetime
import enum
import functools
import gettext
import json
import logging
import os
import typing

import requests

__all__ = ('BankHolidays', 'BankHoliday', 'Division')
logger = logging.getLogger(__name__)


class Division(str, enum.Enum):
    """
    Bank holidays vary between parts of the UK so GOV.UK provide separate lists for different "divisions".
    """
    ENGLAND_AND_WALES = 'england-and-wales'
    SCOTLAND = 'scotland'
    NORTHERN_IRELAND = 'northern-ireland'

    def __repr__(self):
        return f'<Division: {self._name_}>'


DivisionType = typing.Union[Division, str, None]


class BankHoliday:
    """
    Represents the details of a bank holiday
    """
    __slots__ = ('title', 'date', 'notes', 'bunting')

    def __init__(self, title: str, date: datetime.date, notes: str = '', bunting: bool = False):
        self.title: str = title
        self.date: datetime.date = date
        self.notes: str = notes
        self.bunting: bool = bunting

    def __repr__(self):
        return f'<{self.title} ({self.date})>'

    def __getitem__(self, item):
        # this method exists to maintain dictionary access compatibility from previous versions
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError


class BankHolidays:
    """
    Tool to load UK bank holidays from GOV.UK (see https://www.gov.uk/bank-holidays)

    NB: Bank holidays vary between parts of the UK so GOV.UK provide separate lists for different "divisions".
    Methods of this class will default to only considering bank holidays common to *all* divisions
    unless a specific division is provided.
    """
    source_url = 'https://www.gov.uk/bank-holidays.json'

    # division constants
    ENGLAND_AND_WALES = Division.ENGLAND_AND_WALES
    SCOTLAND = Division.SCOTLAND
    NORTHERN_IRELAND = Division.NORTHERN_IRELAND

    @classmethod
    def load_backup_data(cls) -> dict:
        with open(os.path.join(os.path.dirname(__file__), 'bank-holidays.json')) as f:
            return json.load(f)

    def __init__(self, locale: str = None, weekend: typing.Iterable[int] = (5, 6), use_cached_holidays: bool = False):
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
                return BankHoliday(
                    title=_(holiday['title']),
                    date=datetime.datetime.strptime(holiday['date'], '%Y-%m-%d').date(),
                    notes=_(holiday.get('notes') or ''),
                    bunting=bool(holiday.get('bunting')),
                )
            except (KeyError, ValueError):
                logger.warning('Holiday could not be parsed')
                logger.debug(holiday, exc_info=True)

        self._data = {
            Division(division): sorted(filter(None, map(map_holiday, item.get('events', []))),
                                       key=lambda holiday: holiday.date)
            for division, item in data.items()
        }

    def __iter__(self) -> typing.Iterator[BankHoliday]:
        """
        Iterates over the current year's holidays that are common to *all* divisions
        """
        return iter(self.get_holidays(year=datetime.date.today().year))

    def get_holidays(self, division: DivisionType = None, year: int = None) -> typing.List[BankHoliday]:
        """
        Gets a list of all known bank holidays, optionally filtered by division and/or year
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see Division enum; defaults to common holidays
        :param year: defaults to all available years
        """
        if division:
            if isinstance(division, str):
                division = Division(division)
            holidays = self._data[division]
        else:
            holidays = self._data[Division.ENGLAND_AND_WALES]
            dates_in_common = functools.reduce(
                set.intersection,
                (
                    set(map(lambda holiday: holiday.date, division_holidays))
                    for division, division_holidays in self._data.items()
                )
            )
            holidays = filter(lambda holiday: holiday.date in dates_in_common, holidays)
        if year:
            holidays = filter(lambda holiday: holiday.date.year == year, holidays)
        return list(holidays)

    def is_holiday(self, date: datetime.date, division: DivisionType = None) -> bool:
        """
        True if the date is a known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param date: the date to check
        :param division: see Division enum; defaults to common holidays
        """
        return date in (holiday.date for holiday in self.get_holidays(division=division))

    def is_work_day(self, date: datetime.date, division: DivisionType = None) -> bool:
        """
        True if the date is not a weekend or a known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param date: the date to check
        :param division: see Division enum; defaults to common holidays
        """
        return date.weekday() not in self.weekend and date not in (
            holiday.date for holiday in self.get_holidays(division=division)
        )

    def get_next_holiday(self, division: DivisionType = None, date: datetime.date = None) \
            -> typing.Optional[BankHoliday]:
        """
        Returns the next known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see Division enum; defaults to common holidays
        :param date: search starting from this date; defaults to today
        """
        date = date or datetime.date.today()
        for holiday in self.get_holidays(division=division):
            if holiday.date > date:
                return holiday

    def get_prev_holiday(self, division: DivisionType = None, date: datetime.date = None) \
            -> typing.Optional[BankHoliday]:
        """
        Returns the previous known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see Division enum; defaults to common holidays
        :param date: search starting from this date; defaults to today
        """
        date = date or datetime.date.today()
        for holiday in reversed(self.get_holidays(division=division)):
            if holiday.date < date:
                return holiday

    def get_next_work_day(self, division: DivisionType = None, date: datetime.date = None) -> datetime.date:
        """
        Returns the next work day, skipping weekends and bank holidays
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see Division enum; defaults to common holidays
        :param date: search starting from this date; defaults to today
        """
        date = date or datetime.date.today()
        one_day = datetime.timedelta(days=1)
        holidays = set(holiday.date for holiday in self.get_holidays(division=division))
        while True:
            date += one_day
            if date.weekday() not in self.weekend and date not in holidays:
                return date

    def get_prev_work_day(self, division: DivisionType = None, date: datetime.date = None) -> datetime.date:
        """
        Returns the previous work day, skipping weekends and bank holidays
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see Division enum; defaults to common holidays
        :param date: search starting from this date; defaults to today
        """
        date = date or datetime.date.today()
        one_day = datetime.timedelta(days=1)
        holidays = set(holiday.date for holiday in self.get_holidays(division=division))
        while True:
            date -= one_day
            if date.weekday() not in self.weekend and date not in holidays:
                return date
