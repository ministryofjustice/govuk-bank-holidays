import dataclasses
import datetime
import enum
import functools
import gettext
import json
import logging
import pathlib
import typing
import warnings

import requests

__all__ = ('BankHoliday', 'BankHolidays', 'Division')
logger = logging.getLogger(__name__)


@dataclasses.dataclass
class BankHoliday:
    """
    Represents the details of a bank holiday
    """
    title: str
    date: datetime.date
    notes: str = ''
    bunting: bool = False

    def __repr__(self) -> str:
        return f'<BankHoliday: {self.title} ({self.date})>'

    # following methods exists to maintain dict compatibility from previous versions
    # other dict methods deemed not necessary

    def __getitem__(self, item: str) -> typing.Union[str, datetime.date, bool]:
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError

    def keys(self) -> typing.Iterable[str]:
        return (field.name for field in dataclasses.fields(self))

    def items(self) -> typing.Iterable[typing.Tuple[str, typing.Union[str, datetime.date, bool]]]:
        for key in self.keys():
            yield key, getattr(self, key)

    def values(self) -> typing.Iterable[typing.Union[str, datetime.date, bool]]:
        for _key, value in self.items():
            yield value


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


class DeprecatedAttr:
    __slots__ = ('division',)

    def __init__(self, division: Division):
        self.division = division

    def __get__(self, instance, owner) -> Division:
        warnings.warn(
            'Divisions should be accessed from `govuk_bank_holidays.bank_holidays.Division` enumeration now',
            category=DeprecationWarning,
            stacklevel=2,
        )
        return self.division


