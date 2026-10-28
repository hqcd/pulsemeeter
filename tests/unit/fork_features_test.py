import unittest
from types import SimpleNamespace
from unittest import mock

from pulsemeeter.model.config_model import ConfigModel, CATEGORY_KEYS
from pulsemeeter.model.device_model import DeviceModel
from pulsemeeter.model.connection_model import ConnectionModel
from pulsemeeter.model.signal_model import SignalModel
from pulsemeeter.controller.device_controller import DeviceController
from pulsemeeter.repository.device_repository import DeviceRepository
from pulsemeeter.clients.gtk.theme_manager import generate_theme_css, apply_alpha
from pulsemeeter.clients.gtk.shortcut_manager import GlobalShortcutManager, gtk_accel_to_portal_trigger


def _make_device(name, device_type='sink', device_class='virtual', channels=2):
    return DeviceModel(
        name=name,
        nick=name,
        description=name,
        channels=channels,
        channel_list=['front-left', 'front-right'][:channels],
        selected_channels=[True] * channels,
        device_type=device_type,
        device_class=device_class,
        primary=False if device_class == 'virtual' else None,
    )


class TestConfigModelForkFeatures(unittest.TestCase):

    def test_default_fork_settings(self):
        cfg = ConfigModel()
        self.assertTrue(cfg.scroll_volume)
        for key in CATEGORY_KEYS:
            self.assertIn(key, cfg.visible_categories)
            self.assertTrue(cfg.visible_categories[key])
        self.assertFalse(cfg.theme['enabled'])
        self.assertEqual(cfg.theme['bg_mode'], 'solid')

    def test_partial_visible_categories_healed(self):
        cfg = ConfigModel(visible_categories={'hi': False, 'sink_input': False})
        self.assertFalse(cfg.visible_categories['hi'])
        self.assertFalse(cfg.visible_categories['sink_input'])
        self.assertTrue(cfg.visible_categories['vi'])
        self.assertTrue(cfg.visible_categories['a'])
        self.assertTrue(cfg.visible_categories['b'])
        self.assertTrue(cfg.visible_categories['source_output'])

    def test_partial_theme_healed(self):
        cfg = ConfigModel(theme={'enabled': True, 'bg_mode': 'translucent', 'bg_opacity': 0.5})
        self.assertTrue(cfg.theme['enabled'])
        self.assertEqual(cfg.theme['bg_mode'], 'translucent')
        self.assertEqual(cfg.theme['bg_opacity'], 0.5)
        self.assertIn('accent_color', cfg.theme)
        self.assertIn('card_color', cfg.theme)


class TestExclusiveToggleOutputs(unittest.TestCase):

    def setUp(self):
        vi1 = _make_device('vi_1', device_type='sink', device_class='virtual')
        out1 = _make_device('out_1', device_type='sink', device_class='hardware')
        out2 = _make_device('out_2', device_type='sink', device_class='hardware')
        out3 = _make_device('out_3', device_type='source', device_class='virtual')

        self.cfg = ConfigModel(devices={
            'vi': {'1': vi1},
            'hi': {},
            'a': {'1': out1, '2': out2},
            'b': {'1': out3},
        })
        # Mark a/1 and a/2 as exclusive toggle group, leave b/1 as independent
        vi1.connections['a']['1'].toggle_group = True
        vi1.connections['a']['2'].toggle_group = True
        vi1.connections['b']['1'].toggle_group = False

        persistence = SimpleNamespace(get_config=lambda: self.cfg)
        self.repo = DeviceRepository(persistence)

        self.controller = DeviceController.__new__(DeviceController)
        SignalModel.__init__(self.controller)
        self.controller.device_repository = self.repo
        self.controller._loopback_procs = {}
        self.controller._intermediate_sinks = {}
        self.controller._device_available = mock.Mock(return_value=False)

        self.connect_events = []
        self.controller.connect('connect', lambda *args: self.connect_events.append(args))

    def test_enabling_toggle_output_disables_other_toggle_outputs(self):
        vi1 = self.repo.get_device('vi', '1')
        # Also enable independent output b/1
        self.controller.set_connection('vi', '1', 'b', '1', True)
        self.assertTrue(vi1.connections['b']['1'].state)

        # Enable toggle group output a/1
        self.controller.set_connection('vi', '1', 'a', '1', True)
        self.assertTrue(vi1.connections['a']['1'].state)
        self.assertFalse(vi1.connections['a']['2'].state)
        self.assertTrue(vi1.connections['b']['1'].state)

        # Enable toggle group output a/2 -> should automatically disable a/1, keep b/1
        self.controller.set_connection('vi', '1', 'a', '2', True)
        self.assertFalse(vi1.connections['a']['1'].state)
        self.assertTrue(vi1.connections['a']['2'].state)
        self.assertTrue(vi1.connections['b']['1'].state)

    def test_cycle_toggle_group_rotates_exclusive_outputs(self):
        vi1 = self.repo.get_device('vi', '1')
        # First cycle: activates a/1
        res1 = self.controller.cycle_toggle_group('vi', '1')
        self.assertEqual(res1, ('a', '1'))
        self.assertTrue(vi1.connections['a']['1'].state)
        self.assertFalse(vi1.connections['a']['2'].state)

        # Second cycle: activates a/2 and deactivates a/1
        res2 = self.controller.cycle_toggle_group('vi', '1')
        self.assertEqual(res2, ('a', '2'))
        self.assertFalse(vi1.connections['a']['1'].state)
        self.assertTrue(vi1.connections['a']['2'].state)

        # Third cycle: wraps around to a/1
        res3 = self.controller.cycle_toggle_group('vi', '1')
        self.assertEqual(res3, ('a', '1'))
        self.assertTrue(vi1.connections['a']['1'].state)
        self.assertFalse(vi1.connections['a']['2'].state)

    def test_exclusive_hardware_input_to_virtual_output(self):
        hi1 = _make_device('hi_1', device_type='source', device_class='hardware')
        hi2 = _make_device('hi_2', device_type='source', device_class='hardware')
        b1 = _make_device('b_1', device_type='source', device_class='virtual')
        cfg = ConfigModel(devices={
            'vi': {},
            'hi': {'1': hi1, '2': hi2},
            'a': {},
            'b': {'1': b1},
        })
        hi1.connections['b']['1'].exclusive_source = True
        hi2.connections['b']['1'].exclusive_source = True

        persistence = SimpleNamespace(get_config=lambda: cfg)
        repo = DeviceRepository(persistence)
        controller = DeviceController.__new__(DeviceController)
        SignalModel.__init__(controller)
        controller.device_repository = repo
        controller._loopback_procs = {}
        controller._intermediate_sinks = {}
        controller._device_available = mock.Mock(return_value=False)

        # Route hardware input 1 to virtual output 1
        controller.set_connection('hi', '1', 'b', '1', True)
        self.assertTrue(hi1.connections['b']['1'].state)
        self.assertFalse(hi2.connections['b']['1'].state)

        # Route hardware input 2 to virtual output 1 -> should disable hardware input 1 -> virtual output 1
        controller.set_connection('hi', '2', 'b', '1', True)
        self.assertFalse(hi1.connections['b']['1'].state)
        self.assertTrue(hi2.connections['b']['1'].state)

        # Route hardware input 1 to virtual output 1 again -> should disable hardware input 2 -> virtual output 1
        controller.set_connection('hi', '1', 'b', '1', True)
        self.assertTrue(hi1.connections['b']['1'].state)
        self.assertFalse(hi2.connections['b']['1'].state)

    def test_device_settings_update_hides_outputs_and_sets_exclusive_source(self):
        hi1 = _make_device('hi_1', device_type='source', device_class='hardware')
        a1 = _make_device('a_1', device_type='sink', device_class='hardware')
        b1 = _make_device('b_1', device_type='source', device_class='virtual')
        cfg = ConfigModel(devices={
            'vi': {},
            'hi': {'1': hi1},
            'a': {'1': a1},
            'b': {'1': b1},
        })
        schema = {
            'name': 'hi_1',
            'description': 'hi_1',
            'nick': 'hi_1',
            'external': False,
            'channels': 2,
            'channel_list': ['front-left', 'front-right'],
            'selected_channels': [True, True],
            'volume': [100, 100],
            'device_type': 'source',
            'device_class': 'hardware',
            'toggle_group_shortcut': '',
            'output_visibility': {'a:1': False, 'b:1': True},
            'exclusive_virtual_outputs': {'1': True},
        }
        hi1.update_device_settings(schema)
        self.assertTrue(hi1.connections['a']['1'].hidden)
        self.assertFalse(hi1.connections['b']['1'].hidden)
        self.assertTrue(hi1.connections['b']['1'].exclusive_source)


