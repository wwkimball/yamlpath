# pylint: skip-file
# type: ignore
"""
Fix writing unordered sets with aliased entries.

Source: https://sourceforge.net/p/ruamel-yaml/tickets/384/
Copyright 2021 Anthon van der Neut, William W. Kimball, Jr. MBA MSIS
"""

import ruamel.yaml


if ruamel.yaml.version_info < (0, 17, 5):
    class MyAliasEvent(ruamel.yaml.events.NodeEvent):
        """Add a style slot."""

        __slots__ = ('style')

        def __init__(self, anchor, start_mark=None, end_mark=None, style=None, comment=None, ):
            """Initialize."""
            ruamel.yaml.events.NodeEvent.__init__(self, anchor, start_mark, end_mark, comment)
            self.style = style

    ruamel.yaml.events.AliasEvent = MyAliasEvent

    def new_init(self, anchor, start_mark=None, end_mark=None, style=None, comment=None, ):
        """Override class initializer."""
        ruamel.yaml.events.NodeEvent.__init__(self, anchor, start_mark, end_mark, comment)
        self.style = style

    ruamel.yaml.events.AliasEvent.__slots__ = ('style', )
    ruamel.yaml.events.AliasEvent.__init__ = new_init

    class MyEmitter(ruamel.yaml.emitter.Emitter):
        """Custom Emitter."""

        def expect_node(self, root=False, sequence=False, mapping=False, simple_key=False):
            """Expect a node."""
            self.root_context = root
            self.sequence_context = sequence  # not used in PyYAML
            self.mapping_context = mapping
            self.simple_key_context = simple_key
            if isinstance(self.event, (MyAliasEvent, ruamel.yaml.events.AliasEvent)):
                self.expect_alias()
            elif isinstance(self.event, (ruamel.yaml.events.ScalarEvent, ruamel.yaml.events.CollectionStartEvent)):
                if (
                    self.process_anchor('&')
                    and isinstance(self.event, ruamel.yaml.events.ScalarEvent)
                    and self.sequence_context
                ):
                    self.sequence_context = False
                if (
                    root
                    and isinstance(self.event, ruamel.yaml.events.ScalarEvent)
                    and not self.scalar_after_indicator
                ):
                    self.write_indent()
                self.process_tag()
                if isinstance(self.event, ruamel.yaml.events.ScalarEvent):
                    # nprint('@', self.indention, self.no_newline, self.column)
                    self.expect_scalar()
                elif isinstance(self.event, ruamel.yaml.events.SequenceStartEvent):
                    # nprint('@', self.indention, self.no_newline, self.column)
                    i2, n2 = self.indention, self.no_newline  # NOQA
                    if self.event.comment:
                        if self.event.flow_style is False and self.event.comment:
                            if self.write_post_comment(self.event):
                                self.indention = False
                                self.no_newline = True
                        if self.write_pre_comment(self.event):
                            self.indention = i2
                            self.no_newline = not self.indention
                    if (
                        self.flow_level
                        or self.canonical
                        or self.event.flow_style
                        or self.check_empty_sequence()
                    ):
                        self.expect_flow_sequence()
                    else:
                        self.expect_block_sequence()
                elif isinstance(self.event, ruamel.yaml.events.MappingStartEvent):
                    if self.event.flow_style is False and self.event.comment:
                        self.write_post_comment(self.event)
                    if self.event.comment and self.event.comment[1]:
                        self.write_pre_comment(self.event)
                    if (
                        self.flow_level
                        or self.canonical
                        or self.event.flow_style
                        or self.check_empty_mapping()
                    ):
                        self.expect_flow_mapping(single=self.event.nr_items == 1)
                    else:
                        self.expect_block_mapping()
            else:
                raise ruamel.yaml.emitter.EmitterError(
                    "expected NodeEvent, but got {}".format(self.event)
                )

        def expect_block_mapping_key(self, first=False):
            """Expect block mapping key."""
            if not first and isinstance(self.event, ruamel.yaml.events.MappingEndEvent):
                if self.event.comment and self.event.comment[1]:
                    # final comments from a doc
                    self.write_pre_comment(self.event)
                self.indent = self.indents.pop()
                self.state = self.states.pop()
            else:
                if self.event.comment and self.event.comment[1]:
                    # final comments from a doc
                    self.write_pre_comment(self.event)
                self.write_indent()
                if self.check_simple_key():
                    if not isinstance(
                        self.event, (ruamel.yaml.events.SequenceStartEvent, ruamel.yaml.events.MappingStartEvent)
                    ):  # sequence keys
                        try:
                            if self.event.style == '?':
                                self.write_indicator('?', True, indention=True)
                        except AttributeError:  # aliases have no style
                            pass
                    self.states.append(self.expect_block_mapping_simple_value)
                    self.expect_node(mapping=True, simple_key=True)
                    if isinstance(self.event, (MyAliasEvent, ruamel.yaml.events.AliasEvent)):
                        self.stream.write(' ')
                else:
                    self.write_indicator('?', True, indention=True)
                    self.states.append(self.expect_block_mapping_value)
                    self.expect_node(mapping=True)

        def check_simple_key(self):
            """Check simple keys."""
            length = 0
            if isinstance(self.event, ruamel.yaml.events.NodeEvent) and self.event.anchor is not None:
                if self.prepared_anchor is None:
                    self.prepared_anchor = self.prepare_anchor(self.event.anchor)
                length += len(self.prepared_anchor)
            if (
                isinstance(self.event, (ruamel.yaml.events.ScalarEvent, ruamel.yaml.events.CollectionStartEvent))
                and self.event.tag is not None
            ):
                if self.prepared_tag is None:
                    self.prepared_tag = self.prepare_tag(self.event.tag)
                length += len(self.prepared_tag)
            if isinstance(self.event, ruamel.yaml.events.ScalarEvent):
                if self.analysis is None:
                    self.analysis = self.analyze_scalar(self.event.value)
                length += len(self.analysis.scalar)
            return length < self.MAX_SIMPLE_KEY_LENGTH and (
                isinstance(self.event, (MyAliasEvent, ruamel.yaml.events.AliasEvent))
                or (isinstance(self.event, ruamel.yaml.events.SequenceStartEvent) and self.event.flow_style is True)
                or (isinstance(self.event, ruamel.yaml.events.MappingStartEvent) and self.event.flow_style is True)
                or (
                    isinstance(self.event, ruamel.yaml.events.ScalarEvent)
                    # if there is an explicit style for an empty string, it is a simple key
                    and not (self.analysis.empty and self.style and self.style not in '\'"')
                    and not self.analysis.multiline
                )
                or self.check_empty_sequence()
                or self.check_empty_mapping()
            )


    class MySerializer(ruamel.yaml.serializer.Serializer):
        """Custom Serializer."""

        def serialize_node(self, node, parent, index):
            # type: (Any, Any, Any) -> None
            """Serialize node."""
            alias = self.anchors[node]
            if node in self.serialized_nodes:
                # self.emitter.emit(ruamel.yaml.events.AliasEvent(alias, style=node.style if node.style == '?' else None))
                node_style = getattr(node, 'style', None)
                if node_style != '?':
                    node_style = None
                self.emitter.emit(MyAliasEvent(alias, style=node_style))
            else:
                self.serialized_nodes[node] = True
                self.resolver.descend_resolver(parent, index)
                if isinstance(node, ruamel.yaml.nodes.ScalarNode):
                    # here check if the node.tag equals the one that would result from parsing
                    # if not equal quoting is necessary for strings
                    detected_tag = self.resolver.resolve(ruamel.yaml.nodes.ScalarNode, node.value, (True, False))
                    default_tag = self.resolver.resolve(ruamel.yaml.nodes.ScalarNode, node.value, (False, True))
                    implicit = (
                        (node.tag == detected_tag),
                        (node.tag == default_tag),
                        node.tag.startswith('tag:yaml.org,2002:'),
                    )
                    self.emitter.emit(
                        ruamel.yaml.events.ScalarEvent(
                            alias,
                            node.tag,
                            implicit,
                            node.value,
                            style=node.style,
                            comment=node.comment,
                        )
                    )
                elif isinstance(node, ruamel.yaml.nodes.SequenceNode):
                    implicit = node.tag == self.resolver.resolve(ruamel.yaml.nodes.SequenceNode, node.value, True)
                    comment = node.comment
                    end_comment = None
                    seq_comment = None
                    if node.flow_style is True:
                        if comment:  # eol comment on flow style sequence
                            seq_comment = comment[0]
                            # comment[0] = None
                    if comment and len(comment) > 2:
                        end_comment = comment[2]
                    else:
                        end_comment = None
                    self.emitter.emit(
                        ruamel.yaml.events.SequenceStartEvent(
                            alias,
                            node.tag,
                            implicit,
                            flow_style=node.flow_style,
                            comment=node.comment,
                        )
                    )
                    index = 0
                    for item in node.value:
                        self.serialize_node(item, node, index)
                        index += 1
                    self.emitter.emit(ruamel.yaml.events.SequenceEndEvent(comment=[seq_comment, end_comment]))
                elif isinstance(node, ruamel.yaml.nodes.MappingNode):
                    implicit = node.tag == self.resolver.resolve(ruamel.yaml.nodes.MappingNode, node.value, True)
                    comment = node.comment
                    end_comment = None
                    map_comment = None
                    if node.flow_style is True:
                        if comment:  # eol comment on flow style sequence
                            map_comment = comment[0]
                            # comment[0] = None
                    if comment and len(comment) > 2:
                        end_comment = comment[2]
                    self.emitter.emit(
                        ruamel.yaml.events.MappingStartEvent(
                            alias,
                            node.tag,
                            implicit,
                            flow_style=node.flow_style,
                            comment=node.comment,
                            nr_items=len(node.value),
                        )
                    )
                    for key, value in node.value:
                        self.serialize_node(key, node, None)
                        self.serialize_node(value, node, key)
                    self.emitter.emit(ruamel.yaml.events.MappingEndEvent(comment=[map_comment, end_comment]))
                self.resolver.ascend_resolver()
