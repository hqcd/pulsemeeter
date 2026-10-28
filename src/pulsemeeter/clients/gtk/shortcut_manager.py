'''
Keyboard shortcut manager for PulseMeeter.
Supports:
1. Global system-wide shortcuts via XDG Desktop Portal GlobalShortcuts (org.freedesktop.portal.GlobalShortcuts)
2. Fallback X11 global keybinding (when Keybinder is available)
3. Window-level GTK4 ShortcutController / EventControllerKey for immediate in-app response
'''
import logging
import uuid
from typing import Callable

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

LOG = logging.getLogger("generic")

PORTAL_BUS_NAME = 'org.freedesktop.portal.Desktop'
PORTAL_OBJECT_PATH = '/org/freedesktop/portal/desktop'
GLOBAL_SHORTCUTS_IFACE = 'org.freedesktop.portal.GlobalShortcuts'
REQUEST_IFACE = 'org.freedesktop.portal.Request'


def gtk_accel_to_portal_trigger(accel: str) -> str:
    '''
    Convert a GTK accelerator string (e.g. '<Control><Alt>1') to an XDG Portal
    preferred_trigger string (e.g. 'CTRL+ALT+1').
    '''
    if not accel:
        return ''
    ok, keyval, mods = Gtk.accelerator_parse(accel)
    if not ok or keyval == 0:
        return accel
    parts = []
    if mods & gi.repository.Gdk.ModifierType.CONTROL_MASK:
        parts.append('CTRL')
    if mods & gi.repository.Gdk.ModifierType.ALT_MASK:
        parts.append('ALT')
    if mods & gi.repository.Gdk.ModifierType.SHIFT_MASK:
        parts.append('SHIFT')
    if mods & gi.repository.Gdk.ModifierType.SUPER_MASK:
        parts.append('LOGO')
    key_name = gi.repository.Gdk.keyval_name(keyval) or ''
    if key_name:
        parts.append(key_name)
    return '+'.join(parts)


