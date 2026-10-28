import gettext

from pulsemeeter.clients.gtk.widgets.popovers.edit_connection_widget import ConnectionSettingsPopup
from pulsemeeter.clients.gtk.widgets.common.volume_widget import VolumeWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject, Pango  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class ConnectionWidget(Gtk.Box):

    __gsignals__ = {
        'connection': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        'route_volume': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (int,)),
        'use_loopback': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, (bool,)),
        'settings_pressed': (GObject.SignalFlags.RUN_FIRST, GObject.TYPE_NONE, ()),
    }

    def __init__(self, label: str, connection_model, input_type: str = None, output_type: str = None, *args, **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, *args, **kwargs)
        self.set_hexpand(True)
        self.connection_model = connection_model
        self.input_type = input_type
        self.output_type = output_type

        # Warning icon shown when route fails to set up
        self.warning_icon = Gtk.Image.new_from_icon_name('dialog-warning')
        is_exclusive = bool(getattr(connection_model, 'toggle_group', False) or getattr(connection_model, 'exclusive_source', False))
        self.toggle_group_icon = Gtk.Image.new_from_icon_name('media-playlist-repeat-symbolic')
        self.toggle_group_icon.set_visible(is_exclusive)

        # Info icon shown when automatic mapping paired channels by order
        self.info_icon = Gtk.Image.new_from_icon_name('dialog-information')

        # Toggle button with [warning_icon | info_icon | toggle_group_icon | label] as its content
        toggle_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4, halign=Gtk.Align.CENTER, hexpand=True)
        toggle_content.append(self.warning_icon)
        toggle_content.append(self.info_icon)
        toggle_content.append(self.toggle_group_icon)
        self.label_widget = Gtk.Label(label=label)
        self.label_widget.set_wrap(True)
        self.label_widget.set_wrap_mode(Pango.WrapMode.WORD)
        self.label_widget.set_justify(Gtk.Justification.CENTER)
        self.label_widget.set_hexpand(True)
        toggle_content.append(self.label_widget)
        self.toggle_button = Gtk.ToggleButton(active=connection_model.state)
        self.toggle_button.set_hexpand(True)
        if is_exclusive:
            self.toggle_button.add_css_class('toggle-group-member')
        self.toggle_button.set_child(toggle_content)
        self._toggle_handler_id = self.toggle_button.connect('toggled', self._on_toggled)

        # Right-click gesture for connection settings popup
        gesture = Gtk.GestureClick.new()
        gesture.set_button(3)
        gesture.connect("pressed", self._on_pressed)
        self.popover = ConnectionSettingsPopup(connection_model, input_type=input_type, output_type=output_type)
        self.popover.set_parent(self.toggle_button)
        self.toggle_button.add_controller(gesture)

        # Checkbox for use_loopback opt-in
        self.loopback_check = Gtk.CheckButton(active=connection_model.use_loopback)
        self.loopback_check.set_tooltip_text(_('Enable per-route volume (uses pw-loopback)'))
        self._loopback_handler_id = self.loopback_check.connect('toggled', self._on_loopback_toggled)

        # Volume slider for route volume
        self.volume_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.volume_scale.set_range(0, 153)
        self.volume_scale.set_increments(1, 5)
        self.volume_scale.set_digits(0)
        self.volume_scale.set_value(connection_model.route_volume)
        self.volume_scale.set_hexpand(True)
        self.volume_scale.set_size_request(60, -1)
        self.volume_scale.add_mark(100, Gtk.PositionType.TOP, '')
        self.volume_scale.set_tooltip_text(_('Route volume'))
        self._volume_handler_id = self.volume_scale.connect('value-changed', self._on_volume_changed)

        scroll_controller = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
        scroll_controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        scroll_controller.connect('scroll', self._on_volume_scroll)
        self.volume_scale.add_controller(scroll_controller)

        # Pack widgets
        self.append(self.toggle_button)
        self.append(self.loopback_check)
        self.append(self.volume_scale)

        # Initial visibility. set_accessible() must run before update_warning()
        # because it sets a default tooltip on the toggle button - update_warning
        # then overrides that tooltip with the error message when failed.
        self.set_visible(not bool(getattr(connection_model, 'hidden', False)))
        self._update_visibility()
        self.set_accessible()
        self.update_warning()

    def set_accessible(self):
        description_label = _('Connect to %s, right click to open connection settings') % self.connection_model.nick
        extras = []
        if getattr(self.connection_model, 'toggle_group', False):
            extras.append(_('Exclusive Toggle'))
        if getattr(self.connection_model, 'exclusive_source', False):
            extras.append(_('Exclusive Virtual Output'))
        shortcut = getattr(self.connection_model, 'shortcut', '')
        if shortcut:
            extras.append(_('Shortcut: %s') % ConnectionSettingsPopup._format_shortcut(shortcut))
        if extras:
            description_label += f" ({', '.join(extras)})"
        self.toggle_button.set_tooltip_text(description_label)
        Gtk.Accessible.update_property(self.toggle_button, [Gtk.AccessibleProperty.DESCRIPTION], [description_label])
        Gtk.Accessible.update_property(self.toggle_button, [Gtk.AccessibleProperty.HAS_POPUP], [True])

    def update_metadata_visuals(self):
        is_toggle = bool(getattr(self.connection_model, 'toggle_group', False) or getattr(self.connection_model, 'exclusive_source', False))
        self.toggle_group_icon.set_visible(is_toggle)
        if is_toggle:
            self.toggle_button.add_css_class('toggle-group-member')
        else:
            self.toggle_button.remove_css_class('toggle-group-member')
        self.set_visible(not bool(getattr(self.connection_model, 'hidden', False)))
        self.update_warning()

    def _on_volume_scroll(self, controller, dx, dy):
        if not VolumeWidget.scroll_enabled:
            return True
        return False

    def _update_visibility(self):
        '''Update visibility of checkbox and slider based on connection state and loopback flag.'''
        is_connected = self.toggle_button.get_active()
        use_loopback = self.loopback_check.get_active()
        self.loopback_check.set_visible(is_connected)
        self.volume_scale.set_visible(is_connected and use_loopback)

    def update_warning(self):
        """
        Show warning when this route has a real failure, or links only part of its channels.
        Show info when automatic mapping had to pair channels by order.
        """
        problem = self.connection_model.error_text() or self.connection_model.warning_text()
        order = self.connection_model.order_text()
        self.warning_icon.set_visible(bool(problem))
        self.info_icon.set_visible(not problem and bool(order))
        if problem or order:
            self.toggle_button.set_tooltip_text(problem or order)
        else:
            self.set_accessible() # Restores normal tooltip

    def _on_toggled(self, widget):
        self._update_visibility()
        self.emit('connection', widget.get_active())
        self.update_warning()

    def _on_loopback_toggled(self, widget):
        self._update_visibility()
        self.emit('use_loopback', widget.get_active())
        self.update_warning()

    def _on_volume_changed(self, widget):
        self.emit('route_volume', int(widget.get_value()))

    def _on_pressed(self, _, __, ___, ____):
        self.popover.popup()
        self.emit('settings_pressed')

    def set_connection(self, state):
        self.toggle_button.handler_block(self._toggle_handler_id)
        self.toggle_button.set_active(state)
        self._update_visibility()
        self.toggle_button.handler_unblock(self._toggle_handler_id)

    def set_route_volume(self, value):
        self.volume_scale.handler_block(self._volume_handler_id)
        self.volume_scale.set_value(value)
        self.volume_scale.handler_unblock(self._volume_handler_id)

    def set_use_loopback(self, state):
        self.loopback_check.handler_block(self._loopback_handler_id)
        self.loopback_check.set_active(state)
        self._update_visibility()
        self.loopback_check.handler_unblock(self._loopback_handler_id)
