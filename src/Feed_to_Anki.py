# -*- coding: utf-8 -*-
# Feed to Anki: an Anki addon makes a RSS (or Atom) Feed into Anki cards.
# Version: 0.9
# GitHub: https://github.com/ijgnd/anki__feed_to_anki
#
# Copyright: 2016-2017 Luminous Spice <luminous.spice@gmail.com>
#            2020- ijgnd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import requests

from aqt import mw
from aqt.utils import showText
from aqt.qt import (
    QAction,
)
from anki.lang import ngettext
from bs4 import BeautifulSoup


def gc(arg, fail=False):
    conf = mw.addonManager.getConfig(__name__)
    if conf:
        return conf.get(arg, fail)
    else:
        return fail


def getFeed(url):
    data = ""
    errmsg = ""
    try:
        r = requests.get(url)
        data = r.text
    except requests.ConnectionError as e:
        errmsg = "Failed to reach the server." + str(e) + "\n"
    except requests.HTTPError as e:
        errmsg = "The server couldn\'t fulfill the request." + str(e) + "\n"
    else:
        if not str(r.status_code) in ("200", "304"):
            errmsg = "The server couldn\'t return the file." + " Code: " + str( r.status_code) + "\n"
    finally:
        return [data, errmsg]


def addFeedModel(col):
    # add the model for feeds
    mm = col.models
    m = mm.new(gc("note type"))
    target_fields = gc('target_fields')
    for f in target_fields:
        fm = mm.newField(f)
        mm.addField(m, fm)
    t = mm.newTemplate("Card 1")
    t['qfmt'] = "{{"+target_fields[0]+"}}"
    t['afmt'] = "{{FrontSide}}\n\n<hr id=answer>\n\n"+"{{"+target_fields[1]+"}}"
    mm.addTemplate(m, t)
    mm.add(m)
    return m


# iterate decks
def buildCards():
    msg = ""
    mw.progress.start(immediate=True)
    feeds_info = gc('feeds_info')
    for i in range(len(feeds_info)):
        msg += feeds_info[i]["DECK"] + ":\n"
        msg += buildCard(**feeds_info[i]) + "\n"
    mw.progress.finish()
    showText(msg)


def buildCard(**kw):
    # get deck and model
    deck  = mw.col.decks.get(mw.col.decks.id(kw['DECK']))
    model = mw.col.models.byName(gc("note type"))

    # if MODEL doesn't exist, create a MODEL
    if model is None:
        model = addFeedModel(mw.col)
        model['name'] = gc("note type")
    else:
        act_name = set([f['name'] for f in model['flds']])
        std_name = set(gc('target_fields'))
        if not len(act_name & std_name) == 2:
            model['name'] = gc("note type") + "-" + model['id']
            model = addFeedModel(mw.col)
            model['name'] = gc("note type")

    # assign model to deck
    mw.col.decks.select(deck['id'])
    mw.col.decks.get(deck)['mid'] = model['id']
    mw.col.decks.save(deck)

    # assign deck to model
    mw.col.models.setCurrent(model)
    mw.col.models.current()['did'] = deck['id']
    mw.col.models.save(model)

    # retrieve rss
    data, errmsg = getFeed(kw['URL'])
    if errmsg:
        return errmsg

    #parse xml
    doc = BeautifulSoup(data, "html.parser")

    if not doc.find('item') is None:
        items = doc.findAll('item')
        feed = "rss"
    elif not doc.find('entry') is None:
        items = doc.findAll('entry')
        feed = "atom"
    else:
        return

    # iterate notes
    dups = 0
    adds = 0
    target_fields = gc('target_fields')
    for item in items:
        note = mw.col.newNote()
        note[target_fields[0]] = item.title.text
        nounique = note.dupeOrEmpty()
        if nounique:
            if nounique == 2:
                dups += 1
            continue
        if feed == "rss":
            if not item.description is None:
                note[target_fields[1]] = item.description.text
        if feed == "atom":
            if not item.content is None:
                note[target_fields[1]] = item.content.text
            elif not item.summary is None:
                note[target_fields[1]] = item.summary.text
        note.tags = filter(None, kw['tags'])
        mw.col.addNote(note)
        adds += 1

    mw.col.reset()
    mw.reset()

    # show result
    msg = ngettext("%d note added", "%d notes added", adds) % adds
    msg += "\n"
    if dups > 0:
        msg += _("<ignored>") + "\n"
        msg += _("duplicate") + ": "
        msg += ngettext("%d note", "%d notes", dups) % dups
        msg += "\n"
    return msg

# create a new menu item
action = QAction("Feed to Anki", mw)
action.triggered.connect(buildCards)
mw.form.menuTools.addAction(action)
