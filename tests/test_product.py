"""Hello's own part, on App Base's real device and settings (saved in a temporary folder)."""
import json
import types

import pytest

import product
from base.device import Device


@pytest.fixture
def device(tmp_path):
    platform = types.SimpleNamespace(state_path=lambda name: str(tmp_path / name), device_name=lambda: 'hello',
                                     NAME_EDITABLE=False, health=lambda: {}, SENSORS=())
    d = Device(product, platform)
    d.states = 0

    def state_changed():
        d.states += 1
    d.state_changed = state_changed
    return d


def test_the_greeting_starts_as_the_default(device):
    assert product.state(device) == {'greeting': 'Hello from Juggle OS'}
    assert product.info(device) == {'greeting': 'Hello from Juggle OS'}


def test_a_greeting_from_mqtt_is_saved_and_its_state_sent(device, tmp_path):
    assert product.set(device, {'greeting': 'Morning'}) is None
    assert product.state(device) == {'greeting': 'Morning'}
    assert device.states == 1
    assert json.loads((tmp_path / 'config.json').read_text())['hello']['greeting'] == 'Morning'


def test_the_same_greeting_again_sends_no_state(device):
    assert product.set(device, {'greeting': 'Hello from Juggle OS'}) is None
    assert device.states == 0


@pytest.mark.parametrize('command', [{'greeting': ''}, {'greeting': '   '}, {'greeting': 'x' * 65},
                                     {'greeting': 5}, {'colour': 'red'}])
def test_a_wrong_command_is_refused_and_changes_nothing(device, command):
    assert product.set(device, command)
    assert product.state(device) == {'greeting': 'Hello from Juggle OS'}
    assert device.states == 0


def test_home_assistant_gets_a_text_box_that_sends_json():
    config = product.ha_entity(None, 'greeting', {'set': 'home/hello/set'})
    assert product.HA_ENTITIES == (('text', 'greeting'),)
    assert config['command_topic'] == 'home/hello/set'
    assert config['max'] == product.GREETING_LONGEST
    assert 'tojson' in config['command_template']


def test_the_version_is_the_manifests():
    manifest = json.loads((product.Path(product.__file__).parent / 'app.json').read_text())
    assert product.VERSION == manifest['version']
    assert manifest['juggle'] == '1.0' and manifest['name'] == 'hello'
