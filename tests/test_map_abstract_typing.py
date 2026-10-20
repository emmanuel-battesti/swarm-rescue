"""
Typing checks for `MapAbstract`.

Purely static contracts, but they are contracts: a wrong annotation is
invisible at runtime and only shows up in the participants' IDEs, where it
reads as "this is either a Playground or something odd".

`playground` used to be annotated `Union[Playground, Type[None]]`.
`Type[None]` is the *class* NoneType, not the value None, so the annotation
said the property returns a Playground or the class None, which is neither
what it returns nor a useful thing to show.
"""

import pathlib
import sys
import typing

# Insert the 'src' directory into sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from swarm_rescue.simulation.gui_map.map_abstract import MapAbstract
from swarm_rescue.simulation.gui_map.playground import Playground


def _return_annotation():
    return typing.get_type_hints(MapAbstract.playground.fget)["return"]


class TestPlaygroundAnnotation:
    def test_annotation_is_optional_playground(self):
        """The property is a Playground, or None before the map is built."""
        assert _return_annotation() == typing.Optional[Playground]

    def test_annotation_is_not_a_type_of_none(self):
        """`Type[None]` is the NoneType *class*, not the None value.

        `Union[Playground, Type[None]]` and `Optional[Playground]` are not the
        same annotation: the first says the property may return the class
        NoneType, the second that it may return None.
        """
        annotation = _return_annotation()
        assert typing.Type[None] not in annotation.__args__
        assert annotation is not typing.Union[Playground, typing.Type[None]]

    def test_annotation_resolves_at_runtime(self):
        """A broken forward reference would raise here instead of in the IDE."""
        assert _return_annotation() is not None


class TestPlaygroundPropertyBehavior:
    def test_it_is_none_before_the_map_is_built(self):
        """Matches what the annotation now promises."""

        class BareMap(MapAbstract):
            def __init__(self):
                super().__init__(drone_type=None)

        assert BareMap().playground is None
