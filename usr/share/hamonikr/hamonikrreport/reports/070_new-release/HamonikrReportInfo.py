import configparser
import os
import subprocess
import gettext
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from hamonikrreport import InfoReport, InfoReportAction

class Report(InfoReport):

    def __init__(self):

        gettext.install("hamonikrreport", "/usr/share/locale", names="ngettext")

        self.title = _("A new version of HamoniKR OS is available")
        self.icon = "mintupdate-type-package-symbolic"
        self.has_ignore_button = True

    def is_pertinent(self):
        # Defines whether this report should show up
        self.rel_target = None
        rel_edition = None
        rel_codename = None
        rel_relno = None
        if os.path.exists("/etc/hamonikr/info"):
            with open("/etc/hamonikr/info", encoding="utf-8") as info:
                for line in info:
                    line = line.strip()
                    if "EDITION=" in line:
                        rel_edition = line.split('=')[1].replace('"', '').split()[0]
                    if "CODENAME=" in line:
                        rel_codename = line.split('=')[1].replace('"', '').split()[0]
                    if "RELEASE=" in line:
                        rel_relno = line.split('=')[1].replace('"', '').split()[0]                        
        # When there is a new version of the code name
        if rel_edition is not None and rel_codename is not None:
            rel_path = "/usr/share/hamonikr-upgrade-info/%s/info" % rel_codename
            if os.path.exists(rel_path):
                config = configparser.ConfigParser()
                config.read(rel_path)
                if rel_edition.lower() in config['general']['editions']:
                    self.rel_target = config['general']['target_name']
                    return True
        return False

    def get_descriptions(self):
        # Return the descriptions
        descriptions = []
        descriptions.append(_("Visit %s for the latest announcements.") % "<a href='https://hamonikr.org'>https://hamonikr.org</a>")
        return descriptions

    def get_actions(self):
        # Return available actions
        actions = []
        action = InfoReportAction(label=_("Upgrade to %s") % self.rel_target, callback=self.callback)
        action.set_style(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        actions.append(action)
        return actions

    def callback(self, data):
        # real command : /usr/lib/linuxmint/mintUpdate/rel_upgrade.py
        subprocess.run(["/usr/bin/mint-release-upgrade"])
        
        # To upgrade the Harmonica OS to the next version
        # First, run Linux Mint's release upgrade 
        # If there is something to do for HamoniKR, run it here

        # reload
        return True

if __name__ == "__main__":
    report = Report()
    print(report.is_pertinent())
