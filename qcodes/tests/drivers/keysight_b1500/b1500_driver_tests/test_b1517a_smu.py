from unittest.mock import MagicMock, call
import re

import pytest

from qcodes.instrument_drivers.Keysight.keysightb1500 import constants
from qcodes.instrument_drivers.Keysight.keysightb1500.KeysightB1517A import \
    B1517A
from qcodes.instrument_drivers.Keysight.keysightb1500.constants import \
    VOutputRange, CompliancePolarityMode, IOutputRange, IMeasRange, MM

# pylint: disable=redefined-outer-name


@pytest.fixture
def mainframe():
    yield MagicMock()


@pytest.fixture
def smu(mainframe):
    slot_nr = 1
    smu = B1517A(parent=mainframe, name='B1517A', slot_nr=slot_nr)
    yield smu


def test_snapshot():
    from qcodes.instrument.base import InstrumentBase
    # We need to use `InstrumentBase` (not a bare mock) in order for
    # `snapshot` methods call resolution to work out
    mainframe = InstrumentBase(name='mainframe')
    mainframe.write = MagicMock()
    slot_nr = 1
    smu = B1517A(parent=mainframe, name='B1517A', slot_nr=slot_nr)

    smu.use_high_speed_adc()
    smu.source_config(output_range=VOutputRange.AUTO)
    smu.measure_config(measure_range=IMeasRange.AUTO)
    smu.timing_parameters(0.0, 0.123, 321)

    s = smu.snapshot()

    assert '_source_config' in s
    assert 'output_range' in s['_source_config']
    assert isinstance(s['_source_config']['output_range'], VOutputRange)
    assert '_measure_config' in s
    assert 'measure_range' in s['_measure_config']
    assert isinstance(s['_measure_config']['measure_range'], IMeasRange)
    assert '_timing_parameters' in s
    assert 'number' in s['_timing_parameters']
    assert isinstance(s['_timing_parameters']['number'], int)


def test_force_voltage_with_autorange(smu):
    mainframe = smu.parent

    smu.source_config(output_range=VOutputRange.AUTO)
    smu.voltage(10)

    mainframe.write.assert_called_once_with('DV 1,0,10')


def test_force_voltage_autorange_and_compliance(smu):
    mainframe = smu.parent

    smu.source_config(output_range=VOutputRange.AUTO,
                      compliance=1e-6,
                      compl_polarity=CompliancePolarityMode.AUTO,
                      min_compliance_range=IOutputRange.MIN_10uA)
    smu.voltage(20)

    mainframe.write.assert_called_once_with('DV 1,0,20,1e-06,0,15')


def test_new_source_config_should_invalidate_old_source_config(smu):
    mainframe = smu.parent

    smu.source_config(output_range=VOutputRange.AUTO,
                      compliance=1e-6,
                      compl_polarity=CompliancePolarityMode.AUTO,
                      min_compliance_range=IOutputRange.MIN_10uA)

    smu.source_config(output_range=VOutputRange.AUTO)
    smu.voltage(20)

    mainframe.write.assert_called_once_with('DV 1,0,20')


def test_unconfigured_source_defaults_to_autorange_v(smu):
    mainframe = smu.parent

    smu.voltage(10)

    mainframe.write.assert_called_once_with('DV 1,0,10')


def test_unconfigured_source_defaults_to_autorange_i(smu):
    mainframe = smu.parent

    smu.current(0.2)

    mainframe.write.assert_called_once_with('DI 1,0,0.2')


def test_force_current_with_autorange(smu):
    mainframe = smu.parent

    smu.source_config(output_range=IOutputRange.AUTO)
    smu.current(0.1)

    mainframe.write.assert_called_once_with('DI 1,0,0.1')


def test_raise_warning_output_range_mismatches_output_command(smu):
    smu.source_config(output_range=VOutputRange.AUTO)
    msg = re.escape("Asking to force current, but source_config contains a "
                    "voltage output range")
    with pytest.raises(TypeError, match=msg):
        smu.current(0.1)

    smu.source_config(output_range=IOutputRange.AUTO)
    msg = re.escape("Asking to force voltage, but source_config contains a "
                    "current output range")
    with pytest.raises(TypeError, match=msg):
        smu.voltage(0.1)


def test_measure_current(smu):
    mainframe = smu.parent
    mainframe.ask.return_value = "NAI+000.005E-06\r"
    assert pytest.approx(0.005e-6) == smu.current()


def test_measure_voltage(smu):
    mainframe = smu.parent
    mainframe.ask.return_value = "NAV+000.123E-06\r"
    assert pytest.approx(0.123e-6) == smu.voltage()


def test_some_voltage_sourcing_and_current_measurement(smu):
    mainframe = smu.parent

    smu.source_config(output_range=VOutputRange.MIN_0V5, compliance=1e-9)
    smu.measure_config(IMeasRange.FIX_100nA)

    mainframe.ask.return_value = "NAI+000.005E-09\r"

    smu.voltage(6)

    mainframe.write.assert_called_once_with('DV 1,5,6,1e-09')

    assert pytest.approx(0.005e-9) == smu.current()


def test_use_high_resolution_adc(smu):
    mainframe = smu.parent

    smu.use_high_resolution_adc()

    mainframe.write.assert_called_once_with('AAD 1,1')


def test_use_high_speed_adc(smu):
    mainframe = smu.parent

    smu.use_high_speed_adc()

    mainframe.write.assert_called_once_with('AAD 1,0')


def test_measurement_mode_at_init(smu):
    mode_at_init = smu.measurement_mode()
    assert mode_at_init == MM.Mode.SPOT


