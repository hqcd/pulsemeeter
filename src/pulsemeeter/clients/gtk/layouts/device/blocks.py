from pulsemeeter.clients.gtk.widgets.device.device_widget import DeviceWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Pango  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


def arrange_widgets(device_widget: DeviceWidget):
    '''
    Arrange device widget in blocks layout.

    Args:
        device_widget: The device widget to arrange

    Returns:
        DeviceWidget: The arranged device widget
    '''

    # Create grid layout
    button_props = {
        'vexpand': False,
        'hexpand': False,
        'valign': Gtk.Align.CENTER,
        'halign': Gtk.Align.END
    }

    device_widget.edit_button.set_properties(halign=Gtk.Align.END, valign=Gtk.Align.START, hexpand=False)
    device_widget.primary_widget.set_properties(**button_props)
    device_widget.mute_widget.set_properties(**button_props)
    device_widget.vumeter_widget.set_properties(margin_bottom=6, margin_start=6, hexpand=True)
    device_widget.volume_widget.set_properties(hexpand=True)

    device_widget.nick_label.set_properties(
        wrap=True,
        wrap_mode=Pango.WrapMode.WORD,
        hexpand=True,
        xalign=0.0,
    )
    device_widget.description_label.set_properties(
        wrap=True,
        wrap_mode=Pango.WrapMode.WORD,
        hexpand=True,
        xalign=0.0,
    )

    device_widget.set_properties(
        margin_top=6,
        margin_bottom=6,
        margin_start=6,
        margin_end=6,
        hexpand=True,
        vexpand=True,
    )

    main_grid = Gtk.Grid(
        hexpand=True,
        vexpand=True,
        row_spacing=6,
        margin_top=8,
        margin_bottom=8,
        margin_start=8,
        margin_end=8,
    )
    control_grid = Gtk.Grid(hexpand=True, row_spacing=4, column_spacing=6)

    text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, hexpand=True)
    text_box.append(device_widget.nick_label)
    text_box.append(device_widget.description_label)

    name_container = Gtk.Box(margin_start=0, margin_end=0, hexpand=True, orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    name_container.append(device_widget.warning_icon)
    name_container.append(text_box)
    name_container.append(device_widget.edit_button)
    if device_widget.device_model.nick == device_widget.device_model.description:
        device_widget.description_label.set_visible(False)

    control_grid.attach(device_widget.volume_widget, 0, 0, 1, 1)
    control_grid.attach(device_widget.vumeter_widget, 0, 1, 2, 1)
    button_box = Gtk.Box(spacing=4)
    button_box.append(device_widget.mute_widget)
    if device_widget.device_model.primary is not None:
        button_box.append(device_widget.primary_widget)

    main_grid.attach(name_container, 0, 0, 1, 1)
    control_grid.attach(button_box, 1, 0, 1, 1)
    main_grid.attach(control_grid, 0, 1, 1, 1)

    if device_widget.device_model.get_type() in ('vi', 'hi'):
        device_widget.connections_widgets['a'].set_properties(hexpand=True, spacing=4)
        device_widget.connections_widgets['b'].set_properties(hexpand=True, spacing=4)
        connections_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6, hexpand=True)
        connections_container.append(device_widget.connections_widgets['a'])
        connections_container.append(device_widget.connections_widgets['b'])
        main_grid.attach(connections_container, 0, 2, 1, 1)

    device_widget.set_child(main_grid)
    return device_widget
