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

    # choose a different locale for holiday titles and notes
    bank_holidays = BankHolidays(locale='cy')

Bank holidays differ around the UK. The GOV.UK source currently lists these for 3 "divisions":

- England and Wales
- Scotland
- Northern Ireland

… and many methods in this library take a ``division`` parameter (c.f. constants on ``BankHolidays`` class).

NB: If no division is specified, only holidays common to *all* divisions are returned.

Development
-----------

.. image:: https://travis-ci.org/ministryofjustice/govuk-bank-holidays.svg?branch=master
    :target: https://travis-ci.org/ministryofjustice/govuk-bank-holidays

Please report bugs and open pull requests on `GitHub`_.

Update translation files using ``python setup.py makemessages``, e.g. when updating the i18n module or when adding new languages.
Compile them using ``python setup.py compilemessages``; this is *required* before testing and distribution.

Use ``python setup.py compilemessages test`` to run all tests.

Distribute a new version by updating the ``VERSION`` tuple in ``govuk_bank_holidays`` and
run ``python setup.py compilemessages sdist bdist_wheel upload``.

Copyright
---------

Copyright (C) 2018 HM Government (Ministry of Justice Digital Services).
See LICENSE.txt for further details.

.. _GitHub: https://github.com/ministryofjustice/govuk-bank-holidays
