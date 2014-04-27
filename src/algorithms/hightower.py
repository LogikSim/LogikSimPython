#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Apr 27, 2014

@author: Christian
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
                if is_point_out_bounds(point):
                    break
                point = next
            return point
        if orientation is horizontal:
            return (find_bound(point, lambda left: (left[0] - 1, left[0])),
                    find_bound(point, lambda left: (left[0] + 1, left[0])))
        else:
            return (find_bound(point, lambda left: (left[0], left[0] - 1)),
                    find_bound(point, lambda left: (left[0], left[0] + 1)))
        
    while not no_escape_flag[a] or not no_escape_flag[b]:
        if not no_escape_flag[a]:
            object = a
            object_point = L_e[object][-1]
            target = not object
            #
            # escape algorithm
            #
            if orientation_flag[object] is horizontal:
                # construct horizontal line escape
                new_line = get_same_line(object_point, 
                                         orientation_flag[object])
                lines[object][orientation_flag[object]].append(new_line)
                # does line intersect with any entry in target list
                for line in lines[target][not orientation_flag[object]]:
                    if do_lines_intersect(line, new_line):
                        return #TODO: return list
                
                #
                # find escape point (process I)
                #
                
                #TODO: refactoring possible, do not need to calculate
                #    escape lines twice --> cache decorator
                hor_escape_line = get_same_line(object_point, horizontal)
                ver_escape_line = get_same_line(object_point, vertical)
                
                # find extremities of horizontal cover
                f1, f3 = get_same_line((ver_escape_line[0], 
                                        ver_escape_line[0] - 1), horizontal)
                f2, f4 = get_same_line((ver_escape_line[1], 
                                        ver_escape_line[1] + 1), horizontal)
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
                    orientation_flag[object] = vertical
                    L_e[object].append(e)
                
                if not found:
                    # find extremities of vertical cover
                    # TODO: refactor: abstract similar code for vertical cover
                    f1, f3 = get_same_line((hor_escape_line[0] - 1, 
                                            hor_escape_line[0]), vertical)
                    f2, f4 = get_same_line((hor_escape_line[1] + 1, 
                                            hor_escape_line[1]), vertical)
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
                        orientation_flag[object] = horizontal
                        L_e[object].append(e)
                # find escape point (process II)
            else:
                # construct vertical line escape
            
            #end escape algorithm
        
        
        if intersect_flag:
            return
        
        if not no_escape_flag[b]:
            object = b
            object_point = L_e[object][-1]
            target = not object
            #
            # escape algorithm
            #
    
    return False
    
    start_lines = []
    end_lines = []