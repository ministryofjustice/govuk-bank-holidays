GOV.UK Bank Holidays
====================

This library loads the official list of bank holidays in the United Kingdom as supplied by `GOV.UK`_.
GOV.UK tend to provide this list for only a year or two into the future.

Usage
-----

Install using ``pip install govuk-bank-holidays``. Sample usage:

.. code-block:: python

    from govuk_bank_holidays.bank_holidays import BankHolidays

    bank_holidays = BankHolidays()
    for bank_holiday in bank_holidays.get_holidays():
        print(bank_holiday['title'], '>', bank_holiday['date'])
    print(bank_holidays.get_next_holiday())
    # see govuk_bank_holidays/bank_holidays.py source file for more methods and arguments…

    # choose a different locale for holiday titles and notes
    bank_holidays = BankHolidays(locale='cy')

Bank holidays differ around the UK. The GOV.UK source currently lists these for 3 "divisions":

- England and Wales
- Scotland
- Northern Ireland

… and many methods in this library take a ``division`` parameter (see constants defined on ``BankHolidays`` class).

NB: If no division is specified, only holidays common to *all* divisions are returned so some local bank holidays
may not be listed. Therefore specifying a division is recommended.

While localisation is provided in English (the default with locale code 'en') and Welsh (locale code 'cy'),
please note that the Welsh version may contain errors.

Development
-----------

.. image:: https://github.com/ministryofjustice/govuk-bank-holidays/workflows/Run%20tests/badge.svg?branch=master
    :target: https://github.com/ministryofjustice/govuk-bank-holidays/actions

Please report bugs and open pull requests on `GitHub`_.

Update translation files using ``python setup.py makemessages``, e.g. when updating the i18n module or when adding new languages.
Compile them using ``python setup.py compilemessages``; this is *required* before testing and distribution.

Use ``python setup.py compilemessages test`` to run all tests locally.

Distribute a new version by:

- updating the ``VERSION`` tuple in ``govuk_bank_holidays``
- adding a note to the `History`_
- publishing a release on GitHub which triggers an upload to PYPI

Alternatively, run ``python setup.py compilemessages sdist bdist_wheel upload`` locally.

History
-------

0.9
    Added methods to find previous bank holidays / work days, mirroring the existing methods.
    Removed support for python versions older than 3.6.
    Added python 3.9 to testing matrix.

0.8
    The library does not differ from 0.7.
    This release is the first to use GitHub Actions to automatically publish to PYPI.

0.7
    Minor documentation update.

0.6
    Updated cached bank holidays file to include latest holidays published by GOV.UK.
    Added python 3.8 to testing matrix.
    Minor documentation update.

0.5
    Updated cached bank holidays file to include latest holidays published by GOV.UK.

0.4
    Updated cached bank holidays file to include latest holidays published by GOV.UK.
    Added python 3.7 to testing matrix.
    Documentation improved.

0.3
    Improved testing.
    Library unchanged.

0.2
    Updated cached bank holidays file to include latest holidays published by GOV.UK.
    Added option to force use of cached file.
    Added next work day calculation.

0.1
    Initial release.

Copyright
---------

Copyright (C) 2021 HM Government (Ministry of Justice Digital & Technology).
See LICENSE.txt for further details.

.. _GOV.UK: https://www.gov.uk/bank-holidays
.. _GitHub: https://github.com/ministryofjustice/govuk-bank-holidays