class GlobalShortcutManager:
    '''
    Registers and listens for global and window-level shortcuts to toggle output routes.
    Action IDs use the format:
      - "route:{input_type}:{input_id}:{output_type}:{output_id}"
      - "toggle_group:{input_type}:{input_id}"
      - "mute:{device_type}:{device_id}"
    '''

    def __init__(self, on_trigger_callback: Callable[[str], None]):
        self.on_trigger_callback = on_trigger_callback
        self.shortcuts: dict[str, tuple[str, str]] = {}  # action_id -> (accel, description)
        self._window = None
        self._key_controller = None
        self._bus = None
        self._portal_proxy = None
        self._session_handle = None
        self._signal_sub_id = None
        self._init_portal()

    def _init_portal(self):
        try:
            self._bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            self._portal_proxy = Gio.DBusProxy.new_sync(
                self._bus,
                Gio.DBusProxyFlags.DO_NOT_AUTO_START,
                None,
                PORTAL_BUS_NAME,
                PORTAL_OBJECT_PATH,
                GLOBAL_SHORTCUTS_IFACE,
                None,
            )
            if self._portal_proxy.get_name_owner() is not None:
                self._signal_sub_id = self._bus.signal_subscribe(
                    PORTAL_BUS_NAME,
                    GLOBAL_SHORTCUTS_IFACE,
                    'Activated',
                    PORTAL_OBJECT_PATH,
                    None,
                    Gio.DBusSignalFlags.NONE,
                    self._on_portal_activated,
                )
                self._create_portal_session()
            else:
                self._portal_proxy = None
        except Exception:
            LOG.debug("XDG GlobalShortcuts portal not available; using window-level & CLI shortcuts")
            self._portal_proxy = None

    def _create_portal_session(self):
        if self._portal_proxy is None or self._bus is None:
            return
        try:
            token = f'pm_{uuid.uuid4().hex[:8]}'
            session_token = f'pm_sess_{uuid.uuid4().hex[:8]}'
            sender = self._bus.get_unique_name().lstrip(':').replace('.', '_')
            request_path = f'/org/freedesktop/portal/desktop/request/{sender}/{token}'

            def on_response(connection, sender_name, object_path, interface_name, signal_name, parameters):
                response_code, results = parameters.unpack()
                if response_code == 0 and 'session_handle' in results:
                    self._session_handle = results['session_handle']
                    self._bind_portal_shortcuts()

            self._bus.signal_subscribe(
                PORTAL_BUS_NAME,
                REQUEST_IFACE,
                'Response',
                request_path,
                None,
                Gio.DBusSignalFlags.NONE,
                on_response,
            )

            options = {
                'handle_token': GLib.Variant('s', token),
                'session_handle_token': GLib.Variant('s', session_token),
            }
            self._portal_proxy.call_sync(
                'CreateSession',
                GLib.Variant('(a{sv})', (options,)),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except Exception:
            LOG.debug("Failed to create XDG GlobalShortcuts session")

    def _bind_portal_shortcuts(self):
        if not self._portal_proxy or not self._session_handle or not self.shortcuts:
            return
        try:
            shortcut_list = []
            for action_id, (accel, description) in self.shortcuts.items():
                if not accel:
                    continue
                props = {
                    'description': GLib.Variant('s', description),
                    'preferred_trigger': GLib.Variant('s', gtk_accel_to_portal_trigger(accel)),
                }
                shortcut_list.append((action_id, props))

            if not shortcut_list:
                return

            token = f'pm_bind_{uuid.uuid4().hex[:8]}'
            options = {'handle_token': GLib.Variant('s', token)}
            self._portal_proxy.call(
                'BindShortcuts',
                GLib.Variant('(oa(sa{sv})sa{sv})', (self._session_handle, shortcut_list, '', options)),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
                None,
            )
        except Exception:
            LOG.debug("Failed to bind XDG GlobalShortcuts")

    def _on_portal_activated(self, connection, sender_name, object_path, interface_name, signal_name, parameters):
        try:
            _session_handle, shortcut_id, _timestamp, _options = parameters.unpack()
            if shortcut_id in self.shortcuts:
                GLib.idle_add(self.on_trigger_callback, shortcut_id)
        except Exception:
            LOG.exception("Error handling portal shortcut activation")

    def attach_to_window(self, window: Gtk.Window):
        '''
        Attach a key controller to the GTK window so configured shortcuts also work
        immediately when the window is focused.
        '''
        self._window = window
        self._key_controller = Gtk.EventControllerKey.new()
        self._key_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        self._key_controller.connect('key-pressed', self._on_window_key_pressed)
        window.add_controller(self._key_controller)

    def _on_window_key_pressed(self, controller, keyval, keycode, state):
        # Do not intercept keys when an Editable entry or Popover button is recording a shortcut
        if self._window is not None:
            focus_widget = self._window.get_focus()
            if isinstance(focus_widget, Gtk.Editable):
                return False

        mods = state & Gtk.accelerator_get_default_mod_mask()
        for action_id, (accel, _) in self.shortcuts.items():
            if not accel:
                continue
            ok, target_keyval, target_mods = Gtk.accelerator_parse(accel)
            if ok and target_keyval == keyval and target_mods == mods:
                self.on_trigger_callback(action_id)
                return True
        return False

    def sync_from_config(self, config_model):
        '''
        Rebuild the active shortcut map from all input connections and global shortcuts in ConfigModel.
        '''
        new_shortcuts: dict[str, tuple[str, str]] = {}

        for input_type in ('hi', 'vi'):
            for input_id, input_device in config_model.devices.get(input_type, {}).items():
                cycle_accel = getattr(input_device, 'toggle_group_shortcut', '')
                if cycle_accel:
                    cycle_action_id = f'toggle_group:{input_type}:{input_id}'
                    new_shortcuts[cycle_action_id] = (cycle_accel, f'Cycle toggle outputs on {input_device.nick}')
                for output_type in ('a', 'b'):
                    for output_id, conn in input_device.connections.get(output_type, {}).items():
                        accel = getattr(conn, 'shortcut', '')
                        if accel:
                            action_id = f'route:{input_type}:{input_id}:{output_type}:{output_id}'
                            desc = f'Toggle {input_device.nick} -> {conn.nick}'
                            new_shortcuts[action_id] = (accel, desc)

        for action_id, accel in getattr(config_model, 'shortcuts', {}).items():
            if accel:
                new_shortcuts[action_id] = (accel, f'PulseMeeter {action_id}')

        self.shortcuts = new_shortcuts
        self._bind_portal_shortcuts()
