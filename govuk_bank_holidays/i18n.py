"""
Known holiday names that appear in GOV.UK sources are listed here for translation.

`gettext(…)` is used to label messages for inclusion into messages files by `xgettext` via makemessages setup.py command
and `gettext` function here is a dummy to make the module importable.
"""

translatable_messages = set()


def gettext(s):
    translatable_messages.add(s)
    return s


gettext('Bank holiday')
gettext('Bank holidays')

gettext('England')
gettext('Wales')
gettext('England and Wales')
gettext('Scotland')
gettext('Northern Ireland')
gettext('United Kingdom')

gettext('2nd January')
gettext('Battle of the Boyne (Orangemen’s Day)')
gettext('Boxing Day')
gettext('Christmas Day')
gettext('Early May bank holiday')
gettext('Early May bank holiday (VE day)')
gettext('Easter Monday')
gettext('Good Friday')
gettext('New Year’s Day')
gettext('Spring bank holiday')
gettext('St Andrew’s Day')
gettext('St Patrick’s Day')
gettext('Summer bank holiday')

gettext('Queen’s Diamond Jubilee')
gettext('Platinum Jubilee bank holiday')
gettext('Bank Holiday for the State Funeral of Queen Elizabeth II')
gettext('Bank holiday for the coronation of King Charles III')

gettext('Extra bank holiday')
gettext('Substitute day')

del gettext