def test_measurement_mode_to_enum_value(smu):
    mainframe = smu.parent

    smu.measurement_mode(MM.Mode.SAMPLING)
    mainframe.write.assert_called_once_with('MM 10,1')

    new_mode = smu.measurement_mode()
    assert new_mode == MM.Mode.SAMPLING


def test_measurement_mode_to_int_value(smu):
    mainframe = smu.parent

    smu.measurement_mode(10)
    mainframe.write.assert_called_once_with('MM 10,1')

    new_mode = smu.measurement_mode()
    assert new_mode == MM.Mode.SAMPLING


def test_setting_timing_parameters(smu):
    mainframe = smu.parent

    smu.timing_parameters(0.0, 0.42, 32)
    mainframe.write.assert_called_once_with('MT 0.0,0.42,32')

    mainframe.reset_mock()

    smu.timing_parameters(0.0, 0.42, 32, 0.02)
    mainframe.write.assert_called_once_with('MT 0.0,0.42,32,0.02')


def test_set_average_samples_for_high_speed_adc(smu):
    mainframe = smu.parent

    smu.set_average_samples_for_high_speed_adc(131, 2)
    mainframe.write.assert_called_once_with('AV 131,2')

    mainframe.reset_mock()

    smu.set_average_samples_for_high_speed_adc(132)
    mainframe.write.assert_called_once_with('AV 132,0')


def test_connection_mode_of_smu_filter(smu):
    mainframe = smu.parent

    smu.connection_mode_of_smu_filter(True)
    mainframe.write.assert_called_once_with('FL 1')

    mainframe.reset_mock()

    smu.connection_mode_of_smu_filter(True, [constants.ChNr.SLOT_01_CH1,
                                             constants.ChNr.SLOT_02_CH1,
                                             constants.ChNr.SLOT_03_CH1])
    mainframe.write.assert_called_once_with('FL 1,1,2,3')

    mainframe.reset_mock()

    smu.connection_mode_of_smu_filter(True, [constants.ChNr.SLOT_01_CH2,
                                             constants.ChNr.SLOT_02_CH2,
                                             constants.ChNr.SLOT_03_CH2])
    mainframe.write.assert_called_once_with('FL 1,102,202,302')


def test_measurement_operation_mode(smu):
    mainframe = smu.parent

    smu.measurement_operation_mode(constants.CMM.Mode.COMPLIANCE_SIDE)
    mainframe.write.assert_called_once_with('CMM 1,0')

    mainframe.reset_mock()

    mainframe.ask.return_value = 'CMM 1,0'
    cmm_mode = smu.measurement_operation_mode()
    assert cmm_mode == [(constants.ChNr.SLOT_01_CH1,
                         constants.CMM.Mode.COMPLIANCE_SIDE)]


def test_current_measurement_range(smu):
    mainframe = smu.parent

    smu.current_measurement_range(constants.IMeasRange.FIX_1A)
    mainframe.write.assert_called_once_with('RI 1,-20')

    mainframe.reset_mock()

    mainframe.ask.return_value = 'RI 1,-20'
    cmm_mode = smu.current_measurement_range()
    assert cmm_mode == [('SLOT_01_CH1', 'FIX_1A')]


def test_iv_sweep_delay(smu):
    mainframe = smu.root_instrument


    smu.iv_sweep.hold_time(43.12)
    smu.iv_sweep.delay(34.01)
    smu.iv_sweep.step_delay(0.01)
    smu.iv_sweep.trigger_delay(0.1)
    smu.iv_sweep.measure_delay(15.4)

    mainframe.write.assert_has_calls([call("WT 43.12,0.0,0.0,0.0,0.0"),
                                      call("WT 43.12,34.01,0.0,0.0,0.0"),
                                      call("WT 43.12,34.01,0.01,0.0,0.0"),
                                      call("WT 43.12,34.01,0.01,0.1,0.0"),
                                      call("WT 43.12,34.01,0.01,0.1,15.4")])


def test_iv_sweep_mode_start_end_steps_compliance(smu):
    mainframe = smu.root_instrument

    # mainframe.ask.return_value = "WV 1,1,19,0.0,0.0,1,0.1,0.0"

    smu.iv_sweep.sweep_mode(constants.SweepMode.LINEAR_TWO_WAY)
    smu.iv_sweep.sweep_range(constants.VOutputRange.MIN_2V)
    smu.iv_sweep.sweep_start(0.2)
    smu.iv_sweep.sweep_end(12.3)
    smu.iv_sweep.sweep_steps(13)
    smu.iv_sweep.current_compliance(45e-3)
    smu.iv_sweep.power_compliance(0.2)

    mainframe.write.assert_has_calls([call('WT 0.0,0.0,0.0,0.0,0.0'),
                                      call('WV 1,1,0,0.0,0.0,1,0.1,2.0'),
                                      call('WV 1,3,0,0.0,0.0,1,0.1,2.0'),
                                      call('WV 1,3,20,0.0,0.0,1,0.1,2.0'),
                                      call('WV 1,3,20,0.2,0.0,1,0.1,2.0'),
                                      call('WV 1,3,20,0.2,12.3,1,0.1,2.0'),
                                      call('WV 1,3,20,0.2,12.3,13,0.1,2.0'),
                                      call('WV 1,3,20,0.2,12.3,13,0.045,2.0'),
                                      call('WV 1,3,20,0.2,12.3,13,0.045,0.2')]
                                     )


def test_sweep_auto_abort(smu):
    mainframe = smu.parent

    smu.iv_sweep.sweep_auto_abort(constants.Abort.ENABLED)

    mainframe.write.assert_called_once_with("WM 2")


def test_post_sweep_voltage_cond(smu):
    mainframe = smu.parent

    smu.iv_sweep.post_sweep_voltage_condition(constants.WMDCV.Post.STOP)

    mainframe.write.assert_called_once_with("WM 2,2")



