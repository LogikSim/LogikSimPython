#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright 2014 The LogikSim Authors. All rights reserved.
Use of this source code is governed by the GNU GPL license that can 
be found in the LICENSE.txt file.
'''

def do_lines_intersect(line_a, line_b):
    """ Test weather two lines intersect. 
    
    It is assumed that one line is horizontal and the other is vertical.
    It is further assumed that the lines have the form ((x1, y1), (x2, y2)),
    while x1 <= x2 and y1 <= y2.
    """
    if line_a[0][1] == line_a[1][1] and line_b[0][0] == line_b[1][0]:
        h_line = line_a
        v_line = line_b
    else:
        h_line = line_b
        v_line = line_a
    return (h_line[0][1] <= v_line[0][1] and h_line[1][1] >= v_line[0][1] and
            v_line[0][0] <= h_line[0][0] and v_line[1][0] >= h_line[0][0])


def is_point_on_line(point, line):
    """ Test weather point is one line.
    
    It is assumed that the line is eather horizontal or vertical.
    It is assumed that the line has the format ((x1, y1), (x2, y2)) and
    x1 <= x2, y1 <= y2.
    """
    return (line[0][0] <= point[0] and line[1][0] >= point[0] and
            line[0][1] <= point[1] and line[1][1] >= point[1])


def distance(point_a, point_b):
    """ Euclidean distance between point A and B. """
    return ((point_a[0] - point_b[0])**2 + (point_a[1] - point_b[1])**2)**0.5


def hightower_line_search(point_a, point_b, is_point_free, is_point_out_bounds):
    """ Finds path with minimum bends from point A to B on a 2D grid.
    
    Reference:
        David W. Hightower. 1969. A solution to line-routing problems on the 
        continuous plane. In Proceedings of the 6th annual Design Automation 
        Conference (DAC '69). ACM, New York, NY, USA, 1-24. 
        http://doi.acm.org/10.1145/800260.809014
    
    Args:
        point_a (tuple): Point A
        point_b (tuple): Point B
        is_point_free (function): function used to probe the grid weather point
                is free or taken. (x, y) -> boolean
        is_point_out_bounds (function): function used to probe the grid weather
                a point is out of the bounding area of the problem.
                (x, y) -> boolean
                It is assumed that there is a ring of free slots just within
                the bounding box
        #TODO: refactoring: think about bounded problem, where is_point_free
                has to be False for sufficiant large or small points
    
    Return:
        Minimum path as list of tuples.
    """
    
    # define types
    a, b = True, False
    horizontal, vertical, orientation_both = True, False, object()
    
    #point = {a: point_a, b: point_b}
    L_e = {a: [point_a], b: [point_b]} # escape points
    orientation_flag = {a: orientation_both, b: orientation_both}
    no_escape_flag = {a: False, b: False}
    lines = {a: {horizontal: [], vertical: []}, 
             b: {horizontal: [], vertical: []}}
    intersect_flag = False
    
    def get_same_line(point, orientation):
        """ 
        Construct line for given point and orientation with same fee 
        status as point.
        
        Can be used to find escape lines or obstacle lines.
        """
        point_free = is_point_free(point)
        def find_bound(point, update):
            while True:
                next = update(point)
                if is_point_free(next) != point_free:
                    break
                if is_point_out_bounds(next):
                    break
                point = next
            return point
        if orientation is horizontal:
            return (find_bound(point, lambda left: (left[0] - 1, left[1])),
                    find_bound(point, lambda left: (left[0] + 1, left[1])))
        else:
            return (find_bound(point, lambda left: (left[0], left[1] - 1)),
                    find_bound(point, lambda left: (left[0], left[1] + 1)))
    
    
    def escape_algorithm(pivot):
        """ Main escape algorithm """
        intersect_flag = False
        object_point = L_e[pivot][-1]
        
        def construct_escape_line(orientation):
            """ Construct new escape line """
            intersect_flag = False
            new_line = get_same_line(object_point, orientation)
            lines[pivot][orientation].append(new_line)
            # does line intersect with any entry in target list
            for line in lines[not pivot][not orientation]:
                if do_lines_intersect(line, new_line):
                    intersect_flag = True
                    break
            return new_line, intersect_flag
        
        # construct or get all escape lines
        if orientation_flag[pivot] in [horizontal, orientation_both]:
            hor_escape_line, intersect_flag = construct_escape_line(horizontal)
        else:
            hor_escape_line, intersect_flag = lines[pivot][horizontal][-1]
        if orientation_flag[pivot] in [horizontal, orientation_both]:
            ver_escape_line, intersect_flag = construct_escape_line(vertical)
        else:
            ver_escape_line = lines[pivot][vertical][-1]
        
        if intersect_flag:
            return intersect_flag
        
        #
        # find escape point (process I)
        #
        
        # find extremities of horizontal cover
        f1, f3 = get_same_line((ver_escape_line[0][0], 
                                ver_escape_line[0][1] - 1), horizontal)
        f2, f4 = get_same_line((ver_escape_line[1][0], 
                                ver_escape_line[1][1] + 1), horizontal)
        f_list = sorted([f1, f2, f3, f4], 
                        key=lambda f: distance(f, object_point))
        
        found = True
        for f in f_list:
            if f == f1 or f == f2:
                e = (f[0] - 1, object_point[1])
                # test weather it is an escape point
                if is_point_on_line(e, hor_escape_line):
                    print("escape_point_found", e)
                    break
            else:
                e = (f[0] + 1, object_point[1])
                # test weather it is an escape point
                if is_point_on_line(e, hor_escape_line):
                    print("escape_point_found", e)
                    break
        else:
            found = False
        if found:
            orientation_flag[pivot] = vertical
            L_e[pivot].append(e)
        
        if not found:
            # find extremities of vertical cover
            # TODO: refactor: abstract similar code for vertical cover
            f1, f3 = get_same_line((hor_escape_line[0][0] - 1, 
                                    hor_escape_line[0][1]), vertical)
            f2, f4 = get_same_line((hor_escape_line[1][0] + 1, 
                                    hor_escape_line[1][1]), vertical)
            f_list = sorted([f1, f2, f3, f4], 
                            key=lambda f: distance(f, object_point))
            
            found = True
            for f in f_list:
                if f == f1 or f == f2:
                    e = (object_point[0], f[1] - 1)
                    # test weather it is an escape point
                    if is_point_on_line(e, ver_escape_line):
                        print("escape_point_found", e)
                        break
                else:
                    e = (object_point[0], f[1] + 1)
                    # test weather it is an escape point
                    if is_point_on_line(e, ver_escape_line):
                        print("escape_point_found", e)
                        break
            else:
                found = False
            if found:
                orientation_flag[pivot] = horizontal
                L_e[pivot].append(e)
        # find escape point (process II)
        
        # TODO
        
        return intersect_flag
    
    #
    # main loop
    #
    pivot = a
    while not no_escape_flag[a] or not no_escape_flag[b]:
        if not no_escape_flag[pivot]:
            intersect_flag = escape_algorithm(pivot)
        
        if intersect_flag:
            print(lines)
            print(L_e)
            return True
        
        pivot = not pivot
    
    return False
    