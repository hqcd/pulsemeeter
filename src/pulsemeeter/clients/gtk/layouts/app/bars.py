from pulsemeeter.clients.gtk.widgets.app.app_widget import AppWidget

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Pango  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position


def arrange_widgets(app_widget: AppWidget):

    button_props = {
        'vexpand': False,
        'hexpand': False,
        'valign': Gtk.Align.CENTER,
        'halign': Gtk.Align.CENTER
    }

    scale_props = {
        'orientation': Gtk.Orientation.VERTICAL,
        'vexpand': True,
        'hexpand': False,
        'height_request': 100,
        'inverted': True,
    }
    app_widget.set_properties(
        margin_top=6,
        margin_bottom=6,
        margin_start=6,
        margin_end=6,
        hexpand=True,
        vexpand=True,
    )
    app_widget.label.set_properties(
        wrap=True,
        wrap_mode=Pango.WrapMode.WORD,
        justify=Gtk.Justification.CENTER,
        hexpand=True,
    )
    app_widget.mute_widget.set_properties(**button_props)
    app_widget.volume_widget.set_properties(**scale_props)
    meter = app_widget.vumeter_widget  # None for recording apps
    if meter is not None:
        meter.set_properties(margin_top=10, margin_start=10, margin_end=0, **scale_props)
    app_widget.combobox.set_hexpand(True)

    name_box = Gtk.Box(spacing=4, halign=Gtk.Align.CENTER, hexpand=True, margin_bottom=6)
    name_box.append(app_widget.icon)
    name_box.append(app_widget.label)

    volume_box = Gtk.Box(spacing=4, halign=Gtk.Align.CENTER, vexpand=True, orientation=Gtk.Orientation.VERTICAL)
    volume_box.append(app_widget.volume_widget)
    volume_box.append(app_widget.mute_widget)

    control_grid = Gtk.Grid(hexpand=True, vexpand=True, row_spacing=8, column_spacing=8, halign=Gtk.Align.CENTER)
    # without a meter the volume column is the only one, so it stays centered
    volume_column = 0 if meter is None else 1
    if meter is not None:
        control_grid.attach(meter, 0, 1, 1, 1)
    control_grid.attach(volume_box, volume_column, 1, 1, 1)
    control_grid.attach(app_widget.combobox, 0, 2, volume_column + 1, 1)

    main_grid = Gtk.Grid(margin_top=8, margin_bottom=8, margin_end=8, margin_start=8, hexpand=True, vexpand=True, row_spacing=8, column_spacing=8)
    main_grid.attach(name_box, 0, 0, 1, 1)
    main_grid.attach(control_grid, 0, 1, 1, 1)

    app_widget.set_child(main_grid)
