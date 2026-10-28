import gettext

from pulsemeeter.model.types import DEVICE_TYPE_PRETTY
from pulsemeeter.clients.gtk.widgets.common.dropdown_widget import LabeledDropDown
from pulsemeeter.clients.gtk.layouts import layout_manager

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GObject  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

_ = gettext.gettext

CATEGORY_KEYS = ('hi', 'vi', 'a', 'b', 'sink_input', 'source_output')
BG_MODES = ['solid', 'gradient', 'translucent']
BG_MODE_LABELS = {
    'solid': _('Solid'),
    'gradient': _('Gradient'),
    'translucent': _('Translucent'),
}
LABEL_TO_BG_MODE = {v: k for k, v in BG_MODE_LABELS.items()}


def _make_color_button(rgba_str: str) -> Gtk.Widget:
    rgba = Gdk.RGBA()
    if not rgba.parse(rgba_str):
        rgba.parse('rgba(30, 30, 46, 1.0)')
    if hasattr(Gtk, 'ColorDialog') and hasattr(Gtk, 'ColorDialogButton'):
        dialog = Gtk.ColorDialog(with_alpha=True)
        btn = Gtk.ColorDialogButton(dialog=dialog)
        btn.set_rgba(rgba)
        return btn
    btn = Gtk.ColorButton()
    btn.set_use_alpha(True)
    btn.set_rgba(rgba)
    return btn


def _get_color_button_rgba(btn: Gtk.Widget) -> str:
    rgba = btn.get_rgba()
    r = int(round(rgba.red * 255))
    g = int(round(rgba.green * 255))
    b = int(round(rgba.blue * 255))
    return f'rgba({r}, {g}, {b}, {rgba.alpha:.3f})'


def _set_color_button_rgba(btn: Gtk.Widget, rgba_str: str):
    rgba = Gdk.RGBA()
    if rgba.parse(rgba_str):
        btn.set_rgba(rgba)


