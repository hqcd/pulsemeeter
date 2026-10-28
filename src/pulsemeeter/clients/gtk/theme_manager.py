'''
Theming engine for PulseMeeter GTK4 client.
Supports solid colors, linear gradients, translucent backgrounds (desktop wallpaper show-through),
card/frame styling, accent colors, and text color customization.
'''
import logging
import re

# pylint: disable=wrong-import-order,wrong-import-position
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk  # noqa: E402
# pylint: enable=wrong-import-order,wrong-import-position

LOG = logging.getLogger("generic")


def apply_alpha(color_str: str, opacity: float) -> str:
    '''
    Convert a CSS color string (rgba/rgb/hex) to an rgba() string with the given opacity (0.0 - 1.0).
    '''
    opacity = max(0.0, min(1.0, float(opacity)))
    rgba = Gdk.RGBA()
    if rgba.parse(color_str):
        r = int(round(rgba.red * 255))
        g = int(round(rgba.green * 255))
        b = int(round(rgba.blue * 255))
        return f'rgba({r}, {g}, {b}, {opacity:.3f})'

    # Fallback regex parsing if Gdk.RGBA is unavailable or fails
    match = re.match(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color_str)
    if match:
        r, g, b = match.groups()
        return f'rgba({r}, {g}, {b}, {opacity:.3f})'

    return f'rgba(30, 30, 46, {opacity:.3f})'


def generate_theme_css(theme_config: dict) -> str:
    '''
    Generate GTK4 CSS string from a theme configuration dictionary.
    '''
    base_css = """
    button.toggle-group-member {
        border-style: dashed;
        border-width: 1px;
    }

    frame.category-frame {
        padding: 10px;
    }

    frame.device-frame,
    frame.app-frame {
        padding: 10px;
        border-radius: 8px;
    }
    """

    if not theme_config or not theme_config.get('enabled', False):
        return base_css

    bg_mode = theme_config.get('bg_mode', 'solid')
    bg_color = theme_config.get('bg_color', 'rgba(30, 30, 46, 1.0)')
    bg_gradient_end = theme_config.get('bg_gradient_end', 'rgba(17, 17, 27, 1.0)')
    bg_gradient_angle = int(theme_config.get('bg_gradient_angle', 135))
    bg_opacity = float(theme_config.get('bg_opacity', 0.85))
    card_color = theme_config.get('card_color', 'rgba(49, 50, 68, 0.85)')
    accent_color = theme_config.get('accent_color', 'rgba(137, 180, 250, 1.0)')
    text_color = theme_config.get('text_color', 'rgba(205, 214, 244, 1.0)')

    if bg_mode == 'gradient':
        c1 = apply_alpha(bg_color, bg_opacity) if bg_opacity < 1.0 else bg_color
        c2 = apply_alpha(bg_gradient_end, bg_opacity) if bg_opacity < 1.0 else bg_gradient_end
        window_bg_rule = f"background-image: linear-gradient({bg_gradient_angle}deg, {c1}, {c2}); background-color: transparent;"
    elif bg_mode == 'translucent':
        c1 = apply_alpha(bg_color, bg_opacity)
        window_bg_rule = f"background-color: {c1}; background-image: none;"
    else:  # solid
        window_bg_rule = f"background-color: {bg_color}; background-image: none;"

    accent_translucent = apply_alpha(accent_color, 0.35)
    accent_border = apply_alpha(accent_color, 0.8)

    css = f"""
    {base_css}

    window, window.background {{
        {window_bg_rule}
        color: {text_color};
    }}

    window > box,
    window scrolledwindow,
    window viewport,
    window stack {{
        background-color: transparent;
        background-image: none;
    }}

    frame.category-frame {{
        padding: 12px;
    }}

    frame.category-frame > border {{
        background-color: {apply_alpha(card_color, 0.35)};
        border-radius: 10px;
        border-color: {apply_alpha(text_color, 0.15)};
    }}

    frame.device-frame,
    frame.app-frame {{
        background-color: {card_color};
        border-radius: 10px;
        padding: 12px;
    }}

    frame.device-frame > border,
    frame.app-frame > border {{
        border-radius: 10px;
        border-color: {apply_alpha(text_color, 0.2)};
    }}

    window label {{
        color: {text_color};
    }}

    scale trough highlight {{
        background-color: {accent_color};
        border-color: {accent_color};
    }}

    progressbar trough progress {{
        background-color: {accent_color};
        border-color: {accent_color};
    }}

    button.toggle:checked,
    togglebutton:checked {{
        background-color: {accent_translucent};
        border-color: {accent_border};
        color: {text_color};
    }}

    checkbutton:checked > check {{
        background-color: {accent_color};
        border-color: {accent_color};
    }}
    """
    return css


class ThemeManager:
    '''
    Manages a Gtk.CssProvider registered on the default display for runtime theme updates.
    '''

    def __init__(self):
        self._provider = None

    def apply_theme(self, theme_config: dict):
        css = generate_theme_css(theme_config)
        try:
            display = Gdk.Display.get_default()
            if display is None:
                return
            if self._provider is None:
                self._provider = Gtk.CssProvider()
                Gtk.StyleContext.add_provider_for_display(
                    display,
                    self._provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_USER
                )
            self._provider.load_from_data(css.encode('utf-8'))
        except Exception:
            LOG.exception("Failed to apply custom theme CSS")
