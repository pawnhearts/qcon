#!/usr/bin/python

__VERSION__ = '2.6'
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
import configparser
from subprocess import Popen, PIPE

CONFIG_SAMPLE = """
[xterm]
Position-x: center
Position-y: top
Width: 100
Height: 40
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
Width: 40
Height: 40
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

    __instances__ = set()

    def __init__(self, name):
        self.name = name
        self.spawn_process()
        Keybinder.bind(conf.get(self.name, 'Key'), self.on_key_press)
        Process.__instances__.add(self)

    def spawn_process(self):
        os.chdir(os.path.expanduser('~'))
        ps = Popen(shlex.split(conf.get(self.name, 'Command')), stdout=PIPE, stdin=PIPE)
        self.pid = ps.pid
        GObject.child_watch_add(self.pid, self.on_child_exit, self)
        GObject.timeout_add(100, self._search_window)

    def _search_window(self):
        if conf.has_option(self.name, 'instance'):
             for win in scr.get_windows():
                 if win.get_class_instance_name() == conf.get(self.name, 'instance'):
                     if conf.has_option(self.name, 'class'):
                         if win.get_class_group_name() != conf.get(self.name, 'class'):
                             continue
                     self.window = win
                     self.setup_window()
                     return False

        for win in scr.get_windows():
            if win.get_pid() == self.pid:
                self.window = win
                self.setup_window()
                return False
        return True

    def setup_window(self):
        self.x11window = GdkX11.X11Window.foreign_new_for_display(GdkX11.X11Display.get_default(),
                                                                  self.window.get_xid())
        # func = Gdk.WMFunction.ALL
        # for k, v in conf.defaults().items():
        #     if k.startswith('WM_'):
        #         func = func | getattr(Gdk.WMFunction,v[3:])
        # self.x11window.set_functions(func)
        # func = Gdk.WMDecoration.ALL
        # for k, v in conf.defaults().items():
        #     if k.startswith('DEC_'):
        #         func = func | getattr(Gdk.WMDecoration,v[4:])
        # self.x11window.set_decorations(func)

        self.x11window.set_opacity(conf.getfloat(self.name, 'Opacity'))
        Wnck.Screen.get_default().connect('active_window_changed', self.on_hide_inactive)
        self.setup_geometry()
        self.window.stick()
        if conf.getboolean(self.name, 'StartHidden'):
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
        if scr.get_active_window() == self.window:
            self.hide()
        else:
            self.activate()

    def on_hide_inactive(self, screen, window):
        if conf.getboolean(self.name, 'HideWhenLosesFocus'):
            if window == self.window:
                if screen.get_active_window().get_group_leader() == window.get_group_leader():
                    return
                self.hide()

    def on_child_exit(self, pid, errcode, proc):
        Keybinder.unbind(conf.get(proc.name, 'KEY'))
        Process.__instances__.remove(proc)
        if errcode != 0:
            raise OSError('Terminal {} crashed'.format(self.name))
        if conf.getboolean(self.name, 'Restart'):
            Process(self.name)
            del self
        else:
            sys.exit()

    def restart(self):
        Process.__instances__.remove(self)
        Process(self.name)
        del self

    def setup_geometry(self):
        if conf.getboolean(self.name, 'Decorations'):
            dec = Gdk.WMDecoration.TITLE | Gdk.WMDecoration.BORDER
            self.x11window.set_decorations(dec)
        else:
            self.x11window.set_decorations(Gdk.WMDecoration.BORDER)

        # BORDER, TITLE, MINIMIZE, MENU, RESIZEH, MAXIMIZE

        fun = Gdk.WMFunction.ALL
        functions = {'Movable': Gdk.WMFunction.MOVE,
             'Minimizable': Gdk.WMFunction.MINIMIZE,
             'Maximizable': Gdk.WMFunction.MAXIMIZE,
             'Resizable': Gdk.WMFunction.RESIZE}
        for k, v in functions.items():
            if  not conf.getboolean(self.name, k):
                fun = fun | v
        self.x11window.set_functions(fun)



        if conf.get(self.name, 'Width').endswith('%'):
            w = scr.get_width() / 100.0 * int(conf.get(self.name, 'Width').rstrip('%'))
        else:
            w = conf.getint(self.name, 'Width')
        if conf.get(self.name, 'Height').endswith('%'):
            h = scr.get_height() / 100.0 * int(conf.get(self.name, 'Height').rstrip('%'))
        else:
            h = conf.getint(self.name, 'Height')
        x = conf.getint(self.name, 'Offset-x')
        if conf.get(self.name, 'Position-x').lower() == 'right':
            x = scr.get_width() - x - w
        if conf.get(self.name, 'Position-x').lower() == 'center':
            x = scr.get_width() / 2 - (w / 2) + x
        y = conf.getint(self.name, 'Offset-y')
        if conf.get(self.name, 'Position-y').lower() == 'bottom':
            y = scr.get_height() - y -h
        if conf.get(self.name, 'Position-y').lower() == 'center':
            y = scr.get_height() / 2 - (h / 2) + y
        self.x11window.move(x, y)
        self.x11window.resize(w, h)
        # self.window.set_geometry(Wnck.WindowGravity.STATIC, Wnck.WindowMoveResizeMask.X | Wnck.WindowMoveResizeMask.Y | Wnck.WindowMoveResizeMask.WIDTH | Wnck.WindowMoveResizeMask.HEIGHT, x, y, w, h)


def make_menu():
    menu = Gtk.Menu()
    item_save = Gtk.MenuItem("Save window")
    item_save.connect('activate', save_window)
    menu.append(item_save)
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
    #os.kill(os.getsid(os.getpid()), signal.SIGKILL)
    for proc in Process.__instances__:
        try:
            os.kill(proc.pid, signal.SIGKILL)
        except:
            pass


def kill_other_copies():
    os.system(r"ps aux|grep qcon.py|grep -v %s|awk '{print $2}'|xargs kill -7" % os.getpid())

def save_window(*args):
    win = scr.get_active_window()
    x11window = GdkX11.X11Window.foreign_new_for_display(GdkX11.X11Display.get_default(),
                                                                  win.get_xid())
    section = win.get_class_group_name()
    if not conf.has_section(section):
        conf.add_section(section)
    conf.set(section, 'Class', win.get_class_group_name())
    conf.set(section, 'Instance', win.get_class_instance_name())
    conf.set(section, 'Command', open('/proc/{}/cmdline'.format(win.get_pid())).read().strip())
    conf.set(section, 'Offset-x', str(x11window.get_position()[0]))
    conf.set(section, 'Offset-y', str(x11window.get_position()[1]))
    conf.set(section, 'Width', str(x11window.get_width()))
    conf.set(section, 'Height', str(x11window.get_height()))
    conf.write(open(os.path.expanduser("~/.qconrc"), 'w'))



def restart():
    kill_other_copies()
    os.execv(sys.executable, ['python'] + sys.argv)

#if __name__ == '__main__':
if not os.path.exists(os.path.expanduser('~/.qconrc')):
    open(os.path.expanduser('~/.qconrc'), 'w').write(CONFIG_SAMPLE)
    print "Default ~/.qconrc has been written, modify it according to your needs and run again"
    sys.exit()
kill_other_copies()
ConfigDefaults = {
'Position-x': 'left',
'Position-y': 'top',
'Offset-x': '0',
'Offset-y': '0',
'StartHidden': '0',
'Restart': 'true',
'HideWhenLosesFocus': 'true',
'Decorations': 'true',
'Opacity': '1.0',
'Movable': '1',
'Resizable': '1',
'Minimizable': '1',
'Maximizable': '1',
}
scr = Wnck.Screen.get_default()
conf = configparser.SafeConfigParser(defaults=ConfigDefaults, interpolation=None)
conf.read(os.path.expanduser('~/.qconrc'))
signal.signal(signal.SIGINT, signal.SIG_DFL)
signal.signal(signal.SIGHUP, restart)
atexit.register(kill_children)
Keybinder.init()
indicator = AppIndicator3.Indicator.new('qcon', 'qcon', AppIndicator3.IndicatorCategory.OTHER)
indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
indicator.set_menu(make_menu())
indicator.set_icon('utilities-terminal')
for section in conf.sections():
    Process(section)
Gtk.main()

