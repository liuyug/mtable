#!/usr/bin/env python3
# -*- encoding:utf-8 -*-

import mtable


def test_rst():
    header = ['名字', '网站', '备注', '其它']
    data = [
        ['百度', 'www.baidu.com', '搜索，网盘，地图', None],
        ['新浪', 'www.sina.com.cn', '新闻', None],
        ['腾讯', 'www.qq.com', '聊天', '微信'],
        ['网易', 'www.163.com', '邮箱', '１２３'],
    ]
    table = mtable.MarkupTable()
    table.set_data(data, header, encoding='utf8')
    print('''
rst table
---------''')
    print(table.to_rst())
    print('''
rst table with style 1
----------------------''')
    print(table.to_rst(1))

    # no header
    table2 = mtable.MarkupTable()
    table2.set_data(data, encoding='utf8')
    print('''
rst table with no header
------------------------''')
    print(table2.to_rst())
    print('''
rst table with no header and style 1
------------------------------------''')
    print(table2.to_rst(1))

    print('''
md table
--------''')
    print(table.to_md())

    print('''
csv table
---------
output test.csv
    ''')
    table.to_csv('test.csv')
    print('''
csv table
---------
read test.csv
    ''')
    table = mtable.MarkupTable.from_csv('test.csv')
    print(table.to_rst())

    print('''
html table
----------
output test.html
    ''')
    table.to_html('test.html', full=True)
    print('''
html table
----------
read test.html
    ''')
    for table in mtable.MarkupTable.from_html('test.html'):
        print(table.to_rst())


if __name__ == '__main__':
    test_rst()