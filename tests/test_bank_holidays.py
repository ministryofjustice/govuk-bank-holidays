#!/usr/bin/env python
import datetime
import itertools
import unittest
from unittest import mock

import responses

from govuk_bank_holidays.bank_holidays import BankHolidays

# numbers of known bank holidays cached in backup data for 2018-2022
BACKUP_DATA_COMMON_HOLIDAY_COUNT = 32
BACKUP_DATA_ENGLAND_AND_WALES_HOLIDAY_COUNT = 42
BACKUP_DATA_SCOTLAND_HOLIDAY_COUNT = 47
BACKUP_DATA_NORTHERN_IRELAND_HOLIDAY_COUNT = 52


class BankHolidayTestCase(unittest.TestCase):
    @classmethod
    def get_bank_holidays_using_local_data(cls, **kwargs):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, BankHolidays.source_url, json=BankHolidays.load_backup_data())
            return BankHolidays(**kwargs)

    def assertExpectedFormat(self, holidays):  # noqa: N802
        last_holiday = None
        expected_keys = ['bunting', 'date', 'notes', 'title']
        for holiday in holidays:
            self.assertListEqual(sorted(holiday.keys()), expected_keys,
                                 msg='Unexpected or missing dictionary keys')
            self.assertIsInstance(holiday['date'], datetime.date)
            if last_holiday:
                self.assertGreater(holiday['date'], last_holiday['date'],
                                   msg='Holidays are not correctly sorted')
            last_holiday = holiday

    def test_holidays(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        holidays = bank_holidays.get_holidays()
        holidays_2018_to_2022 = [holiday for holiday in holidays if 2018 <= holiday['date'].year <= 2022]
        self.assertEqual(len(holidays_2018_to_2022), BACKUP_DATA_COMMON_HOLIDAY_COUNT)
        self.assertExpectedFormat(holidays)

    def test_holidays_for_division(self):
        bank_holidays = self.get_bank_holidays_using_local_data()

        holidays = bank_holidays.get_holidays(division=BankHolidays.ENGLAND_AND_WALES)
        holidays_2018_to_2022 = [holiday for holiday in holidays if 2018 <= holiday['date'].year <= 2022]
        self.assertEqual(len(holidays_2018_to_2022), BACKUP_DATA_ENGLAND_AND_WALES_HOLIDAY_COUNT)
        self.assertExpectedFormat(holidays)
        self.assertNotIn('St Patrick’s Day', map(lambda holiday: holiday['title'], holidays))

        holidays = bank_holidays.get_holidays(division=BankHolidays.SCOTLAND)
        holidays_2018_to_2022 = [holiday for holiday in holidays if 2018 <= holiday['date'].year <= 2022]
        self.assertEqual(len(holidays_2018_to_2022), BACKUP_DATA_SCOTLAND_HOLIDAY_COUNT)
        self.assertExpectedFormat(holidays)
        self.assertIn('St Andrew’s Day', map(lambda holiday: holiday['title'], holidays))

        holidays = bank_holidays.get_holidays(division=BankHolidays.NORTHERN_IRELAND)
        holidays_2018_to_2022 = [holiday for holiday in holidays if 2018 <= holiday['date'].year <= 2022]
        self.assertEqual(len(holidays_2018_to_2022), BACKUP_DATA_NORTHERN_IRELAND_HOLIDAY_COUNT)
        self.assertExpectedFormat(holidays)
        self.assertIn('St Patrick’s Day', map(lambda holiday: holiday['title'], holidays))

    def test_holidays_for_year(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        holidays = bank_holidays.get_holidays(year=2017)
        self.assertEqual(len(holidays), 6)
        self.assertExpectedFormat(holidays)
        self.assertTrue(all(holiday['date'].year == 2017 for holiday in holidays))

    def test_holidays_for_division_and_year(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        holidays = bank_holidays.get_holidays(division=BankHolidays.NORTHERN_IRELAND, year=2016)
        self.assertEqual(len(holidays), 10)
        self.assertExpectedFormat(holidays)
        self.assertIn('Battle of the Boyne (Orangemen’s Day)', map(lambda holiday: holiday['title'], holidays))
        self.assertTrue(all(holiday['date'].year == 2016 for holiday in holidays))

    def test_holiday_iterator(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        holidays_1 = [holiday for holiday in bank_holidays]
        holidays_2 = bank_holidays.get_holidays(year=datetime.date.today().year)
        self.assertListEqual(holidays_1, holidays_2)

    def test_next_bank_holiday(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        second_january = datetime.date(2016, 1, 2)
        self.assertEqual(
            bank_holidays.get_next_holiday(date=second_january)['date'],
            datetime.date(2016, 3, 25)
        )
        self.assertEqual(
            bank_holidays.get_next_holiday(division=BankHolidays.SCOTLAND, date=second_january)['date'],
            datetime.date(2016, 1, 4)
        )

    def test_prev_bank_holiday(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        fifth_january = datetime.date(2016, 1, 5)
        self.assertEqual(
            bank_holidays.get_prev_holiday(date=fifth_january)['date'],
            datetime.date(2016, 1, 1)
        )
        self.assertEqual(
            bank_holidays.get_prev_holiday(division=BankHolidays.SCOTLAND, date=fifth_january)['date'],
            datetime.date(2016, 1, 4)
        )

    def test_is_holiday_check(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        self.assertTrue(bank_holidays.is_holiday(datetime.date(2012, 1, 2)))
        self.assertFalse(bank_holidays.is_holiday(datetime.date(2016, 1, 4)))
        self.assertTrue(bank_holidays.is_holiday(datetime.date(2016, 1, 4), division=BankHolidays.SCOTLAND))

    def test_next_work_day(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        self.assertEqual(
            bank_holidays.get_next_work_day(date=datetime.date(2017, 12, 19)),
            datetime.date(2017, 12, 20)
        )
        self.assertEqual(
            bank_holidays.get_next_work_day(date=datetime.date(2017, 12, 22)),
            datetime.date(2017, 12, 27)
        )
        self.assertEqual(
            bank_holidays.get_next_work_day(date=datetime.date(2017, 12, 30)),
            datetime.date(2018, 1, 2)
        )
        self.assertEqual(
            bank_holidays.get_next_work_day(division=BankHolidays.SCOTLAND, date=datetime.date(2017, 12, 30)),
            datetime.date(2018, 1, 3)
        )

    def test_prev_work_day(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        self.assertEqual(
            bank_holidays.get_prev_work_day(date=datetime.date(2017, 12, 19)),
            datetime.date(2017, 12, 18)
        )
        self.assertEqual(
            bank_holidays.get_prev_work_day(date=datetime.date(2017, 12, 18)),
            datetime.date(2017, 12, 15)
        )
        self.assertEqual(
            bank_holidays.get_prev_work_day(date=datetime.date(2017, 12, 27)),
            datetime.date(2017, 12, 22)
        )
        self.assertEqual(
            bank_holidays.get_prev_work_day(date=datetime.date(2018, 1, 3)),
            datetime.date(2018, 1, 2)
        )
        self.assertEqual(
            bank_holidays.get_prev_work_day(division=BankHolidays.SCOTLAND, date=datetime.date(2018, 1, 3)),
            datetime.date(2017, 12, 29)
        )

    def test_is_work_day(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        self.assertTrue(bank_holidays.is_work_day(datetime.date(2017, 12, 19)))
        self.assertFalse(bank_holidays.is_work_day(datetime.date(2018, 1, 1)))
        self.assertTrue(bank_holidays.is_work_day(datetime.date(2018, 1, 2)))
        self.assertFalse(bank_holidays.is_work_day(datetime.date(2018, 1, 2), division=BankHolidays.SCOTLAND))

    def test_configuring_weekends(self):
        bank_holidays = self.get_bank_holidays_using_local_data(weekend={1, 5, 6})
        self.assertFalse(bank_holidays.is_work_day(datetime.date(2017, 12, 19)))

    @mock.patch('govuk_bank_holidays.bank_holidays.logger')
    def test_holidays_use_backup_data(self, mock_logger):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, BankHolidays.source_url, status=404)
            bank_holidays = BankHolidays()
        mock_logger.warning.assert_called_once_with('Using backup bank holiday data')
        self.assertTrue(bank_holidays.get_holidays())

    @mock.patch('govuk_bank_holidays.bank_holidays.logger')
    def test_using_cached_list_of_holidays(self, mock_logger):
        with responses.RequestsMock():
            bank_holidays = BankHolidays(use_cached_holidays=True)
        mock_logger.warning.assert_not_called()
        self.assertTrue(bank_holidays.get_holidays())

    def test_localisation(self):
        bank_holidays = self.get_bank_holidays_using_local_data(locale='cy')  # Welsh
        holidays = bank_holidays.get_holidays(division=BankHolidays.ENGLAND_AND_WALES)
        holiday_names = set(holiday['title'] for holiday in holidays)
        self.assertIn('Dydd Nadolig', holiday_names)
        self.assertNotIn('Christmas Day', holiday_names)

    def test_localisation_fallback(self):
        bank_holidays = self.get_bank_holidays_using_local_data(locale='gd')  # Scottish Gaelic
        holidays = bank_holidays.get_holidays(division=BankHolidays.SCOTLAND)
        holiday_names = set(holiday['title'] for holiday in holidays)
        self.assertIn('Christmas Day', holiday_names)
        self.assertNotIn('Latha na Nollaige', holiday_names)

    def test_future_holiday_generators(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        generator = bank_holidays.holidays_after(date=datetime.date(2016, 1, 2))
        self.assertEqual(next(generator)['date'], datetime.date(2016, 3, 25))
        self.assertEqual(next(generator)['date'], datetime.date(2016, 5, 2))
        self.assertEqual(next(generator)['date'], datetime.date(2016, 5, 30))
        more_holidays = list(itertools.islice(generator, 3))
        self.assertEqual(len(more_holidays), 3)
        self.assertExpectedFormat(more_holidays)
        generator = bank_holidays.holidays_after(division=BankHolidays.SCOTLAND, date=datetime.date(2016, 1, 2))
        self.assertEqual(next(generator)['date'], datetime.date(2016, 1, 4))

    def test_past_holiday_generators(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        generator = bank_holidays.holidays_before(date=datetime.date(2016, 1, 5))
        self.assertEqual(next(generator)['date'], datetime.date(2016, 1, 1))
        self.assertEqual(next(generator)['date'], datetime.date(2015, 12, 28))
        self.assertEqual(next(generator)['date'], datetime.date(2015, 12, 25))
        more_holidays = list(itertools.islice(generator, 3))
        self.assertEqual(len(more_holidays), 3)
        self.assertExpectedFormat(list(reversed(more_holidays)))
        generator = bank_holidays.holidays_before(division=BankHolidays.SCOTLAND, date=datetime.date(2016, 1, 5))
        self.assertEqual(next(generator)['date'], datetime.date(2016, 1, 4))

    def test_future_work_day_generators(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        generator = bank_holidays.work_days_after(date=datetime.date(2017, 12, 19))
        self.assertEqual(next(generator), datetime.date(2017, 12, 20))
        self.assertEqual(next(generator), datetime.date(2017, 12, 21))
        self.assertEqual(next(generator), datetime.date(2017, 12, 22))
        self.assertEqual(next(generator), datetime.date(2017, 12, 27))
        generator = bank_holidays.work_days_after(date=datetime.date(2017, 12, 30))
        self.assertSequenceEqual(
            list(itertools.islice(generator, 3)),
            [datetime.date(2018, 1, 2), datetime.date(2018, 1, 3), datetime.date(2018, 1, 4)],
        )
        generator = bank_holidays.work_days_after(division=BankHolidays.SCOTLAND, date=datetime.date(2017, 12, 30))
        self.assertSequenceEqual(
            list(itertools.islice(generator, 3)),
            [datetime.date(2018, 1, 3), datetime.date(2018, 1, 4), datetime.date(2018, 1, 5)],
        )
        generator = bank_holidays.work_days_after(date=datetime.date(2050, 12, 24))
        self.assertEqual(len(list(itertools.islice(generator, 14))), 14)

    def test_past_work_day_generators(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        generator = bank_holidays.work_days_before(date=datetime.date(2018, 1, 3))
        self.assertEqual(next(generator), datetime.date(2018, 1, 2))
        self.assertEqual(next(generator), datetime.date(2017, 12, 29))
        self.assertEqual(next(generator), datetime.date(2017, 12, 28))
        self.assertEqual(next(generator), datetime.date(2017, 12, 27))
        generator = bank_holidays.work_days_before(division=BankHolidays.SCOTLAND, date=datetime.date(2018, 1, 3))
        self.assertEqual(next(generator), datetime.date(2017, 12, 29))
        self.assertEqual(next(generator), datetime.date(2017, 12, 28))
        self.assertEqual(next(generator), datetime.date(2017, 12, 27))
        generator = bank_holidays.work_days_after(date=datetime.date(2000, 1, 3))
        self.assertEqual(len(list(itertools.islice(generator, 14))), 14)
