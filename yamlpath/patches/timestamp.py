# pylint: skip-file
"""
Fix missing anchors from timestamp and date nodes.

This must be removed once incorporated into ruamel.yaml, likely at version
0.17.22.

Source: https://sourceforge.net/p/ruamel-yaml/tickets/440/
Copyright 2022 Anthon van der Neut, William W. Kimball Jr. MBA MSIS
"""
import ruamel.yaml
from ruamel.yaml.constructor import ConstructorError
from ruamel.yaml.anchor import Anchor
from ruamel.yaml.timestamp import TimeStamp

from typing import Any, Dict, Union  # NOQA
import datetime
import copy


class AnchoredTimeStamp(TimeStamp):
    """Extend TimeStamp to track YAML Anchors."""

    def __init__(self, *args: Any, **kw: Any) -> None:
        """Initialize a new instance."""
        self._yaml: Dict[Any, Any] = dict(t=False, tz=None, delta=0)

    def __new__(cls, *args: Any, **kw: Any) -> Any:  # datetime is immutable
        """Create a new, immutable instance."""
        anchor = kw.pop('anchor', None)
        ts = TimeStamp.__new__(cls, *args, **kw)
        if anchor is not None:
            ts.yaml_set_anchor(anchor, always_dump=True)
        return ts

    def __deepcopy__(self, memo: Any) -> Any:
        """Deeply copy this instance to another."""
        ts = AnchoredTimeStamp(self.year, self.month, self.day, self.hour, self.minute, self.second)
        ts._yaml = copy.deepcopy(self._yaml)
        return ts

    @property
    def anchor(self) -> Any:
        """Access the YAML Anchor."""
        if not hasattr(self, Anchor.attrib):
            setattr(self, Anchor.attrib, Anchor())
        return getattr(self, Anchor.attrib)

    def yaml_anchor(self, any: bool = False) -> Any:
        """Get the YAML Anchor."""
        if not hasattr(self, Anchor.attrib):
            return None
        if any or self.anchor.always_dump:
            return self.anchor
        return None

    def yaml_set_anchor(self, value: Any, always_dump: bool = False) -> None:
        """Set the YAML Anchor."""
        self.anchor.value = value
        self.anchor.always_dump = always_dump


class AnchoredDate(AnchoredTimeStamp):
    """Define AnchoredDate."""

    pass


def construct_anchored_timestamp(
    self, node: Any, values: Any = None
) -> Union[AnchoredTimeStamp, AnchoredDate]:
    """Construct an AnchoredTimeStamp."""
    try:
        match = self.timestamp_regexp.match(node.value)
    except TypeError:
        match = None
    if match is None:
        raise ConstructorError(
            None,
            None,
            f'failed to construct timestamp from "{node.value}"',
            node.start_mark,
        )
    values = match.groupdict()
    dd = ruamel.yaml.util.create_timestamp(**values)  # this has delta applied
    delta = None
    if values['tz_sign']:
        tz_hour = int(values['tz_hour'])
        minutes = values['tz_minute']
        tz_minute = int(minutes) if minutes else 0
        delta = datetime.timedelta(hours=tz_hour, minutes=tz_minute)
        if values['tz_sign'] == '-':
            delta = -delta
    if isinstance(dd, datetime.datetime):
        data = AnchoredTimeStamp(
            dd.year, dd.month, dd.day, dd.hour, dd.minute, dd.second, dd.microsecond, anchor=node.anchor
        )
    else:
        data = AnchoredDate(dd.year, dd.month, dd.day, 0, 0, 0, 0, anchor=node.anchor)
        return data
    if delta:
        data._yaml['delta'] = delta
        tz = values['tz_sign'] + values['tz_hour']
        if values['tz_minute']:
            tz += ':' + values['tz_minute']
        data._yaml['tz'] = tz
    else:
        if values['tz']:  # no delta
            data._yaml['tz'] = values['tz']
    if values['t']:
        data._yaml['t'] = True
    return data

ruamel.yaml.constructor.RoundTripConstructor.add_constructor('tag:yaml.org,2002:timestamp', construct_anchored_timestamp)

def represent_anchored_timestamp(self, data: Any):
    """Render an AnchoredTimeStamp."""
    try:
        anchor = data.yaml_anchor()
    except AttributeError:
        anchor = None
    inter = 'T' if data._yaml['t'] else ' '
    _yaml = data._yaml
    if _yaml['delta']:
        data += _yaml['delta']
    if isinstance(data, AnchoredDate):
        value = data.date().isoformat()
    else:
        value = data.isoformat(inter)
    if _yaml['tz']:
        value += _yaml['tz']
    return self.represent_scalar('tag:yaml.org,2002:timestamp', value, anchor=anchor)

ruamel.yaml.representer.RoundTripRepresenter.add_representer(AnchoredTimeStamp, represent_anchored_timestamp)
ruamel.yaml.representer.RoundTripRepresenter.add_representer(AnchoredDate, represent_anchored_timestamp)
