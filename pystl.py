"""
PySTL - a simple package to write STL files

TODO:

- Only supports ASCII STL files for now. Could add binary files
- Make it a class and support context manager (so can do with stl_file as stl:
"""

import math
import struct


def write_stl_header(f, name='', bin=True, num_triangles=0):
    if bin:
        header_str = ''
        f.write(struct.pack("80sI", header_str, num_triangles))
    else:
        f.write('solid ' + name + '\n' )


def write_stl_trailer(f, bin=True):
    if bin:
        # No trailer on binary STL files
        pass
    else:
        f.write('endsolid \n' )

def write_stl_triangle(f, triangle, normal=None, bin=True):
    if bin:
        """ Each triangle is 4 sets of 3 floats - normal, three verticices, then a byte count (which can be used for color)"""
        if not normal:
            normal = calc_normal(triangle)
        data = [ normal[0], normal[1], normal[2],
                 triangle[0][0], triangle[0][1], triangle[0][2],
                 triangle[1][0], triangle[1][1], triangle[1][2],
                 triangle[2][0], triangle[2][1], triangle[2][2],
                 0 ]
        f.write(struct.pack("12fH", *data))
    else:
        if not normal:
            normal = calc_normal(triangle)

        f.write('  facet normal {:.3f} {:.3f} {:.3f}\n'.format(normal[0], normal[1], normal[2]) )
        f.write('    outer loop\n' )
        f.write('      vertex {:.3f} {:.3f} {:.3f}\n'.format(triangle[0][0], triangle[0][1], triangle[0][2]))
        f.write('      vertex {:.3f} {:.3f} {:.3f}\n'.format(triangle[1][0], triangle[1][1], triangle[1][2]))
        f.write('      vertex {:.3f} {:.3f} {:.3f}\n'.format(triangle[2][0], triangle[2][1], triangle[2][2]))
        f.write('    endloop\n' )
        f.write('  endfacet \n')


# def write_stl_bin_header(f, num_triangles):
#     """ Write the header for a binary STL file. The 1st line is 80 characters (usually blank), the 2nd line is a UINT32
#     for the number of triangles.    """
#     header_str = ''
#     f.write(struct.pack("80sI", header_str, num_triangles))


# def write_stl_bin_triangle(f, triangle, normal=None):
#     """ Each triangle is 4 sets of 3 floats - normal, three verticices, then a byte count (which can be used for color)"""
#     if not normal:
#         normal = calc_normal(triangle)
#     data = [ normal[0], normal[1], normal[2],
#              triangle[0][0], triangle[0][1], triangle[0][2],
#              triangle[1][0], triangle[1][1], triangle[1][2],
#              triangle[2][0], triangle[2][1], triangle[2][2],
#              0 ]
#     f.write(struct.pack("12fH", *data))


def length_vector(v):
    """ Return the length of a vector """
    return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)


def unit_vector(v):
    """ return the unit vector for a vector """
    l = length_vector(v)
    return (v[0] / l, v[1] / l, v[2] / l)

    # if l > 0.00001:
    #     return (v[0] / l, v[1] / l, v[2] / l)
    # else:
    #     print('Got zero length vector!')   # ???
    #     raise RuntimeError
    #     return (0.0, 0.0, 0.0)


def calc_normal(t):
    """ Return the normal for a triangle. Make sure it's a unit vector """
    # U = pt2 - pt1
    # V = pt3 - pt1
    # nx = UyVz - UzVy
    # ny = UzVx - UxVz
    # nz = UxVy - UyVx
    u = (t[1][0] - t[0][0], t[1][1] - t[0][1], t[1][2] - t[0][2])
    v = (t[2][0] - t[0][0], t[2][1] - t[0][1], t[2][2] - t[0][2])

    nx = u[1]*v[2] - u[2]*v[1]
    ny = u[2]*v[0] - u[0]*v[2]
    nz = u[0]*v[1] - u[1]*v[0]
    return unit_vector((nx, ny, nz))


if __name__ == '__main__':
    stl_name = 'bin_stl_test.stl'
    num_triangles=2
    v1 = (0.0, 0.0, 0.5)
    v2 = (0.0, 1.0, 0.0)
    v3 = (1.0, 1.0, 0.5)
    v4 = (1.0, 0.0, 0.0)
    t1 = (v1,v2,v4)
    t2 = (v2,v3,v4)
    with open(stl_name, 'wb') as f:
        # write_stl_bin_header(f, num_triangles)
        # write_stl_bin_triangle(f, t1, normal=None)
        # write_stl_bin_triangle(f, t2, normal=None)
        write_stl_header(f, bin=True, num_triangles=num_triangles)
        write_stl_triangle(f, t1, normal=None, bin=True)
        write_stl_triangle(f, t2, normal=None, bin=True)