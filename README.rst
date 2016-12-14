GOV.UK Bank Holidays
====================

Usage
-----

Install using ``pip install govuk-bank-holidays``. Sample usage:

.. code-block:: python

    from govuk_bank_holidays.bank_holidays import BankHolidays

    bank_holidays = BankHolidays()
    for bank_holiday in bank_holidays.get_holidays():
        print(bank_holiday['title'], '>', bank_holiday['date'])
    print(bank_holidays.get_next_holiday())

Development
-----------

Please report bugs and open pull requests on `GitHub`_.

Use ``python setup.py test`` to run all tests.

Distribute a new version by updating the ``VERSION`` tuple in ``govuk_bank_holidays`` and run ``python setup.py sdist upload``.

Copyright
---------

Copyright |copy| 2016 HM Government (Ministry of Justice Digital Services). See LICENSE.txt for further details.

.. |copy| unicode:: 0xA9 .. copyright symbol
.. _GitHub: https://github.com/ministryofjustice/govuk-bank-holidays
