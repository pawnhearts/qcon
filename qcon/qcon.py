#!/usr/bin/python

__VERSION__ = '2.5'
__LICENSE__ = 'MIT'
__URL__ = 'https://github.com/pawnhearts/qcon/'

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Wnck', '3.0')
gi.require_version('Keybinder', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, Gdk, Wnck, GdkX11, GObject, Keybinder, AppIndicator3
import sys, os, signal, atexit, shlex
import ConfigParser
from subprocess import Popen, PIPE

CONFIG_SAMPLE = """
[xterm]
Position-x: center
Position-y: top
Width: 100%
Height: 400
Offset-x: 0
Offset-y: 0
Key: F12
Command: sakura
StartHidden: true
Restart: true
HideWhenLosesFocus: true
Decorations: false
Opacity: 0.7
[top]
Position-x: right
Position-y: bottom
Width: 400
Height: 400
Offset-x: 0
Offset-y: 0
Key: <ctrl>F11
Command: xterm -e top
StartHidden: true
Restart: false
HideWhenLosesFocus: true
Decorations: true
Opacity: 0.7
"""




def find_term():
    terms = ['mate-terminal', 'konsole', 'xfce4-terminal', 'sakura', 'urxvt', 'mrxvt', 'rxvt', 'xterm', 'terminator',
             'eterm', 'aterm']
    for t in terms:
        if os.system('which {} >/dev/null 2>/dev/null'.format(t)) == 0:
            return t


class Process(object):

    def __init__(self, name):
        self.name = name
        self.spawn_process()
        Keybinder.bind(Config.get(self.name, 'Key'), self.on_key_press)

    def spawn_process(self):
        os.chdir(os.path.expanduser('~'))
        ps = Popen(shlex.split(Config.get(self.name, 'Command')), stdout=PIPE, stdin=PIPE)
        self.pid = ps.pid
        GObject.child_watch_add(self.pid, self.on_child_exit)
        GObject.timeout_add(100, self._search_window)

    def _search_window(self):
        if not is_process_running(self.pid):
            raise OSError('Child process for {} died'.format(self.name))
        scr = Wnck.Screen.get_default()
        for win in scr.get_windows():
            if win.get_pid() == self.pid:
                self.window = win
                self.setup_window()
                return False
        return True

    def setup_window(self):
        self.x11window = GdkX11.X11Window.foreign_new_for_display(GdkX11.X11Display.get_default(),
                                                                  self.window.get_xid())
        self.x11window.set_functions(Gdk.WMFunction.RESIZE|Gdk.WMFunction.MINIMIZE|Gdk.WMFunction.CLOSE)
        self.x11window.set_opacity(Config.getfloat(self.name, 'Opacity'))
        Wnck.Screen.get_default().connect('active_window_changed', self.on_hide_inactive)
        self.setup_geometry()
        self.window.stick()
        if Config.getboolean(self.name, 'StartHidden'):
            self.hide()

    def on_key_press(self, *args):
        self.toggle()

    def activate(self):
        if not getattr(self, 'window', None):
            return
        self.window.activate(GdkX11.x11_get_server_time(self.x11window))
        self.window.set_skip_tasklist(False)
        self.window.set_skip_pager(False)
        self.window.make_above()
        # self.setup_geometry()

    def hide(self):
        if not getattr(self, 'window', None):
            return
        self.window.minimize()
        self.x11window.iconify()
        self.window.set_skip_tasklist(True)
        self.window.set_skip_pager(True)

    def toggle(self):
        if not getattr(self, 'window', None):
            return
        scr = Wnck.Screen.get_default()
        if scr.get_active_window() == self.window:
            self.hide()
        else:
            self.activate()

    def on_hide_inactive(self, screen, window):
        if Config.getboolean(self.name, 'HideWhenLosesFocus'):
            if window == self.window:
                self.hide()

    def on_child_exit(self, pid, errcode):
        if errcode != 0:
            raise OSError('Terminal {} crashed'.format(self.name))
        if Config.getboolean(self.name, 'Restart'):
            Process(self.name)
            del self
        else:
            sys.exit()

    def setup_geometry(self):
        if Config.getboolean(self.name, 'Decorations'):
            self.x11window.set_decorations(Gdk.WMDecoration.MINIMIZE | Gdk.WMDecoration.TITLE | Gdk.WMDecoration.BORDER)
        else:
            self.x11window.set_decorations(0)

        if not Config.getboolean(self.name, 'Decorations'):
            self.x11window.set_functions(Gdk.WMFunction.CLOSE | Gdk.WMFunction.MINIMIZE | Gdk.WMFunction.RESIZE)
        # BORDER, TITLE, MINIMIZE, MENU, RESIZEH, MAXIMIZE
        scr = Wnck.Screen.get_default()
        if Config.get(self.name, 'Width').endswith('%'):
            w = scr.get_width() / 100.0 * int(Config.get(self.name, 'Width').rstrip('%'))
        else:
            w = Config.getint(self.name, 'Width')
        if Config.get(self.name, 'Height').endswith('%'):
            h = scr.get_height() / 100.0 * int(Config.getint(self.name, 'Height').rstrip('%'))
        else:
            h = Config.getint(self.name, 'Height')
        x = Config.getint(self.name, 'Offset-x')
        if Config.get(self.name, 'Position-x').lower() == 'right':
            x = scr.get_width() - x - w
        if Config.get(self.name, 'Position-x').lower() == 'center':
            x = scr.get_width() / 2 - (w / 2) + x
        y = Config.getint(self.name, 'Offset-y')
        if Config.get(self.name, 'Position-y').lower() == 'bottom':
            y = scr.get_height() - y -h
        if Config.get(self.name, 'Position-y').lower() == 'center':
            y = scr.get_height() / 2 - (h / 2) + y
        self.x11window.move(x, y)
        self.x11window.resize(w, h)
        # self.window.set_geometry(Wnck.WindowGravity.STATIC, Wnck.WindowMoveResizeMask.X | Wnck.WindowMoveResizeMask.Y | Wnck.WindowMoveResizeMask.WIDTH | Wnck.WindowMoveResizeMask.HEIGHT, x, y, w, h)


def make_menu():
    menu = Gtk.Menu()
    item_restart = Gtk.MenuItem("Restart")
    item_restart.connect('activate', restart)
    menu.append(item_restart)
    item_quit = Gtk.MenuItem("Quit")
    item_quit.connect('activate', Gtk.main_quit)
    menu.append(item_quit)
    menu.show_all()
    return menu


def is_process_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def kill_children():
    os.kill(os.getsid(os.getpid()), signal.SIGTERM)


def kill_other_copies():
    os.system(r'ps aux|grep qcon.py|grep -v %s|awk "{print $2}"|xargs kill -7' % os.getpid())


def restart():
    kill_other_copies()
    os.execv(sys.executable, ['python'] + sys.argv)


if __name__ == '__main__':
    if not os.path.exists(os.path.expanduser('~/.qconrc')):
        open(os.path.expanduser('~/.qconrc'), 'w').write(CONFIG_SAMPLE)
        print "Default ~/.qconrc has been written, modify it according to your needs and run again"
        sys.exit()
    kill_other_copies()
    Config = ConfigParser.ConfigParser()
    Config.read(os.path.expanduser('~/.qconrc'))
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGHUP, restart)
    atexit.register(kill_children)
    Keybinder.init()
    indicator = AppIndicator3.Indicator.new('qcon', 'qcon', AppIndicator3.IndicatorCategory.OTHER)
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
    indicator.set_menu(make_menu())
    indicator.set_icon('utilities-terminal')
    for section in Config.sections():
        Process(section)
    Gtk.main()
