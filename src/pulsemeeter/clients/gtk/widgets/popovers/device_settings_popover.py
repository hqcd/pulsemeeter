import gettext

from pulsemeeter.schemas import pulse_mappings
from pulsemeeter.clients.gtk.widgets.utils.input_widget import InputWidget
from pulsemeeter.clients.gtk.widgets.utils.icon_button_widget import IconButton
from pulsemeeter.clients.gtk.widgets.utils.popover_utils import dismiss_on_outside_click
from pulsemeeter.clients.gtk.widgets.common.dropdown_widget import LabeledDropDown
from pulsemeeter.clients.gtk.widgets.common.port_selector_widget import PortSelector

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class DeviceSettingsPopover(Gtk.Popover):
    '''

    '''
    def __init__(self, device_type, edit=False):
        super().__init__()
        self.device_type = device_type
        self.edit = edit
        self._recording_shortcut = False
        self._current_shortcut = ''

        self.nick_widget = InputWidget(_('Nick: '), tooltip=_('Enter a nickname for the device'))
        self.name_widget = InputWidget(_('Name: '), tooltip=_('Enter a name for the device'))
        self.external_widget = Gtk.CheckButton(label=_('Externally Managed'))
        self.external_widget.set_tooltip_text(
            _("Check this if another application or config file owns this device's lifecycle (creates and destroys it), "
              "such as a PipeWire config or EasyEffects. Pulsemeeter will route and control the device but will not create it on "
              "startup or remove it on exit.")
        )

        self.shortcut_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, margin_top=4, margin_bottom=4)
        self.shortcut_button = Gtk.Button(label=_('None'))
        self.shortcut_button.set_tooltip_text(_('Click and press a key combination to cycle exclusive toggle outputs on this input'))
        self.shortcut_clear_btn = Gtk.Button(icon_name='edit-clear-symbolic')
        self.shortcut_clear_btn.set_tooltip_text(_('Clear shortcut'))
        self.shortcut_box.append(Gtk.Label(label=_('Cycle Toggle Group Shortcut:')))
        self.shortcut_box.append(self.shortcut_button)
        self.shortcut_box.append(self.shortcut_clear_btn)

        self.shortcut_button.connect('clicked', self._on_shortcut_button_clicked)
        self.shortcut_clear_btn.connect('clicked', self._on_shortcut_clear)
        key_controller = Gtk.EventControllerKey.new()
        key_controller.connect('key-pressed', self._on_key_pressed)
        self.shortcut_button.add_controller(key_controller)

        self.outputs_visibility_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, margin_start=8, margin_top=4)
        self.outputs_expander = Gtk.Expander(label=_('Visible Outputs to Route To'))
        self.outputs_expander.set_child(self.outputs_visibility_box)
        self.outputs_expander.set_expanded(False)
        self.outputs_expander.set_visible(False)
        self._output_visibility_checks: dict[tuple[str, str], Gtk.CheckButton] = {}
        self.exclusive_source_checks: dict[str, Gtk.CheckButton] = {}
        self.port_selector = PortSelector()
        if device_type in ('a', 'hi'):
            self.combobox_widget = LabeledDropDown(_('Device: '), tooltip=_('Select a device'))
        else:
            self.combobox_widget = LabeledDropDown(_('Channel Map: '), tooltip=_('Select a channel map'))
        self.confirm_button = Gtk.Button(label='Apply')
        self.remove_button = IconButton('user-trash-symbolic')

        if device_type in ('vi', 'b'):
            self.combobox_widget.load_list(list(pulse_mappings.CHANNEL_MAPS))
        else:
            self.combobox_widget.connect('changed', self.device_combo_changed)

        dismiss_on_outside_click(self)

        self._arrange_widgets()

    def _arrange_widgets(self):

        # Create main container
        main_box = Gtk.Box(hexpand=True, orientation=Gtk.Orientation.VERTICAL)
        self.set_child(main_box)

        # Create name container
        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        name_box.append(self.nick_widget)
        if self.device_type in ('vi', 'b'):
            name_box.append(self.name_widget)

        # Create buttons container
        button_box = Gtk.Box(halign=Gtk.Align.END)
        if self.edit is True:
            button_box.append(self.remove_button)
        button_box.append(self.confirm_button)

        # Insert containers into main container
        main_box.append(name_box)
        main_box.append(self.combobox_widget)
        if self.device_type in ('hi', 'a'):
            main_box.append(self.port_selector)
        else:
            main_box.append(self.external_widget)
        if self.device_type in ('hi', 'vi'):
            main_box.append(self.shortcut_box)
            if self.edit:
                main_box.append(self.outputs_expander)
        main_box.append(button_box)

    @staticmethod
    def _format_shortcut(accel: str) -> str:
        if not accel:
            return _("None")
        ok, keyval, mods = Gtk.accelerator_parse(accel)
        if ok and keyval != 0:
            return Gtk.accelerator_get_label(keyval, mods)
        return accel

    def _on_shortcut_button_clicked(self, _):
        self._recording_shortcut = True
        self.shortcut_button.set_label(_("Press keys..."))

    def _on_shortcut_clear(self, _):
        self._recording_shortcut = False
        self._current_shortcut = ''
        self.shortcut_button.set_label(_("None"))

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if not self._recording_shortcut:
            return False
        if keyval in (
            Gdk.KEY_Shift_L, Gdk.KEY_Shift_R,
            Gdk.KEY_Control_L, Gdk.KEY_Control_R,
            Gdk.KEY_Alt_L, Gdk.KEY_Alt_R,
            Gdk.KEY_Super_L, Gdk.KEY_Super_R,
            Gdk.KEY_Meta_L, Gdk.KEY_Meta_R,
        ):
            return True
        if keyval in (Gdk.KEY_Escape, Gdk.KEY_BackSpace):
            self._recording_shortcut = False
            if keyval == Gdk.KEY_BackSpace:
                self._current_shortcut = ''
            self.shortcut_button.set_label(self._format_shortcut(self._current_shortcut))
            return True
        mods = state & Gtk.accelerator_get_default_mod_mask()
        if Gtk.accelerator_valid(keyval, mods):
            accel = Gtk.accelerator_name(keyval, mods)
            self._current_shortcut = accel
            self._recording_shortcut = False
            self.shortcut_button.set_label(self._format_shortcut(accel))
            return True
        return False

    def fill_settings(self, device_model):

        self.nick_widget.set_option(device_model.nick)
        self._current_shortcut = getattr(device_model, 'toggle_group_shortcut', '')
        self._recording_shortcut = False
        self.shortcut_button.set_label(self._format_shortcut(self._current_shortcut))

        if self.device_type in ('hi', 'vi') and self.edit:
            # Clear previous output checkboxes
            child = self.outputs_visibility_box.get_first_child()
            while child is not None:
                next_child = child.get_next_sibling()
                self.outputs_visibility_box.remove(child)
                child = next_child
            self._output_visibility_checks.clear()
            self.exclusive_source_checks.clear()

            has_outputs = False
            for out_type in ('a', 'b'):
                for out_id, conn in device_model.connections.get(out_type, {}).items():
                    has_outputs = True
                    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                    vis_check = Gtk.CheckButton(label=f"{conn.nick} ({out_type.upper()}{out_id})")
                    vis_check.set_active(not bool(getattr(conn, 'hidden', False)))
                    vis_check.set_tooltip_text(_("Show/hide this output in the routing list for this input"))
                    self._output_visibility_checks[(out_type, out_id)] = vis_check
                    row.append(vis_check)

                    if self.device_type == 'hi' and out_type == 'b':
                        excl_check = Gtk.CheckButton(label=_("Exclusive"))
                        excl_check.set_active(bool(getattr(conn, 'exclusive_source', False)))
                        excl_check.set_tooltip_text(
                            _("Exclusively route to this virtual output (enabling this hardware input disables other hardware inputs routed to %s)") % conn.nick
                        )
                        self.exclusive_source_checks[out_id] = excl_check
                        row.append(excl_check)

                    self.outputs_visibility_box.append(row)

            self.outputs_expander.set_visible(has_outputs)
        if self.device_type in ('hi', 'a'):
            self.port_selector.set_ports(device_model.channel_list, device_model.selected_channels)
            self.combobox_widget.set_active_name(device_model.description)
        else:
            self.name_widget.set_option(device_model.name)
            self.external_widget.set_active(device_model.external)
            self.combobox_widget.set_active_name(pulse_mappings.get_channel_map_name(device_model.channel_list))

    def device_combo_changed(self, widget, active_text):
        device = self.combobox_widget.get_active_entry()

        self.port_selector.set_ports(device.channel_list)

    @property
    def name(self):

        # if virtual
        if self.device_type in ('b', 'vi'):
            return self.name_widget.get_option()

        # if hardware
        return self.combobox_widget.get_active_entry().name

    @property
    def nick(self):
        return self.nick_widget.get_option()

    @property
    def description(self):

        # if virtual
        if self.device_type in ('b', 'vi'):
            return self.nick_widget.get_option()

        # if hardware
        return self.combobox_widget.get_active_entry().description

    @property
    def channels(self):
        return len(self.channel_list)

    @property
    def selected_channels(self):

        # if hardware
        if self.device_type in ('a', 'hi'):
            return self.port_selector.get_selected()
        return [True] * self.channels

    @property
    def channel_list(self):

        # if virtual
        if self.device_type in ('b', 'vi'):
            channel_map = self.combobox_widget.get_active_text()
            channel_list = pulse_mappings.CHANNEL_MAPS[channel_map]
            return channel_list

        # if hardware

        selected_channels = self.selected_channels
        channel_list = []

        # only grab channels that are sellected
        for channel, selected_channel in enumerate(selected_channels):
            if selected_channel is True:
                selected_device = self.combobox_widget.get_active_entry()
                channel_list.append(selected_device.channel_list[channel])

        return channel_list

    @property
    def external(self) -> bool:
        device_class = 'virtual' if self.device_type in ('b', 'vi') else 'hardware'
        if device_class == 'hardware':
            return False

        return self.external_widget.get_active()

    @property
    def volume(self):

        # if virtual
        if self.device_type in ('b', 'vi'):
            return [100] * self.channels

        # if hardware
        selected_channels = self.selected_channels
        volume_list = []
        for channel, selected_channel in enumerate(selected_channels):
            if selected_channel is True:
                selected_device = self.combobox_widget.get_active_entry()
                volume_list.append(selected_device.volume[channel])

        return volume_list

    def to_schema(self) -> dict:

        device_type = 'sink' if self.device_type in ('a', 'vi') else 'source'
        device_class = 'virtual' if self.device_type in ('b', 'vi') else 'hardware'

        data = {
            'name': self.name,
            'description': self.description,
            'nick': self.nick,
            'external': self.external,
            'channels': self.channels,
            'channel_list': self.channel_list,
            'selected_channels': self.selected_channels,
            'volume': self.volume,
            'device_type': device_type,
            'device_class': device_class,
            'toggle_group_shortcut': self._current_shortcut,
            'output_visibility': {
                f'{out_type}:{out_id}': check.get_active()
                for (out_type, out_id), check in self._output_visibility_checks.items()
            },
            'exclusive_virtual_outputs': {
                out_id: check.get_active()
                for out_id, check in self.exclusive_source_checks.items()
            },
        }

        return data
