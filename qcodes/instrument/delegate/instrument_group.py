import importlib

from typing import Callable, List, Dict, Any, TYPE_CHECKING, Union

from qcodes.instrument.base import InstrumentBase

if TYPE_CHECKING:
    from qcodes.station import Station


class InstrumentGroup(InstrumentBase):
    """
    InstrumentGroup is an instrument driver to represent a series of instruments
    that are grouped together. This instrument is mainly used as a wrapper for
    sub instruments/submodules and particularly built for use with grouping
    multiple :class:`DelegateInstrument` s.

    Args:
        name: Name referring to this group of items
        station: Measurement station with real instruments
        submodules: A mapping between an instrument name and the values passed
            to the constructor of the class specified by `type`.
        initial_values: A mapping between the names of parameters and initial
            values to set on those parameters when loading this instrument.
        set_initial_values_on_load: Set default values on load. Defaults to
            False.
    """
    def __init__(
        self,
        name: str,
        station: "Station",
        submodules: Dict[str, Dict[str, Union[str, List[str]]]],
        initial_values: Dict[str, Dict[str, Any]],
        set_initial_values_on_load: bool = False,
        **kwargs: Any
    ):
        super().__init__(name=name, **kwargs)

        for submodule_name, parameters in submodules.items():
            instr_class = self._instr_class(parameters.pop("type"))
            submodule = instr_class(
                name=submodule_name,
                station=station,
                parameters=parameters,
                initial_values=initial_values.get(submodule_name),
                set_initial_values_on_load=set_initial_values_on_load
            )

            self.add_submodule(
                submodule_name,
                submodule
            )

    @staticmethod
    def _instr_class(submodule_type: str) -> Callable:
        module_name = '.'.join(submodule_type.split('.')[:-1])
        instr_class_name = submodule_type.split('.')[-1]
        module = importlib.import_module(module_name)
        instr_class = getattr(module, instr_class_name)
        return instr_class

    def __repr__(self) -> str:
        submodules = ", ".join(self.submodules.keys())
        return f"InstrumentGroup(name={self.name}, submodules={submodules})"
