#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 The LogikSim Authors. All rights reserved.
# Use of this source code is governed by the GNU GPL license that can
# be found in the LICENSE.txt file.
#
'''
Lines are connected in trees from one output to multiple inputs.
'''

import copy

from PySide import QtGui, QtCore

from .insertable_item import InsertableItem
from .line_edge_indicator import LineEdgeIndicator
from .connector import ConnectorItem
from .state_line_item import StateLineItem


class LineTree(InsertableItem, StateLineItem):
    """ A tree of connected lines """

    _debug_painting = False

    def __init__(self, parent, metadata):
        """
        Defines a tree of connected lines.

        The lines are internally stored as a tree. For non-connected trees
        the root of the tree is arbitrary, while line trees connected to
        one output have a defined start, the output. A line tree can only
        have one output driving it and arbitrarily many inputs or free ends.
        Unconnected line trees can be driven by mouse interaction.

        :param path: Initial path given as list of QtCore.QPointF.
        """
        metadata.setdefault('tree', {})

        # defines tree as dict of dict, with key being a tuple (x,y) and
        # value being a dict of children or empty dict. Since there is only
        # one root node, the _tree only contains one key-value pair.
        self._tree = None

        self._lines = None  # list with all lines as QLinesF
        self._edges = None  # set with all edges as tuples
        self._shape = None  # shape path
        self._rect = None  # bounding rect
        self._edge_indicators = []  # list of LineEdgeIndicators

        self._connected_input = None  # id of connected input
        self._connected_outputs = []  # (out_port, id) of connected outputs

        super().__init__(parent, metadata)

    @classmethod
    def metadata_from_path(cls, path):
        """
        Return metadata representing given path.

        This can then be used to construct a tree.

        :param path: Path being added given as list of QtCore.QPointF
        """
        def path_to_tree(p):
            root = pivot = {}
            for point in p:
                p = pivot[point.toTuple()] = {}
                pivot = p
            return root

        return {'tree': cls._encode_tree(path_to_tree(path))}

    @classmethod
    def GUI_GUID(cls):
        return "00352520-7cf0-43b7-9449-6fca5be8d6dc"

    def selectionRect(self):
        return self._rect

    def apply_update(self, metadata):
        super().apply_update(metadata)

        # tree updates
        enc_tree = metadata.get('tree', None)
        if enc_tree is not None:
            tree = self._decode_tree(enc_tree)
            if tree != self._tree:
                self._set_tree(tree)

        # collect input value changes
        input_states = metadata.get('state', None)
        if input_states is not None:
            self.set_logic_state(input_states)

        # connection updates
        inputs = metadata.get('inputs', None)
        if inputs is not None:
            self._connected_input = inputs[0][0]

        outputs = metadata.get('outputs', None)
        if outputs is not None:
            self._connected_outputs = list(
                (con_id, con_port) for con_id, con_port, _ in outputs)

    @classmethod
    def _encode_tree(cls, tree):
        """Encodes tree into a JSON representable data structure."""
        def _encode_subtree(tree):
            new_tree = []
            for point, children in tree.items():
                new_tree.append([list(point), _encode_subtree(children)])
            return new_tree
        return _encode_subtree(tree)

    @classmethod
    def _decode_tree(cls, enc_tree):
        """Decodes tree from JSON representable data structure."""
        def _decode_subtree(enc_tree):
            new_tree = {}
            for point, children in enc_tree:
                new_tree[tuple(point)] = _decode_subtree(children)
            return new_tree
        return _decode_subtree(enc_tree)

    def _set_tree(self, tree):
        """
        Set new tree and updates internal storage.

        Always use this function, rather than assigning to self._tree.
        """
        self._tree = tree
        self._update_tree()

        # TODO: create undo event
        pass

        # notify backend
        self._notify_backend({'tree': self._encode_tree(tree)})

    def _update_tree(self):
        """
        Updates internal storage.

        Call this whenever added or removed from scene or self._tree
        changes or registration status changes.
        """
        # normalization necessary?
        if self.is_registered() and self.scene() is not None:
            if self.pos() != QtCore.QPointF(0, 0):
                n_tree = self._get_normalize_tree()
                self.setPos(0, 0)
                self._set_tree(n_tree)
                return

        # re-root necessary?
        if self.scene() is not None:
            re_tree = self._reroot_to_possible_input(self._tree)
            if re_tree != self._tree:
                self._set_tree(re_tree)
                return

        # okay, then update internals
        self._update_data_structures()
        self._update_edge_indicators()
        self._update_shape()
        if self.is_registered() and self.scene() is not None:
            self._update_connections()

    def _update_data_structures(self):
        """
        Update derived data structures.

        Like lines, edges that are derived from self._tree.
        """
        # collect all lines
        self._lines = list(self._iter_lines(self._tree))

        # collect all edges
        self._edges = set(self._iter_edges(self._tree))

    def _update_edge_indicators(self):
        # delete old
        for indicator in self._edge_indicators:
            indicator.setParentItem(None)

        # collect all edge indicators
        def iter_edge_indicators(tree, root=True):
            for point, children in tree.items():
                if len(children) >= (3 if root else 2):
                    yield LineEdgeIndicator(self, QtCore.QPointF(*point))
                yield from iter_edge_indicators(children, False)

        self._edge_indicators = list(iter_edge_indicators(self._tree))

    def _update_shape(self):
        """
        Updates the geometry of the line tree graphics items.

        Do not call this function directly, it is called by _update_tree.
        """
        self.prepareGeometryChange()
        bounding_rect = QtCore.QRectF(0, 0, 0, 0)
        poly = QtGui.QPolygonF()
        for line in self._lines:
            l_bounding_rect = self._line_to_col_rect(line)
            poly = poly.united(QtGui.QPolygonF(l_bounding_rect))
            bounding_rect = bounding_rect.united(l_bounding_rect)

        shape_path = QtGui.QPainterPath()
        shape_path.addPolygon(poly)
        self._shape = shape_path
        self._rect = bounding_rect

    def _update_connections(self):
        """
        Updates connections to Connectors.
        """
        # Connect connectors
        for con_item in self._get_all_colliding_connectors(self._tree):
            if con_item.is_registered():
                con_item.connect(self)

    def connect(self, con_item):
        if con_item.is_input():
            delay = self._length_to(con_item.endPoint().toTuple()) * \
                self._delay_per_gridpoint / self.scene().get_grid_spacing()

            # disconnect if connected
            key = (con_item.id(), con_item.index())
            if key in self._connected_outputs:
                out_port = self._connected_outputs.index(key)
                self._connected_outputs[out_port] = con_item.id()
                self.scene().interface().disconnect(self.id(), out_port)
            else:
                out_port = len(self._connected_outputs)
                self._connected_outputs.append(key)
            # connect
            self.scene().interface().connect(
                self.id(), out_port,
                con_item.id(), con_item.index(), delay)
        else:
            # for outputs we need to update our tree (re-rooting)
            # in this process connections will be discovered by its own
            self._update_tree()

    def _get_normalize_tree(self):
        """Returns tree that is normalized to scene coordinates."""
        def _normalize_subtree(tree):
            new_tree = {}
            for point, children in tree.items():
                new_point = self.mapToScene(*point).toTuple()
                new_tree[new_point] = _normalize_subtree(children)
            return new_tree
        return _normalize_subtree(self._tree)

    def _iter_lines(self, tree, __origin=None):
        """
        Iterator over all lines in the given tree.

        :param tree: given tree
        :return: list of QLineF

        Note: __origin is for internal use only!
        """
        for destination, children in tree.items():
            if __origin is not None:
                yield QtCore.QLineF(QtCore.QPointF(*__origin),
                                    QtCore.QPointF(*destination))
            yield from self._iter_lines(children, destination)

    def _iter_edges(self, tree):
        """
        Iterator over all edges in the given tree.

        :param tree: given tree
        """
        for point, children in tree.items():
            yield point
            yield from self._iter_edges(children)

    def _get_root(self, tree):
        """Returns root of given tree"""
        if len(tree) == 0:
            return None
        else:
            return list(self._tree.keys())[0]

    def _get_all_colliding_connectors(self, tree, scene=None):
        """Return all colliding connectors."""
        if scene is None:
            scene = self.scene()

        con_items = set()
        for line in self._iter_lines(tree):
            l_bounding_rect = self._line_to_col_rect(line)
            for item in scene.items(l_bounding_rect):
                if isinstance(item, ConnectorItem) and \
                        l_bounding_rect.contains(item.endPoint()):
                    con_items.add(item)
        return list(con_items)

    def numer_of_driving_inputs(self, scene=None):
        """Returns number of inputs of the Linetree."""
        input_count = 0
        for con_item in self._get_all_colliding_connectors(self._tree, scene):
            if not con_item.is_input() and con_item.is_registered():
                input_count += 1
        return input_count

    def _reroot_to_possible_input(self, tree):
        """
        Re-roots tree to possible input.

        :return: Changed tree
        """
        # Find all inputs
        inputs = []
        for con_item in self._get_all_colliding_connectors(tree):
            if not con_item.is_input() and con_item.is_registered():
                inputs.append(con_item)

        if len(inputs) > 1:
            raise Exception("LineTree cannot be driven by more than "
                            "one input.")
        elif len(inputs) == 1:
            con_item = inputs[0]
            # make sure input is root of the tree
            new_root = con_item.endPoint().toTuple()
            if new_root != self._get_root(tree):
                # re-root tree to new input
                tree = copy.deepcopy(tree)
                if new_root not in self._iter_edges(tree):
                    tree = self._split_line_of_tree(self._tree, new_root)
                return self._reroot(tree, new_root)

        return tree

    def _length_to(self, point):
        """
        Get delay from root to given point of tree.

        :param point: destination point as tuple
        """
        found = False

        def iter_lines(tree, origin=None):
            nonlocal found
            for destination, children in tree.items():
                if origin is not None:
                    index = origin[0] == destination[0]  # vertical line?
                    length = (destination[index] - origin[index])
                    # point on same straight?
                    if point[not index] == origin[not index]:
                        delta = (point[index] - origin[index])
                        # point on line?
                        if 0 <= delta <= length or length <= delta <= 0:
                            found = True
                            return abs(delta)
                else:
                    length = 0
                res = abs(length) + iter_lines(children, destination)
                if found:
                    return res
            return 0

        res = iter_lines(self._tree)
        if not found:
            raise Exception("point is not part of tree")
        return res

    @staticmethod
    def _reroot(tree, new_root):
        """Reroot the tree with given new root."""
        tree = copy.deepcopy(tree)
        if len(tree) == 0 or new_root == list(tree.keys())[0]:
            return tree

        def helper(tree):
            for node, children in tree.items():
                if node == new_root:
                    return node, children, {node: children}
                else:
                    res = helper(children)
                    if res is not None:
                        parent_node, parent_children, res_tree = res
                        del children[parent_node]
                        parent_children[node] = children
                        return node, children, res_tree

        res = helper(tree)
        if res is None:
            raise Exception("new_root not found in tree")
        return res[-1]

    def _split_line_of_tree(self, tree, point):
        """Split line in tree into two lines at given point (as tuple)."""
        tree = copy.deepcopy(tree)

        class ItemFound(Exception):
            pass

        def helper(tree):
            for node, children in tree.items():
                for child in children:
                    line = QtCore.QLineF(QtCore.QPointF(*node),
                                         QtCore.QPointF(*child))
                    rect = self._line_to_col_rect(line)
                    if rect.contains(QtCore.QPointF(*point)):
                        children[point] = {child: children[child]}
                        del children[child]
                        raise ItemFound()
                helper(children)

        try:
            helper(tree)
        except ItemFound:
            pass
        else:
            raise Exception("Point not found in tree")
        return tree

    def _merge_root_lines_of_tree(self, tree):
        """
        Merge lines at the root of given tree.

        Two lines can be merged, if they have the same orientation.
        """
        b = list(tree)[0]
        if len(tree[b]) == 2:
            a, c = list(tree[b])
            # check if all points lay on one line
            if a[0] == b[0] == c[0] or a[1] == b[1] == c[1]:
                # remove root and make 'a' the new root
                tree[b][a].update({c: tree[b][c]})
                tree = {a: tree[b][a]}
        assert len(tree) == 1
        return tree

    def merge_tree(self, merge_line_tree):
        """
        Merges two touching trees.

        The two trees must intersect in exactly one point.
        """
        # find all touching points
        col_points = set([edge for edge in self._edges
                          if merge_line_tree.contains(QtCore.QPointF(*edge))] +
                         [edge for edge in merge_line_tree._edges
                          if self.contains(QtCore.QPointF(*edge))])
        if len(col_points) > 1:
            raise Exception("Cannot merge trees")
        col_point = col_points.pop()

        # split trees at collision points
        self_tree = self._tree
        if col_point not in self._edges:
            self_tree = self._split_line_of_tree(self._tree, col_point)
        merge_tree = merge_line_tree._tree
        if col_point not in merge_line_tree._edges:
            merge_tree = self._split_line_of_tree(merge_line_tree._tree,
                                                  col_point)

        # reroot trees to collision point
        new_tree = self._reroot(self_tree, col_point)
        re_merge_tree = self._reroot(merge_tree, col_point)

        # add siblings from other tree to our tree
        new_tree[col_point].update(re_merge_tree[col_point])

        # merge lines at new root, if they have same orientation
        simplified_tree = self._merge_root_lines_of_tree(new_tree)

        self._set_tree(simplified_tree)

    def is_edge(self, scene_point):
        """ Is there an edge at scene_point given as QPointF """
        return scene_point.toTuple() in self._edges

    def _get_nearest_point_of_line(self, scene_point, line):
        """ Get nearest point on given line to given scene_point. """
        grid_point = self.scene().roundToGrid(scene_point)
        vline = line.p2() - line.p1()

        def constrain_to_range(x, l1, l2):
            return max(min(x, max(l1, l2)), min(l1, l2))

        if vline.x() == 0:  # vertical
            return QtCore.QPointF(line.p1().x(), constrain_to_range(
                grid_point.y(), line.p1().y(), line.p2().y()))
        elif vline.y() == 0:  # horizontal
            return QtCore.QPointF(
                constrain_to_range(grid_point.x(),
                                   line.p1().x(), line.p2().x()),
                line.p1().y())
        else:  # somehow tilted
            raise Exception("Found tilted line")

    def get_nearest_point(self, scene_point):
        """ Get nearest point on the line tree to given scene_point. """
        p_nearest = None
        for line in self._lines:
            p = self._get_nearest_point_of_line(scene_point, line)
            if p_nearest is None or \
                    ((scene_point - p).manhattanLength() <
                     (scene_point - p_nearest).manhattanLength()):
                p_nearest = p
        return p_nearest

    def contains_line(self, line):
        """ Returns true if QLineF is fully contained by this line tree """
        radius = self.collision_margin / 2
        l_bounding_rect = self._line_to_col_rect(line, radius)
        return self._shape.contains(l_bounding_rect)

    def boundingRect(self):
        return self._rect

    def shape(self):
        return self._shape

    def on_registration_status_changed(self):
        """Called when registration status changed."""
        if not self.is_registered():
            self._connected_input = None
            self._connected_outputs = []
        self._update_tree()

    def iter_state_line_segments(self):
        """
        Returns iterator of line segments with state information.

        :return: iterator with items of (QLineF, state)
        """
        clock = self.scene().registry().clock()

        def iter_segment(tree, parent_index=None, parent_state=None,
                         origin=None, parent_delay=0):
            longest_delay = parent_delay
            for destination, children in tree.items():
                if origin is not None:
                    is_vertical = origin[0] == destination[0]
                    length = (destination[is_vertical] - origin[is_vertical])
                    delay = (abs(length) * self._delay_per_gridpoint /
                             self.scene().get_grid_spacing())

                    next_index, next_state = yield from \
                        self.iter_state_line_segments_helper(
                            origin, destination, delay, clock, is_vertical,
                            parent_delay, parent_index, parent_state)
                else:
                    delay = 0
                    next_index, next_state = parent_index, parent_state
                subdelay = yield from iter_segment(
                    children, next_index, next_state, destination,
                    delay + parent_delay)
                longest_delay = max(longest_delay, subdelay)
            return longest_delay
        return iter_segment(self._tree)

    # @timeit
    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)

        # debugging
        if self._debug_painting:
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 0, 0, 128)))
            for line in self._lines:
                radius = self.scene().get_grid_spacing() / 4
                rect = self._line_to_col_rect(line, radius)
                painter.drawRect(rect)
            for indicator in self._edge_indicators:
                painter.drawEllipse(indicator.pos(), 50, 50)
