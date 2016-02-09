"""
PySTL - a simple package to write STL files

TODO:

- Only supports ASCII STL files for now. Could add binary files
- Make it a class and support context manager (so can do with stl_file as stl:
"""

import math

def write_stl_header(f, name=''):
    f.write('solid ' + name + '\n' )

def write_stl_trailer(f):
    f.write('endsolid \n' )

def write_stl_triangle(f, triangle, normal=None):
    if not normal:
        normal = calc_normal(triangle)
        
    f.write('  facet normal {:.3f} {:.3f} {:.3f}\n'.format(normal[0], normal[1], normal[2]) )
    f.write('    outer loop\n' )
    f.write('      vertex {:.3f} {:.3f} {:.3f}\n'.format(triangle[0][0], triangle[0][1], triangle[0][2]))
    f.write('      vertex {:.3f} {:.3f} {:.3f}\n'.format(triangle[1][0], triangle[1][1], triangle[1][2]))
    f.write('      vertex {:.3f} {:.3f} {:.3f}\n'.format(triangle[2][0], triangle[2][1], triangle[2][2]))
    f.write('    endloop\n' )
    f.write('  endfacet \n')


def length_vector(v):
    """ Return the length of a vector """
    return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)

def unit_vector(v):
    """ return the unit vector for a vector """
    l = length_vector(v)

    if l > 0.00001:
        return (v[0] / l, v[1] / l, v[2] / l)
    else:
        print('Got zero length vector!')   # ???
        return (0.0, 0.0, 0.0)


def calc_normal(t):
    """ Return the normal for a triangle. Make sure it's a unit vector """
    # U = pt2 - pt1
    # V = pt3 - pt1
    # nx = UyVz - UzVy
    # ny = UzVx - UxVz
    # nz = UxVy - UyVx
    u = (t[1][0] - t[0][0], t[1][1] - t[0][1], t[1][2] - t[0][2])
    v = (t[2][0] - t[0][0], t[2][1] - t[0][1], t[1][2] - t[0][2])

    nx = u[1]*v[2] - u[2]*v[1]
    ny = u[2]*v[0] - u[0]*v[2]
    nz = u[0]*v[1] - u[1]*v[0]
    return unit_vector((nx, ny, nz))
