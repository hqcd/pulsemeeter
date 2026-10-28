import gettext

from pulsemeeter.model.types import DEVICE_TYPE_PRETTY as PRETTY
from pulsemeeter.model.types import DEVICE_TYPE_DESCRIPTION as DESCRIPTION
from pulsemeeter.clients.gtk.widgets.utils.popover_utils import dismiss_on_outside_click

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Pango  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext


class DeviceBox(Gtk.Frame):

    def __init__(self, widget, label, button=None, tooltip=None):
        '''
        Returns a framed widget with the requested label
            "widget" is the widget that is going to be framed
            "label" is the label of the frame
            "tooltip" is hint text shown when hovering the label
        '''
        super().__init__(
            margin_bottom=5,
            margin_top=5,
            margin_start=5,
            margin_end=5,
            hexpand=True,
            vexpand=True,
        )
        title = Gtk.Label(
            label=label,
            margin_bottom=5,
            halign=Gtk.Align.CENTER,
            wrap=True,
            wrap_mode=Pango.WrapMode.WORD_CHAR,
            justify=Gtk.Justification.CENTER,
        )
        if tooltip is not None:
            title.set_tooltip_text(tooltip)
        main_box = Gtk.Box(hexpand=True, spacing=8)
        main_box.append(title)
        if button is not None:
            main_box.append(button)

        self.set_label_widget(main_box)
        self.set_label_align(0.5)
        self.set_child(widget)
        self.add_css_class('category-frame')


def arrange_widgets(content):
    '''
    Arrange device boxes in a grid layout.

    Args:
        device_boxes (dict): Dictionary of device boxes

    Returns:
        Gtk.Grid: The grid container
    '''
    grid = Gtk.Grid(
        margin_start=8,
        margin_end=8,
        margin_top=8,
        margin_bottom=8,
        hexpand=True,
        vexpand=True,
    )

    for device_type in ('hi', 'vi', 'a', 'b'):
        content.device_box[device_type].set_properties(
            orientation=Gtk.Orientation.HORIZONTAL,
            hexpand=True,
            vexpand=True,
        )

    for app_type in ('sink_input', 'source_output'):
        content.app_box[app_type].set_properties(
            orientation=Gtk.Orientation.HORIZONTAL,
            hexpand=True,
            vexpand=True,
        )

    device_frame = {'a': None, 'b': None, 'vi': None, 'hi': None}
    for device_type in device_frame:
        device_frame[device_type] = DeviceBox(
            content.device_box[device_type],
            PRETTY[device_type],
            content.create_device_button[device_type],
            DESCRIPTION.get(device_type)
        )

    # id rather use framed
    sink_input_frame = DeviceBox(content.app_box['sink_input'], PRETTY['sink_input'])
    source_output_frame = DeviceBox(content.app_box['source_output'], PRETTY['source_output'])
    content.category_containers = {
        'hi': device_frame['hi'],
        'vi': device_frame['vi'],
        'a': device_frame['a'],
        'b': device_frame['b'],
        'sink_input': sink_input_frame,
        'source_output': source_output_frame,
    }
    grid.attach(device_frame['hi'], 0, 0, 1, 1)
    grid.attach(device_frame['vi'], 1, 0, 1, 1)
    grid.attach(device_frame['a'], 0, 1, 1, 1)
    grid.attach(device_frame['b'], 1, 1, 1, 1)
    grid.attach(sink_input_frame, 2, 0, 1, 1)
    grid.attach(source_output_frame, 2, 1, 1, 1)

    settings_popover = Gtk.Popover()
    settings_popover.set_child(content.settings_box)
    dismiss_on_outside_click(settings_popover)
    content.settings_button.set_popover(settings_popover)
    content.settings_box.set_properties(margin_start=10, margin_end=10, margin_top=10, margin_bottom=10)

    settings_box = Gtk.Box(halign=Gtk.Align.END, valign=Gtk.Align.START, vexpand=False,
                           margin_top=6, margin_end=6)
    settings_box.append(content.settings_button)

    scrolled = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
    scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled.set_child(grid)

    overlay = Gtk.Overlay()
    overlay.set_child(scrolled)
    overlay.add_overlay(settings_box)

    content.append(overlay)
