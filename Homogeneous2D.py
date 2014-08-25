from matrix import *
from  math import *

def identity2D():
    return Matrix.fromList([[1,0,0],
                            [0,1,0],
                            [0,0,1]])

def rotate2D(x):
    return Matrix.fromList([[cos(x),  sin(x), 0],
                            [-sin(x), cos(x), 0],
                            [0,       0,      1]])

def scale2D(x,y):
    return Matrix.fromList([[x,0,0],
                            [0,y,0],
                            [0,0,1]])

def translate2D(x, y):
    return Matrix.fromList([[1, 0, x],
                            [0, 1, y],
                            [0, 0, 1]])

def point2D(p):
    return Matrix.fromList([[p[0]],
                            [p[1]],
                            [1]])

def tuple2D(v):
    return (v[0][0], v[1][0])
