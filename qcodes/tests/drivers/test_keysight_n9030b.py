import pytest

from qcodes.instrument_drivers.Keysight.N9030B import (N9030B,
                                                       SpectrumAnalyzerMode,
                                                       PhaseNoiseMode)
import qcodes.instrument.sims as sims

VISALIB = sims.__file__.replace('__init__.py', 'Keysight_N9030B.yaml@sim')


@pytest.fixture(name="driver")
def _make_driver():
    driver = N9030B('n9030B_sim', address="GPIB::1::INSTR", visalib=VISALIB)
    yield driver
    driver.close()


@pytest.fixture(name="sa")
def _activate_swept_sa_measurement(driver):
    yield driver.sa


@pytest.fixture(name="pn")
def _activate_log_plot_measurement(driver):
    yield driver.pn


def test_idn(driver):
    assert {'firmware': '0.1',
            'model': 'N9030B',
            'serial': '1000',
            'vendor': 'Keysight Technologies'} == driver.IDN()


def test_swept_sa_setup(sa):
    assert isinstance(sa, SpectrumAnalyzerMode)

    sa.setup_swept_sa_sweep(123, 11e3, 501)
    assert sa.root_instrument.mode() == "SA"
    assert sa.root_instrument.measurement() == "SAN"

    assert sa.start() == 123
    assert sa.stop() == 11e3


def test_log_plot_setup(pn):
    assert isinstance(pn, PhaseNoiseMode)

    pn.setup_log_plot_sweep(100, 1e6, 10001)
    assert pn.root_instrument.mode() == "PNOISE"
    assert pn.root_instrument.measurement() == "LPL"
