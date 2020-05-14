import os

from aqt import mw

addon_path = os.path.dirname(__file__)
user_files_folder = os.path.join(addon_path, "user_files")
already_downloaded_pickle = os.path.join(user_files_folder, "already_downloaded.pypickle")


def gc(arg=None, fail=False):
    conf = mw.addonManager.getConfig(__name__)
    if conf:
        if arg:
            return conf.get(arg, fail)
        else:
            return conf
    else:
        return fail