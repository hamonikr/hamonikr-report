import os
import gettext
import gi
import subprocess

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from hamonikrreport import InfoReport, InfoReportAction

class Report(InfoReport):

    def __init__(self):

        gettext.install("hamonikr-report", "/usr/share/locale", names="ngettext")

        self.title = _("Install multimedia codecs")
        self.icon = "applications-multimedia-symbolic"
        self.has_ignore_button = True

    def is_pertinent(self):
        # Defines whether this report should show up
        installed_codecs_pkg = subprocess.getoutput("dpkg-query -W --showformat='${db:Status-Status}' mint-meta-codecs 2>&1")
        if str(installed_codecs_pkg) == "installed":
            return False
        else:
            return True

    def get_descriptions(self):
        # Return the descriptions
        descriptions = []
        descriptions.append(_("Multimedia codecs are required to play some video formats and to properly render some websites."))
        return descriptions

    def get_actions(self):
        # Return available actions
        actions = []
        action = InfoReportAction(label=_("Install the Multimedia Codecs"), callback=self.callback)
        action.set_style(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        actions.append(action)
        return actions

    def callback(self, data):
        if os.path.exists("/usr/share/doc/debian-system-adjustments/copyright"):
            # LMDE 6
            self.install_packages(["mint-meta-codecs", "libavcodec-extra", "libavcodec-extra59"])
        else:
            self.install_packages(["mint-meta-codecs", "libavcodec-extra", "libavcodec-extra60"])
        # reload
        return True

if __name__ == "__main__":
    report = Report()
    print(report.is_pertinent())
