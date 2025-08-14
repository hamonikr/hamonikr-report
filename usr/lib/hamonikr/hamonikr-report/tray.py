#!/usr/bin/python3
import gettext
import gi
import locale
import os
import setproctitle
import subprocess
import xapp.os

gi.require_version("Gtk", "3.0")
gi.require_version('XApp', '1.0')
from gi.repository import Gtk, Gdk, Gio, XApp, GLib

from common import idle, InfoReportContainer, INFO_DIR

setproctitle.setproctitle("hamonikr-report-tray")

# i18n
APP = 'hamonikr-report'
LOCALE_DIR = "/usr/share/locale"
locale.bindtextdomain(APP, LOCALE_DIR)
gettext.bindtextdomain(APP, LOCALE_DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class GtkStatusIcon(Gtk.StatusIcon):

    def __init__(self):
        Gtk.StatusIcon.__init__(self)

    def set_secondary_menu(self, menu):
        pass

    def set_icon_name(self, icon_name):
        self.set_from_icon_name(icon_name)



class MyApplication(Gtk.Application):
    # Main initialization routine
    def __init__(self, application_id, flags):
        Gtk.Application.__init__(self, application_id=application_id, flags=flags)
        self.connect("activate", self.activate)

        self.settings = Gio.Settings(schema_id="com.hamonikr.report")

        # Status icon
        self.menu = Gtk.Menu()
        menuItem = Gtk.MenuItem.new_with_label(_("Show System Reports"))
        menuItem.connect('activate', self.on_menu_show)
        self.menu.append(menuItem)
        self.menu.append(Gtk.SeparatorMenuItem())
        menuItem = Gtk.MenuItem.new_with_label(_("Quit"))
        menuItem.connect('activate', self.on_menu_quit)
        self.menu.append(menuItem)
        self.menu.show_all()

        try:
            self.status_icon = XApp.StatusIcon()
            self.status_icon.set_name("hamonikr-report")
            self.status_icon.connect("activate", self.on_statusicon_activated)
            self.status_icon.set_secondary_menu(self.menu)
        except Exception as e:
            print("Couldn't instantiate XApp.StatusIcon: %s" % e)
            self.status_icon = GtkStatusIcon()
            self.status_icon.connect("activate", self.on_gtk_statusicon_activated)
            self.status_icon.connect("popup-menu", self.on_gtk_statusicon_popup)
        self.status_icon.set_visible(False)

    def on_statusicon_activated(self, icon, button, time):
        if button == Gdk.BUTTON_PRIMARY:
            GLib.spawn_async(["/usr/bin/hamonikr-report"])
            self.status_icon.set_visible(False)

    def on_gtk_statusicon_activated(self, status_icon):
        self.on_statusicon_activated(status_icon, Gdk.BUTTON_PRIMARY, None)

    def on_gtk_statusicon_popup(self, status_icon, button, time):
        self.menu.popup(None, None, None, None, button, time)

    def on_menu_show(self, widget):
        GLib.spawn_async(["/usr/bin/hamonikr-report"])

    def on_menu_quit(self, widget):
        self.quit()

    def activate(self, application):
        if not hasattr(self, "primary_instance"):
            self.hold()
            self.primary_instance = "Primary instance"
            self.load_info()
            # Auto-refresh
            if self.settings.get_boolean("autorefresh"):
                GLib.timeout_add_seconds(self.settings.get_int("autorefresh-seconds"), self.load_info)
        else:
            print("Already running!")

    def load_info(self):
        found_pertinent_report = False
        security_status = "GREEN"  # 기본값: 양호 상태
        
        # 보안 점검 상태 확인
        try:
            from security_check import SecurityChecker
            security_checker = SecurityChecker()
            security_status = security_checker.get_security_status()
        except Exception as e:
            print(f"Failed to check security status: {e}")
        
        if os.path.exists(INFO_DIR):
            ignored_paths = self.settings.get_strv("ignored-reports")
            for dir_name in sorted(os.listdir(INFO_DIR)):
                path = os.path.join(INFO_DIR, dir_name)
                uuid = dir_name.split("_")[-1]
                if uuid not in ignored_paths:
                    try:
                        report = InfoReportContainer(uuid, path)
                        if report.instance.is_pertinent():
                            found_pertinent_report = True
                    except Exception as e:
                        print("Failed to load report %s: 
%s
" % (dir_name, e))

        # 아이콘 및 툴팁 설정
        if found_pertinent_report:
            self.status_icon.set_visible(True)
            
            # 보안 상태에 따른 아이콘 설정
            if security_status == "RED":
                self.status_icon.set_icon_name("hamonikr-report-security-critical")
                tooltip_text = _("Critical security issues detected!")
            elif security_status == "YELLOW":
                self.status_icon.set_icon_name("hamonikr-report-security-warning")
                tooltip_text = _("Security warnings found - please review")
            else:
                self.status_icon.set_icon_name("hamonikr-report-security-good")
                tooltip_text = _("Security status is good")
            
            # 다른 보고서가 있는 경우 기본 메시지 추가
            other_reports_exist = False
            for dir_name in sorted(os.listdir(INFO_DIR)):
                path = os.path.join(INFO_DIR, dir_name)
                uuid = dir_name.split("_")[-1]
                if uuid not in ignored_paths:
                    try:
                        report = InfoReportContainer(uuid, path)
                        if report.instance.is_pertinent():
                            other_reports_exist = True
                            break
                    except:
                        pass
            
            if other_reports_exist:
                tooltip_text += " - " + _("Other system reports also require attention")
            
            self.status_icon.set_tooltip_text(tooltip_text)
        else:
            self.status_icon.set_visible(False)

        return True

if __name__ == "__main__":
    if ((not xapp.os.is_live_session()) and (not xapp.os.is_guest_session())):
        application = MyApplication("com.hamonikr.reports-tray", Gio.ApplicationFlags.FLAGS_NONE)
        application.run()
