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
    return (h_line[0][0] <= v_line[0][0] and h_line[1][0] >= v_line[0][0] and
            v_line[0][1] <= h_line[0][1] and v_line[1][1] >= h_line[0][1])


def get_intersect_point(line_a, line_b):
    """ Get intersection point of two intersecting lines. 
    
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
    return (v_line[0][0], h_line[0][1])


def get_normalize_line(line):
    """ Returns normalized line, as used throughout this module
    
    For a given line ((xa, ya), (xb, yb)) returns normalized line
    ((x1, y1), (x2, y2)), while x1 <= x2 and y1 <= y2.
    It is assumed that the line is either horizontal or vertical.
    """
    if line[0][0] > line[1][0] or line[0][1] > line[1][1]:
        return (line[1], line[0])
    else:
        return line
    

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


def hightower_line_search(point_a, point_b, is_point_free, search_rect):
    """ Finds path with minimum bends from point A to B on a 2D grid.
    
    The algorithm is fast, but not guaranteed to find a path, 
    even if it exists.
    
    Based on:
        David W. Hightower. 1969. A solution to line-routing problems on the 
        continuous plane. In Proceedings of the 6th annual Design Automation 
        Conference (DAC '69). ACM, New York, NY, USA, 1-24. 
        http://doi.acm.org/10.1145/800260.809014
    
    Args:
        point_a (tuple): Point A
        point_b (tuple): Point B
        is_point_free (function): function used to probe the grid weather point
                is free or taken. (x, y) -> boolean
        search_rect [(top_left), (bottom_right)]: list of two points (tuple)
                that define the search area. The borders are included.
                It is assumed that there only free points on the border.
    
    Return:
        Minimum path as list of tuples or None if nothing could be found
    """
    def is_point_in_bounds(point):
        return (search_rect[0][0] <= point[0] <= search_rect[1][0] and
                search_rect[0][1] <= point[1] <= search_rect[1][1])
    
    if not (is_point_free(point_a) and is_point_in_bounds(point_a) and
            is_point_free(point_b) and is_point_in_bounds(point_b)):
        return None
    
    # define types
    a, b = True, False
    horizontal, vertical, orientation_both = True, False, object()
    x, y = 0, 1
    
    # define data structures
    L_e = {a: [point_a], b: [point_b]} # escape points
    orientation_flag = {a: orientation_both, b: orientation_both}
    no_escape_flag = {a: False, b: False}
    lines = {a: {horizontal: [], vertical: []}, 
             b: {horizontal: [], vertical: []}}
    intersect_flag = False
    intersection_point = []
    
    def get_same_line(point, orientation):
        """ 
        Construct line for given point and orientation with same 
        is_point_free status as the given point.
        
        Can be used to find escape lines or obstacle lines.
        """
        if not is_point_in_bounds(point):
            if orientation is horizontal:
                return ((search_rect[0][0], point[1]), 
                        (search_rect[1][0], point[1]))
            else:
                return ((point[0], search_rect[0][1]), 
                        (point[0], search_rect[1][1]))
        
        point_free = is_point_free(point)
        def find_bound(point, update):
            while True:
                next = update(point)
                if is_point_free(next) != point_free:
                    break
                if not is_point_in_bounds(next):
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
                    intersection_point.append(get_intersect_point(
                            line, new_line))
                    break
            print("orientation", orientation, "object_point", object_point, 
                  "new_line", new_line, "intersect_flag", intersect_flag)
            return new_line, intersect_flag
        
        # construct or get all escape lines
        escape_line = {}
        if orientation_flag[pivot] in [horizontal, orientation_both]:
            escape_line[horizontal], intersect_flag = \
                    construct_escape_line(horizontal)
        else:
            escape_line[horizontal] = lines[pivot][horizontal][-1]
        if intersect_flag:
            return intersect_flag
        if orientation_flag[pivot] in [vertical, orientation_both]:
            escape_line[vertical], intersect_flag = \
                    construct_escape_line(vertical)
        else:
            escape_line[vertical] = lines[pivot][vertical][-1]
        if intersect_flag:
            return intersect_flag
        
        #
        # find escape point (process I)
        #
        def escape_cover(orientation):
            def grow_line_by_one(line, orientation):
                """ grow line by one point in direction of orientation """
                if orientation is horizontal:
                    return ((line[0][0] - 1, line[0][1]),
                            (line[1][0] + 1, line[1][1]))
                else:
                    return ((line[0][0], line[0][1] - 1),
                            (line[1][0], line[1][1] + 1))
            
            # find extremities of cover
            esc_line = grow_line_by_one(escape_line[not orientation], 
                                        not orientation)
            f1, f3 = get_same_line(esc_line[0], orientation)
            f2, f4 = get_same_line(esc_line[1], orientation)
            f_list = sorted([f1, f2, f3, f4], 
                            key=lambda f: distance(f, object_point))
            print("orientation =", orientation, ", f_list =", f_list)
            
            found = True
            for f in f_list:
                if f == f1 or f == f2:
                    if orientation is horizontal:
                        e = (f[0] - 1, object_point[1])
                    else:
                        e = (object_point[0], f[1] - 1)
                    # test weather it is an escape point not being used
                    if (is_point_on_line(e, escape_line[orientation]) and
                            e not in L_e[pivot]):
                        print("escape_point_found A", e)
                        break
                else:
                    if orientation is horizontal:
                        e = (f[0] + 1, object_point[1])
                    else:
                        e = (object_point[0], f[1] + 1)
                    # test weather it is an escape point not being used
                    if (is_point_on_line(e, escape_line[orientation]) and
                            e not in L_e[pivot]):
                        print("escape_point_found B", e)
                        break
            else:
                found = False
            if found:
                orientation_flag[pivot] = not orientation
                L_e[pivot].append(e)
            return found
        
        found = escape_cover(horizontal)
        if not found:
            found = escape_cover(vertical)
        
        if not found:
            # find escape point (process II)
        
            # TODO
            pass
        
        if not found:
            no_escape_flag[pivot] = True
        
        return intersect_flag
    
    def first_refinement_algorithm(pivot):
        """ p is list of escape points """
        path = L_e[pivot]
        # find escape line of escape point
        orientation = horizontal
        while True:
            for k in reversed(lines[pivot][orientation]):
                if is_point_on_line(intersection_point[0], k):
                    print("found")
                    break
            else: # k not found
                orientation = not orientation
                continue
            break
        
        L = []
        while True:
            for i in range(len(path)):
                point = path[i]
                if is_point_on_line(point, k):
                    del path[i:]
                    L.append(point)
                    if i == 0:
                        return list(reversed(L))
                    # find new k
                    orientation = not orientation
                    for k in lines[pivot][orientation]:
                        if is_point_on_line(point, k):
                            break
                    else:
                        assert False # algorithm broken
                    break
    
    def second_refinement(path):
        return path
        #TODO: fix, paper seems to be incorrect here
        if len(path) > 5:
            pass
        else:
            m = -1
            #TODO: loop over m
            m += 1
            for i in range(1, len(path)):
                if path[i][x] == path[i+1][x]:
                    if path[i][y] >= path[i+1][y]:
                        q = (path[i][0], path[i][y] - m)
                        if q[y] <= path[i+1][y]:
                            continue
                    else:
                        q = (path[i][0], path[i][y] + m)
                        if q[y] >= path[i+1][y]:
                            continue
                    # horizontal escape line through q
                    k = get_same_line(q, horizontal)
                else:
                    if path[i][x] < path[i+1][x]:
                        q = (path[i][0] + m, path[i][y])
                        if q[x] >= path[i+1][x]:
                            continue
                    else:
                        q = (path[i][0] - m, path[i][y])
                        if q[x] >= path[i+1][x]:
                            continue
                    # vertical escape line through q
                    k = get_same_line(q, vertical)
                if (len(path) - 1 - i) <= 2:
                    break
                j = i + 2
                while (len(path) - 1 - j) > 0:
                    test_line = get_normalize_line(path[j], path[j+1])
                    if do_lines_intersect(k, test_line):
                        p_prime = get_intersect_point(k, test_line)
                    j += 2
            #TODO: H
    
    #
    # main loop
    #
    pivot = a
    while not no_escape_flag[a] or not no_escape_flag[b]:
        if not no_escape_flag[pivot]:
            print("escape_algorithm", pivot)
            intersect_flag = escape_algorithm(pivot)
        
        if intersect_flag:
            L_a = first_refinement_algorithm(a)
            L_b = first_refinement_algorithm(b)
            if intersection_point[0] in L_a + L_b:
                path = L_a + list(reversed(L_b))
            else:
                path = L_a + intersection_point + list(reversed(L_b))
            return second_refinement(path)
        
        pivot = not pivot
    
    return None # could not find a path
    