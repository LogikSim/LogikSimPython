#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can 
be found in the LICENSE.txt file.
'''

from PySide import QtCore

def find_nearest_point_on_tilted_line(scene, pos, line_item):
    spos = scene.mapToScene(pos)
    def scal_prod(p1, p2):
        return p1.x() * p2.x() + p1.y() * p2.y()
    line = line_item.line()
    
    lvec = line.p2() - line.p1() # line vector
    nvec = QtCore.QPointF(lvec.y(), -lvec.x()) # normal vector
    nvec /= nvec.manhattanLength()
    plvec = line.p1() - spos # point to line vector
    
    distance = scal_prod(plvec, nvec)
    point_on_straight = spos + distance * nvec
    
    p_on_s_vec = point_on_straight - line.p1()
    relative_scale = scal_prod(p_on_s_vec, lvec) / \
            lvec.manhattanLength()**2
    
    if relative_scale < 0:
        return line.p1()
    elif relative_scale > 1:
        return line.p2()
    else:
        return point_on_straight
