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

"""
TODO: use https://pythonhosted.org/feedparser/ (e.g. used in incremental reading add-on)
      5.2 from 2015 in 2020-05 is latest stable (also in IR addon)
      there's also a prelease for 6 on https://github.com/kurtmckee/feedparser
TODO: better duplicate detection: also check existing notes
TODO: add url to field (doesn't seem to work with bs4)  
TODO: "Strip/Delete" with regex          
"""

import pprint
import requests

from aqt import mw
from aqt.utils import showText, showInfo
from aqt.qt import (
    QAction,
)
from anki.hooks import addHook
from anki.lang import ngettext, _
from bs4 import BeautifulSoup

from .config import gc, already_downloaded_pickle
from .helpers import fields_to_fill_for_nonempty_front_template
from .picklehandler import (
    pickleload,
    picklesave
)


def loaddict():
    global processed
    processed = pickleload(already_downloaded_pickle)
addHook("profileLoaded", loaddict)


def savedict():
    picklesave(processed, already_downloaded_pickle)
addHook('unloadProfile', savedict)


addonname = "Feed to Anki"


def is_valid_config(config):
    missing_decks = []
    missing_noteptyes = []
    missing_fields = {}
    for entry in config["feeds_info"]:
        if entry["Deck"] not in mw.col.decks.allNames():
            missing_decks.append(entry["Deck"])
        if entry["Note type"] not in mw.col.models.allNames():
            missing_noteptyes.append(entry["Note type"])
        else:
            # note type exists, check field names
            model = mw.col.models.byName(entry["Note type"])
            needsmatching = []
            title = entry["Mapping: Title"]
            if title:
                needsmatching.append(title)
            back = entry["Mapping: Content/Description/Summary"]
            if back:
                needsmatching.append(back)
            url = entry.get("Mapping: Url")
            if url:
                needsmatching.append(url)
            for field in model["flds"]:
                if field["name"] in needsmatching:
                    needsmatching.remove(field["name"])
            if needsmatching:
                missing_fields[entry["Note type"]] = needsmatching
    errmsg = f"Invalid names in add-on '{addonname}' detected!\n\n"
    if missing_decks:
        errmsg += ('There are no decks with the following names in your collection: Fix the '
                "add-on config or it won't work:\n    %s\n\n" % 
                "\n    ".join(missing_decks))
    if missing_noteptyes:
        errmsg += ('There are no note types with the following names in your collection: Fix the '
                "add-on config or it won't work:\n    %s\n\n" % 
                "\n    ".join(missing_noteptyes))
    if missing_fields:
        errmsg += ("Some of the note types you set under 'Note type' don't have the fields you set "
                'in the config keys "Mapping: Title" or "Mapping: Content/Description/Summary". '
                "Fix the following values or the add-on won't work\n"
                '(note type name: ["non-existant field names you set", ])\n\n'
                "%s\n\n" 
                % pprint.pformat(missing_fields))
    if any([missing_decks, missing_noteptyes, missing_fields]):
        showInfo(errmsg)
        return False
    else:
        return True
mw.addonManager.setConfigUpdatedAction(__name__, is_valid_config)


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


def split_up_item(item, feed):
    title = item.title.text
    try:
        link = item.link.text  # TODO
    except:
        link = ""
    content = ""
    if feed == "rss":
        if not item.description is None:
            content = item.description.text
    if feed == "atom":
        if not item.content is None:
            content = item.content.text
        elif not item.summary is None:
            content = item.summary.text
    return title, link, content


def fill_note_fields(note, title, link, content, kw):
    field_title = kw["Mapping: Title"]
    field_content = kw["Mapping: Content/Description/Summary"]
    field_url = kw.get("Mapping: Url", "")
    for n, f in enumerate(note.model()["flds"]):
        fieldName = f["name"]
        if fieldName == field_title:
            tostrip = kw.get("Strip/Delete from Title")
            if tostrip:
                for entry in tostrip:
                    title = title.replace(entry, "")
            note.fields[n] = title
        if fieldName == field_content:
            tostrip = kw.get("Strip/Delete from Content/Description/Summary")
            if tostrip:
                for entry in tostrip:
                    content = content.replace(entry, "")
            if field_title == field_content:
                note.fields[n] += "<br><br>" + content
            else:
                note.fields[n] = content
        if field_url and fieldName == field_url:
            note.fields[n] = link
    return note


def process_one_item(item, kw, feed, tofill):
    global processed
    note = mw.col.newNote()
    title, link, content = split_up_item(item, feed)
    if not title:
        return False, False  # note, increasedups

    # duplicate check: check second field because sometimes the front is the 
    # same, e.g. for goodreads
    isduplicate = False
    if kw["Name"] in processed:
        for entry in processed[kw["Name"]]:
            if entry == [title, content]:
                isduplicate = True
                break
    if isduplicate:
        return False, True  # note, increasedups

    note = fill_note_fields(note, title, link, content, kw)
    processed.setdefault(kw["Name"], []).append([title, content])
    note.tags = kw['Tags']

    if note.dupeOrEmpty() == 2:
        note.tags.append("possible_duplicate")

    # make sure that a card for the note is generated.
    if not tofill:  # no note of the note type exists
        for f in note.fields:
            if not f:
                f = "."
    else:
        for i in tofill:
            if not note.fields[i]:
                note.fields[i] = "."
    
    return note, False  # note, increasedups


def process_one_feed(**kw):
    # get deck and model
    deck  = mw.col.decks.get(mw.col.decks.id(kw['Deck']))
    model = mw.col.models.byName(kw['Note type'])

    # assign model to deck
    mw.col.decks.select(deck['id'])
    mw.col.decks.get(deck)['mid'] = model['id']
    mw.col.decks.save(deck)

    # assign deck to model
    mw.col.models.setCurrent(model)
    mw.col.models.current()['did'] = deck['id']
    mw.col.models.save(model)

    # retrieve rss
    data, errmsg = getFeed(kw['Url'])
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

    tofill = fields_to_fill_for_nonempty_front_template(model["id"])
    for item in items:
        note, increasedups = process_one_item(item, kw, feed, tofill)
        if increasedups:
            dups += 1
        if not note:
            continue
        mw.col.addNote(note)
        if not tofill:  # now one note of the note type exists
            tofill = fields_to_fill_for_nonempty_front_template(model["id"])
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


# iterate feeds
def process_feeds():
    if not is_valid_config(gc()):
        return
    msg = ""
    mw.progress.start(immediate=True)
    feeds_info = gc('feeds_info')
    for i in range(len(feeds_info)):
        msg += feeds_info[i]["Deck"] + ":\n"
        msg += process_one_feed(**feeds_info[i]) + "\n"
    mw.progress.finish()
    showText(msg)


# create a new menu item
action = QAction("Feed to Anki", mw)
action.triggered.connect(process_feeds)
mw.form.menuTools.addAction(action)
