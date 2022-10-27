#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@time    : 2019/5/21 16:27
@file    : gsea.py
"""
from svglib.svglib import svg2rlg
import sys


def svg_convert(fs):
    '''
    修改图片转换为并行
    '''
    print 'fs type is {} {}'.format(type(fs), fs)
    (f, out_f) = fs
    drawing = svg2rlg(f)
    renderPDF.drawToFile(drawing, out_f)


if __name__ == '__main__':
    svg = sys.argv[1]
    pdf = sys.argv[2]
    svg_convert((svg, pdf))