class TestThemingEngine(unittest.TestCase):

    def test_disabled_theme_returns_base_css_only(self):
        css = generate_theme_css({'enabled': False})
        self.assertIn('toggle-group-member', css)
        self.assertNotIn('linear-gradient', css)

    def test_gradient_theme_generates_linear_gradient(self):
        css = generate_theme_css({
            'enabled': True,
            'bg_mode': 'gradient',
            'bg_color': 'rgba(10, 20, 30, 1.0)',
            'bg_gradient_end': 'rgba(40, 50, 60, 1.0)',
            'bg_gradient_angle': 90,
            'bg_opacity': 0.8,
            'card_color': 'rgba(30, 30, 40, 0.7)',
            'accent_color': 'rgba(100, 150, 250, 1.0)',
            'text_color': 'rgba(255, 255, 255, 1.0)',
        })
        self.assertIn('linear-gradient(90deg,', css)
        self.assertIn('rgba(10, 20, 30, 0.800)', css)
        self.assertIn('rgba(40, 50, 60, 0.800)', css)

    def test_translucent_theme_applies_opacity(self):
        css = generate_theme_css({
            'enabled': True,
            'bg_mode': 'translucent',
            'bg_color': 'rgba(20, 30, 40, 1.0)',
            'bg_opacity': 0.45,
        })
        self.assertIn('rgba(20, 30, 40, 0.450)', css)


class TestShortcutManager(unittest.TestCase):

    def test_gtk_accel_to_portal_trigger(self):
        trigger = gtk_accel_to_portal_trigger('<Control><Alt>1')
        self.assertEqual(trigger, 'CTRL+ALT+1')

    def test_sync_from_config_collects_route_and_cycle_shortcuts(self):
        vi1 = _make_device('vi_1', device_type='sink', device_class='virtual')
        vi1.toggle_group_shortcut = '<Control><Shift>t'
        out1 = _make_device('out_1', device_type='sink', device_class='hardware')
        cfg = ConfigModel(devices={'vi': {'1': vi1}, 'hi': {}, 'a': {'1': out1}, 'b': {}})
        cfg.devices['vi']['1'].connections['a']['1'].shortcut = '<Control><Alt>1'

        triggered = []
        mgr = GlobalShortcutManager(lambda action_id: triggered.append(action_id))
        mgr.sync_from_config(cfg)

        self.assertIn('route:vi:1:a:1', mgr.shortcuts)
        self.assertEqual(mgr.shortcuts['route:vi:1:a:1'][0], '<Control><Alt>1')
        self.assertIn('toggle_group:vi:1', mgr.shortcuts)
        self.assertEqual(mgr.shortcuts['toggle_group:vi:1'][0], '<Control><Shift>t')


if __name__ == '__main__':
    unittest.main()
