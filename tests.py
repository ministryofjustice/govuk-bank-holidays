#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
import subprocess
import unittest

try:
    from unittest import mock
except ImportError:
    import mock
import responses

from govuk_bank_holidays.bank_holidays import BankHolidays


class BankHolidayTestCase(unittest.TestCase):
    @classmethod
    def get_bank_holidays_using_local_data(cls, **kwargs):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, BankHolidays.source_url, json=BankHolidays.load_backup_data())
            return BankHolidays(**kwargs)

    def assertExpectedFormat(self, holidays):
        last_holiday = None
        expected_keys = ['bunting', 'date', 'notes', 'title']
        for holiday in holidays:
            if not last_holiday:
                continue
            self.assertListEqual(sorted(holiday.keys()), expected_keys,
                                 msg='Unexpected or missing dictionary keys')
            self.assertGreater(holiday['date'], last_holiday['date'],
                               msg='Holidays are not correctly sorted')
            last_holiday = holiday

    def test_holidays(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        holidays = bank_holidays.get_holidays()
        self.assertEqual(len(holidays), 37)
        self.assertExpectedFormat(holidays)

    def test_holidays_for_division(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        holidays = bank_holidays.get_holidays(division=BankHolidays.ENGLAND_AND_WALES)
        self.assertEqual(len(holidays), 49)
        self.assertExpectedFormat(holidays)
        holidays = bank_holidays.get_holidays(division=BankHolidays.SCOTLAND)
        self.assertEqual(len(holidays), 55)
        self.assertExpectedFormat(holidays)
        self.assertIn(u'St Andrew\u2019s Day', map(lambda holiday: holiday['title'], holidays))

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
        self.assertIn(u'Battle of the Boyne (Orangemen’s Day)', map(lambda holiday: holiday['title'], holidays))
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

    def test_is_holiday_check(self):
        bank_holidays = self.get_bank_holidays_using_local_data()
        self.assertTrue(bank_holidays.is_holiday(datetime.date(2012, 1, 2)))
        self.assertFalse(bank_holidays.is_holiday(datetime.date(2016, 1, 4)))
        self.assertTrue(bank_holidays.is_holiday(datetime.date(2016, 1, 4), division=BankHolidays.SCOTLAND))

    @mock.patch('govuk_bank_holidays.bank_holidays.logger')
    def test_holidays_use_backup_data(self, mock_logger):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, BankHolidays.source_url, status=404)
            bank_holidays = BankHolidays()
        mock_logger.warning.assert_called_once_with('Using backup bank holiday data')
        self.assertTrue(bank_holidays.get_holidays())

    def test_localisation(self):
        bank_holidays = self.get_bank_holidays_using_local_data(locale='cy')
        holidays = bank_holidays.get_holidays(division=BankHolidays.ENGLAND_AND_WALES)
        holiday_names = set(holiday['title'] for holiday in holidays)
        self.assertIn('Dydd Nadolig', holiday_names)
        self.assertNotIn('Christmas Day', holiday_names)


class CodeStyleTestCase(unittest.TestCase):
    def test_code_style(self):
        try:
            subprocess.check_output(['flake8'])
        except subprocess.CalledProcessError as e:
            self.fail('Code style checks failed\n%s' % e.output.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
