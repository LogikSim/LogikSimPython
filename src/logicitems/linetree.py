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


class LineTree(InsertableItem):
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

        self._connected_input = None  # connected ConnectorItem
        self._connected_outputs = []  # list of connected ConnectorItems

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

        return {'tree': path_to_tree(path)}

    @classmethod
    def GUI_GUID(cls):
        return "00352520-7cf0-43b7-9449-6fca5be8d6dc"

    def selectionRect(self):
        return self._rect

    def apply_update(self, metadata):
        super().apply_update(metadata)

        tree = metadata.get('tree', None)
        if tree is not None and tree != self._tree:
            self._set_tree(tree)

    def _set_tree(self, tree):
        """
        Set new tree and updates internal storage.

        Call this function whenever changing the line tree.
        """
        # update internals
        self._tree = tree
        self._update_data_structures()
        self._update_edge_indicators()
        self._update_shape()
        self._update_connections()

        # TODO: create undo event
        pass

        # notify backend
        self._notify_backend({'tree': tree})

    def _update_data_structures(self):
        """
        Update derived data structures.

        Like lines, edges that are derived from self._tree.
        """
        # collect all lines
        def iter_lines(tree, origin=None):
            for destination, children in tree.items():
                if origin is not None:
                    yield QtCore.QLineF(QtCore.QPointF(*origin),
                                        QtCore.QPointF(*destination))
                for line in iter_lines(children, destination):
                    yield line

        self._lines = list(iter_lines(self._tree))

        # collect all edges
        def iter_edges_as_tuple(tree):
            for point, children in tree.items():
                yield point
                for edge in iter_edges_as_tuple(children):
                    yield edge

        self._edges = set(iter_edges_as_tuple(self._tree))

    def _update_edge_indicators(self):
        # delete old
        for indicator in self._edge_indicators:
            indicator.setParentItem(None)

        # collect all edge indicators
        def iter_edge_indicators(tree, root=True):
            for point, children in tree.items():
                if len(children) >= (3 if root else 2):
                    yield LineEdgeIndicator(self, QtCore.QPointF(*point))
                for indicator in iter_edge_indicators(children, False):
                    yield indicator

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

    def _get_root(self):
        """returns root of tree"""
        keys = list(self._tree.keys())
        if len(keys) == 0:
            return None
        else: return keys[0]

    def _update_connections(self):
        """
        Updates connections to Connectors.
        """
        # TODO: call when position changes

        if not self.is_registered():
            return

        # Disconnect connectors
        if self._connected_input is not None:
            self._connected_input.disconnect()
        self._connected_input = None

        for i, con_item in enumerate(self._connected_outputs):
            self.scene().interface().disconnect(self.id(), i)
        self._input_connectors = []

        # Collect all ConnectorItems
        con_items = set()
        if self.scene() is not None:
            for line in self._lines:
                l_bounding_rect = self._line_to_col_rect(line)
                for item in self.scene().items(l_bounding_rect):
                    if isinstance(item, ConnectorItem) and \
                            l_bounding_rect.contains(item.anchorPoint()):
                        con_items.add(item)

        # Connect input
        for con_item in con_items:
            if not con_item.is_input():
                # tell other item to connect to us
                if con_item.connect(self):
                    assert self._connected_input is None, \
                        'only one output can drive the line-trees'
                    self._connected_input = con_item
                    # make sure input is root of the tree
                    new_root = con_item.anchorPoint().toTuple()
                    if new_root != self._get_root():
                        if new_root not in self._edges:
                            tree = self._split_line_of_tree(self._tree,
                                                            new_root)
                        else:
                            tree = self._tree
                        new_tree = self._reroot(tree, new_root)
                        # TODO: with disabled_undo?
                        self._set_tree(new_tree)

        # Connect output
        for con_item in con_items:
            if con_item.is_input():
                # setup connection in backend
                if con_item.is_registered():
                    self.scene().interface().connect(
                        self.id(), len(self._connected_outputs),
                        con_item.id(), con_item.index())
                    self._connected_outputs.append(con_item)

    @staticmethod
    def _reroot(tree, new_root):
        """Reroot the tree with given new root."""
        tree = copy.deepcopy(tree)

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
        self._update_connections()

    def itemChange(self, change, value):
        res = super().itemChange(change, value)

        # update connections on scene change
        if change is QtGui.QGraphicsItem.ItemSceneHasChanged:
            self._update_connections()

        return res

    def paint(self, painter, option, widget=None):
        # draw lines
        painter.setPen(QtGui.QPen(QtCore.Qt.black))
        for line in self._lines:
            painter.drawLine(line)

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
