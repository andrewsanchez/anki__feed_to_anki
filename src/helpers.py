from aqt import mw

def fields_to_fill_for_nonempty_front_template(mid):
    # doesn't analyze the templates, just returns the card with the least number of fields
    # filled.
    # TODO: improv this ...
    wco = mw.col.findCards("mid:%s card:1" %mid)
    if not wco:  # no note of the note type exists
        return False
    totalcards = {}
    for cid in wco:
        card = mw.col.getCard(cid)
        totalcards.setdefault(card.nid, 0)
        totalcards[card.nid] += 1
    nid_filled_map = {}
    for nid, number_of_cards in totalcards.items():
        if number_of_cards == 1:
            othernote = mw.col.getNote(nid)
            nid_filled_map[nid] = 0
            for f in othernote.fields:
                if f:
                    nid_filled_map[nid] += 1
    lowestnid = min(nid_filled_map, key=nid_filled_map.get)
    othernote = mw.col.getNote(lowestnid)
    tofill = []
    for idx, cont in enumerate(othernote.fields):
        if cont:
            tofill.append(idx)
    return tofill