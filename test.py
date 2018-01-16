#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import mtable


def test_rst():
    header = ['abc', 'bcd', 'cde', 'def']
    data = [
        ['str1', 1, 1.1, None],
        ['str2', 2, 2.2, None],
        ['str3', 3, 3.3, None],
        ['str4', 4, 4.4, None],
    ]
    table = mtable.MarkupTable()
    table.setData(data, header)
    print('rst table\n-------------')
    print(table.rst_table())
    print('rst table with nosep\n---------------------')
    print(table.rst_table('nosep'))
    # no header
    table2 = mtable.MarkupTable()
    table2.setData(data)
    print('rst table with no header\n-------------------------------')
    print(table2.rst_table())
    print('rst table with no header and nosep\n----------------------------------')
    print(table2.rst_table('nosep'))


if __name__ == '__main__':
    test_rst()