class BankHolidays:
    """
    Tool to load UK bank holidays from GOV.UK (see https://www.gov.uk/bank-holidays)

    NB: Bank holidays vary between parts of the UK so GOV.UK provide separate lists for different "divisions".
    Methods of this class will default to only considering bank holidays common to *all* divisions
    unless a specific division is provided.
    """
    source_url = 'https://www.gov.uk/bank-holidays.json'

    # deprecated division constants, use Division enumeration
    ENGLAND_AND_WALES = DeprecatedAttr(Division.ENGLAND_AND_WALES)
    SCOTLAND = DeprecatedAttr(Division.SCOTLAND)
    NORTHERN_IRELAND = DeprecatedAttr(Division.NORTHERN_IRELAND)

    @classmethod
    def load_backup_data(cls) -> dict:
        backup_path = pathlib.Path(__file__).parent / 'bank-holidays.json'
        with backup_path.open() as f:
            return json.load(f)

    def __init__(self, locale: str = None, weekend: typing.Iterable[int] = (5, 6), use_cached_holidays: bool = False):
        """
        Load UK bank holidays
        :param locale: the locale into which holidays should be translated; defaults to no translation
        :param weekend: days of the week that are never work days; defaults to Saturday and Sunday
        :param use_cached_holidays: use the cached local copy of the holiday list
        """
        self._get_known_holiday_date_set_cache: typing.Dict[Division, typing.Set[datetime.date]] = {}
        self.weekend: typing.Set[int] = set(weekend)
        if use_cached_holidays:
            data = self.load_backup_data()
        else:
            try:
                logger.debug(f'Downloading bank holidays from {self.source_url}')
                data = requests.get(self.source_url).json()
            except (requests.RequestException, ValueError):
                logger.warning('Using backup bank holiday data')
                data = self.load_backup_data()

        if locale:
            trans = gettext.translation(
                'messages',
                localedir=pathlib.Path(__file__).parent / 'locale',
                languages=[locale],
                fallback=True,
            )
        else:
            trans = gettext.NullTranslations()
        trans = trans.ugettext if hasattr(trans, 'ugettext') else trans.gettext

        def _(text: str) -> str:
            if not text:
                return text
            return trans(text)

        def map_holiday(holiday: dict) -> typing.Optional[BankHoliday]:
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
        :returns: iterator of BankHoliday with titles, dates, etc
        """
        return iter(self.get_holidays(year=datetime.date.today().year))

    def get_holidays(self, division: DivisionType = None, year: int = None) -> typing.List[BankHoliday]:
        """
        Gets a list of all known bank holidays, optionally filtered by division and/or year
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see Division enum; defaults to common holidays
        :param year: defaults to all available years
        :returns: list of BankHoliday with titles, dates, etc
        """
        if division:
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

    def _get_known_holiday_date_set(self, division: DivisionType = None) -> typing.Set[datetime.date]:
        """
        Returns an unordered set of all known bank holiday dates
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        """
        if division not in self._get_known_holiday_date_set_cache:
            self._get_known_holiday_date_set_cache[division] = set(
                holiday.date
                for holiday in self.get_holidays(division=division)
            )
        return self._get_known_holiday_date_set_cache[division]

    def is_holiday(self, date: datetime.date, division: DivisionType = None) -> bool:
        """
        True if the date is a known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param date: the date to check
        :param division: see Division enum; defaults to common holidays
        :returns: bool
        """
        return date in self._get_known_holiday_date_set(division=division)

    def is_work_day(self, date: datetime.date, division: DivisionType = None) -> bool:
        """
        True if the date is not a weekend or a known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param date: the date to check
        :param division: see Division enum; defaults to common holidays
        :returns: bool
        """
        return date.weekday() not in self.weekend and date not in self._get_known_holiday_date_set(division=division)

    def get_next_holiday(self, division: DivisionType = None, date: datetime.date = None) \
            -> typing.Optional[BankHoliday]:
        """
        Returns the next known bank holiday
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see Division enum; defaults to common holidays
        :param date: search starting from this date; defaults to today
        :returns: BankHoliday or None
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
        :returns: BankHoliday or None
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
        :returns: datetime.date; NB: get_next_holiday returns a BankHoliday
        """
        date = date or datetime.date.today()
        one_day = datetime.timedelta(days=1)
        while True:
            date += one_day
            if self.is_work_day(date, division=division):
                return date

    def get_prev_work_day(self, division: DivisionType = None, date: datetime.date = None) -> datetime.date:
        """
        Returns the previous work day, skipping weekends and bank holidays
        NB: If no division is specified, only holidays common to *all* divisions are returned.
        :param division: see Division enum; defaults to common holidays
        :param date: search starting from this date; defaults to today
        :returns: datetime.date; NB: get_next_holiday returns a BankHoliday
        """
        date = date or datetime.date.today()
        one_day = datetime.timedelta(days=1)
        while True:
            date -= one_day
            if self.is_work_day(date, division=division):
                return date

    def holidays_after(self, division: DivisionType = None, date: datetime.date = None) \
            -> typing.Generator[BankHoliday, None, None]:
        """
        Yields known bank holidays in chronological order
        NB: If no division is specified, only holidays common to *all* divisions are yielded.
        :param division: see Division enum; defaults to common holidays
        :param date: starting after this date; defaults to today
        :returns: yields a sequence of BankHoliday
        """
        date = date or datetime.date.today()
        holidays = self.get_holidays(division=division)
        yield from filter(lambda holiday: holiday.date > date, holidays)

    def holidays_before(self, division: DivisionType = None, date: datetime.date = None) \
            -> typing.Generator[BankHoliday, None, None]:
        """
        Yields known bank holidays in reverse chronological order
        NB: If no division is specified, only holidays common to *all* divisions are yielded.
        :param division: see Division enum; defaults to common holidays
        :param date: starting before this date; defaults to today
        :returns: yields a sequence of BankHoliday
        """
        date = date or datetime.date.today()
        holidays = reversed(self.get_holidays(division=division))
        yield from filter(lambda holiday: holiday.date < date, holidays)

    def work_days_after(self, division: DivisionType = None, date: datetime.date = None) \
            -> typing.Generator[datetime.date, None, None]:
        """
        Yields an infinite series of work days in chronological order skipping weekends and known bank holidays
        NB: If no division is specified, only holidays common to *all* divisions are yielded.
        :param division: see Division enum; defaults to common holidays
        :param date: starting after this date; defaults to today
        :returns: yields a sequence of date
        """
        date = date or datetime.date.today()
        one_day = datetime.timedelta(days=1)
        while True:
            date += one_day
            if self.is_work_day(date, division=division):
                yield date

    def work_days_before(self, division: DivisionType = None, date: datetime.date = None) \
            -> typing.Generator[datetime.date, None, None]:
        """
        Yields an infinite series of work days in reverse chronological order skipping weekends and known bank holidays
        NB: If no division is specified, only holidays common to *all* divisions are yielded.
        :param division: see Division enum; defaults to common holidays
        :param date: starting before this date; defaults to today
        :returns: yields a sequence of date
        """
        date = date or datetime.date.today()
        one_day = datetime.timedelta(days=1)
        while True:
            date -= one_day
            if self.is_work_day(date, division=division):
                yield date
