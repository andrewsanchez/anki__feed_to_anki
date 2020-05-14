**No support. No updates planned. Use this at your own risk.**


### Settings
For each feed you must set these settings: 

- `"Deck"`: the deck to which notes are added.
- `"Name"`: this value is used to detect already imported entries. Never change this value after
the first import from a feed. This key is used in case the feed url changes or you change the
deck name or you modify the already imported notes in your collection. So these can't be used
for detecting duplicates.
- `"Note type"`: The note type that is used for this feed.
- `"Mapping: Title"`, `"Mapping: Content/Description/Summary"`. The fields where the content is 
copied, e.g. "Mapping: Title": "Front", "Mapping: Content/Description/Summary": "Back".
- `"Strip/Delete from Title"`, `"Strip/Delete from Content/Description/Summary"`: You can set a 
list of entries that is removed from the content before the note is created. E.g. some feeds 
always include "most recent addition:" which I don't want to have in each note.
- `"Tags"`: the tags that are assigned for notes created from the respective feed.
- `"Url"`: the feed source.

**This add-on does not create decks, note types or fields on note types. If you set a non-existing**
**deck, note type or field the add-on won't work and instead inform you about the problem.** This
prevents that a typo or deck reorganization leads to unexpected results.

### Note about duplicates

This add-on stores all downloaded fields. This add-on ignores duplicates, i.e. notes that would
have exactly the same front and back will not be added. If only the front is identical the note
will be added. This is useful because for some feeds, e.g. from goodreads the front only consists
of "User John Miller shared a quote by Nietzsche" and it turns out that Nietzsche had more than
one good quote. But for fields that have the same front a tag "possible_duplicate" gets added.