class SettingsMenuBox(Gtk.Box):

    vumeters: Gtk.CheckButton
    cleanup: Gtk.CheckButton
    scroll_volume: Gtk.CheckButton
    layout: LabeledDropDown

    __gsignals__ = {
        "settings_change": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (GObject.TYPE_PYOBJECT,)),
        "help_pressed": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.vumeters = Gtk.CheckButton(label=_('Enable VU Meters'))
        self.cleanup = Gtk.CheckButton(label=_('Enable Cleanup'))
        self.scroll_volume = Gtk.CheckButton(label=_('Control Volume Sliders with Scroll Wheel'))
        self.layout = LabeledDropDown(_('Layout: '))
        self.layout.load_list(layout_manager.get_layout_list())

        self.vumeters.set_tooltip_text(_('Enable or disable VU meters (volume peak)'))
        self.cleanup.set_tooltip_text(_('Enable or disable cleaning up devices and connections upon closing'))
        self.scroll_volume.set_tooltip_text(_('Allow adjusting volume sliders by scrolling the mouse wheel'))
        self.layout.set_tooltip_text(_('Select the GUI layout'))

        # Category visibility checkboxes
        self.category_checks: dict[str, Gtk.CheckButton] = {}
        cat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, margin_start=8, margin_top=4)
        for cat_key in CATEGORY_KEYS:
            check = Gtk.CheckButton(label=DEVICE_TYPE_PRETTY[cat_key])
            check.set_active(True)
            self.category_checks[cat_key] = check
            cat_box.append(check)

        cat_expander = Gtk.Expander(label=_('Visible Categories'))
        cat_expander.set_child(cat_box)
        cat_expander.set_expanded(False)

        # Theme Engine controls
        self.theme_enabled = Gtk.CheckButton(label=_('Enable Custom Theme'))
        self.bg_mode = LabeledDropDown(_('Background: '))
        self.bg_mode.load_list([BG_MODE_LABELS[m] for m in BG_MODES])

        self.bg_color_btn = _make_color_button('rgba(30, 30, 46, 1.0)')
        self.bg_gradient_end_btn = _make_color_button('rgba(17, 17, 27, 1.0)')
        self.card_color_btn = _make_color_button('rgba(49, 50, 68, 0.85)')
        self.accent_color_btn = _make_color_button('rgba(137, 180, 250, 1.0)')
        self.text_color_btn = _make_color_button('rgba(205, 214, 244, 1.0)')

        self.bg_angle_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.bg_angle_scale.set_range(0, 360)
        self.bg_angle_scale.set_digits(0)
        self.bg_angle_scale.set_value(135)
        self.bg_angle_scale.set_hexpand(True)
        self.bg_angle_scale.set_size_request(120, -1)

        self.bg_opacity_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.bg_opacity_scale.set_range(0.05, 1.0)
        self.bg_opacity_scale.set_digits(2)
        self.bg_opacity_scale.set_value(0.85)
        self.bg_opacity_scale.set_hexpand(True)
        self.bg_opacity_scale.set_size_request(120, -1)

        theme_grid = Gtk.Grid(row_spacing=6, column_spacing=8, margin_start=8, margin_top=4)
        theme_grid.attach(self.theme_enabled, 0, 0, 2, 1)
        theme_grid.attach(self.bg_mode, 0, 1, 2, 1)

        theme_grid.attach(Gtk.Label(label=_('Primary Background:'), halign=Gtk.Align.START), 0, 2, 1, 1)
        theme_grid.attach(self.bg_color_btn, 1, 2, 1, 1)

        self.grad_end_label = Gtk.Label(label=_('Gradient End Color:'), halign=Gtk.Align.START)
        theme_grid.attach(self.grad_end_label, 0, 3, 1, 1)
        theme_grid.attach(self.bg_gradient_end_btn, 1, 3, 1, 1)

        self.grad_angle_label = Gtk.Label(label=_('Gradient Angle (°):'), halign=Gtk.Align.START)
        theme_grid.attach(self.grad_angle_label, 0, 4, 1, 1)
        theme_grid.attach(self.bg_angle_scale, 1, 4, 1, 1)

        self.bg_opacity_label = Gtk.Label(label=_('Background Opacity:'), halign=Gtk.Align.START)
        theme_grid.attach(self.bg_opacity_label, 0, 5, 1, 1)
        theme_grid.attach(self.bg_opacity_scale, 1, 5, 1, 1)

        theme_grid.attach(Gtk.Label(label=_('Card Color:'), halign=Gtk.Align.START), 0, 6, 1, 1)
        theme_grid.attach(self.card_color_btn, 1, 6, 1, 1)

        theme_grid.attach(Gtk.Label(label=_('Accent Color:'), halign=Gtk.Align.START), 0, 7, 1, 1)
        theme_grid.attach(self.accent_color_btn, 1, 7, 1, 1)

        theme_grid.attach(Gtk.Label(label=_('Text Color:'), halign=Gtk.Align.START), 0, 8, 1, 1)
        theme_grid.attach(self.text_color_btn, 1, 8, 1, 1)

        self.bg_mode.connect('changed', self._update_theme_row_visibility)
        self._connect_live_theme_signals()

        theme_expander = Gtk.Expander(label=_('Theming & Background'))
        theme_expander.set_child(theme_grid)
        theme_expander.set_expanded(False)

        self.apply_button = Gtk.Button(label=_('Apply'))
        self.help_button = Gtk.Button(icon_name='help-about-symbolic')
        self.help_button.set_tooltip_text(_('Open the welcome guide'))
        Gtk.Accessible.update_property(
            self.help_button,
            [Gtk.AccessibleProperty.LABEL],
            [_('Open the welcome guide')]
        )

        button_box = Gtk.Box(vexpand=False, halign=Gtk.Align.END, valign=Gtk.Align.END, spacing=6)
        button_box.append(self.help_button)
        button_box.append(self.apply_button)

        mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8,
                          margin_top=6, margin_bottom=6, margin_start=6, margin_end=6)
        mainbox.append(self.vumeters)
        mainbox.append(self.cleanup)
        mainbox.append(self.scroll_volume)
        mainbox.append(self.layout)
        mainbox.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        mainbox.append(cat_expander)
        mainbox.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        mainbox.append(theme_expander)
        mainbox.append(button_box)

        self.apply_button.connect('clicked', self.apply_settings)
        self.help_button.connect('clicked', lambda _: self.emit('help_pressed'))

        self.append(mainbox)
        self._update_theme_row_visibility()

    def _update_theme_row_visibility(self, *_):
        mode_label = self.bg_mode.get_active_text()
        mode = LABEL_TO_BG_MODE.get(mode_label, 'solid')
        is_grad = mode == 'gradient'
        is_trans = mode in ('translucent', 'gradient')
        self.grad_end_label.set_visible(is_grad)
        self.bg_gradient_end_btn.set_visible(is_grad)
        self.grad_angle_label.set_visible(is_grad)
        self.bg_angle_scale.set_visible(is_grad)
        self.bg_opacity_label.set_visible(is_trans)
        self.bg_opacity_scale.set_visible(is_trans)

    def _connect_live_theme_signals(self):
        self._filling = False
        self.theme_enabled.connect('toggled', self._on_live_theme_changed)
        self.bg_mode.connect('changed', self._on_live_theme_changed)
        self.bg_angle_scale.connect('value-changed', self._on_live_theme_changed)
        self.bg_opacity_scale.connect('value-changed', self._on_live_theme_changed)
        for btn in (
            self.bg_color_btn,
            self.bg_gradient_end_btn,
            self.card_color_btn,
            self.accent_color_btn,
            self.text_color_btn,
        ):
            btn.connect('notify::rgba', self._on_live_theme_changed)
            if hasattr(btn, 'connect'):
                try:
                    btn.connect('color-set', self._on_live_theme_changed)
                except TypeError:
                    pass

    def _on_live_theme_changed(self, *_):
        if getattr(self, '_filling', False):
            return
        self.emit('settings_change', self.to_schema())

    def fill_settings(self, config_model):
        self._filling = True
        try:
            self.vumeters.set_active(config_model.vumeters)
            self.cleanup.set_active(config_model.cleanup)
            self.scroll_volume.set_active(getattr(config_model, 'scroll_volume', True))
            self.layout.set_active_name(config_model.layout)

            vis = getattr(config_model, 'visible_categories', {})
            for cat_key, check in self.category_checks.items():
                check.set_active(vis.get(cat_key, True))

            theme = getattr(config_model, 'theme', {})
            self.theme_enabled.set_active(theme.get('enabled', False))
            mode = theme.get('bg_mode', 'solid')
            self.bg_mode.set_active_name(BG_MODE_LABELS.get(mode, BG_MODE_LABELS['solid']))
            _set_color_button_rgba(self.bg_color_btn, theme.get('bg_color', 'rgba(30, 30, 46, 1.0)'))
            _set_color_button_rgba(self.bg_gradient_end_btn, theme.get('bg_gradient_end', 'rgba(17, 17, 27, 1.0)'))
            self.bg_angle_scale.set_value(float(theme.get('bg_gradient_angle', 135)))
            self.bg_opacity_scale.set_value(float(theme.get('bg_opacity', 0.85)))
            _set_color_button_rgba(self.card_color_btn, theme.get('card_color', 'rgba(49, 50, 68, 0.85)'))
            _set_color_button_rgba(self.accent_color_btn, theme.get('accent_color', 'rgba(137, 180, 250, 1.0)'))
            _set_color_button_rgba(self.text_color_btn, theme.get('text_color', 'rgba(205, 214, 244, 1.0)'))
            self._update_theme_row_visibility()
        finally:
            self._filling = False

    def to_schema(self):
        mode_label = self.bg_mode.get_active_text()
        bg_mode = LABEL_TO_BG_MODE.get(mode_label, 'solid')
        return {
            'vumeters': self.vumeters.get_active(),
            'cleanup': self.cleanup.get_active(),
            'scroll_volume': self.scroll_volume.get_active(),
            'layout': self.layout.get_active_text(),
            'visible_categories': {
                cat_key: check.get_active() for cat_key, check in self.category_checks.items()
            },
            'theme': {
                'enabled': self.theme_enabled.get_active(),
                'bg_mode': bg_mode,
                'bg_color': _get_color_button_rgba(self.bg_color_btn),
                'bg_gradient_end': _get_color_button_rgba(self.bg_gradient_end_btn),
                'bg_gradient_angle': int(self.bg_angle_scale.get_value()),
                'bg_opacity': round(float(self.bg_opacity_scale.get_value()), 2),
                'card_color': _get_color_button_rgba(self.card_color_btn),
                'accent_color': _get_color_button_rgba(self.accent_color_btn),
                'text_color': _get_color_button_rgba(self.text_color_btn),
            },
        }

    def apply_settings(self, _):
        self.emit('settings_change', self.to_schema())
