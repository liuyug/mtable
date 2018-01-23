#!/usr/bin/env python3
# -*- encoding:utf-8 -*-

import sys
import urllib.request
import chardet
import mtable


header = ['名字', '网站', '备注', '其它']
data = [
    ['百度', 'www.baidu.com', '搜索，网盘，地图', None],
    ['新浪', 'www.sina.com.cn', '新闻', None],
    ['腾讯', 'www.qq.com', '聊天', '微信'],
    ['网易', 'www.163.com', '邮箱', '１２３'],
]


def test_rst():
    table = mtable.MarkupTable()
    table.set_data(data, header, encoding='utf8')
    print('''
rst table
---------''')
    print(table.to_rst())
    print(table.to_rst(1))


def test_rst_noheader():
    # no header
    table2 = mtable.MarkupTable()
    table2.set_data(data, encoding='utf8')
    print('''
rst table with no header
------------------------''')
    print(table2.to_rst())
    print(table2.to_rst(1))


def test_md():
    table = mtable.MarkupTable()
    table.set_data(data, header, encoding='utf8')
    print('''
md table
--------''')
    print(table.to_md())


def test_csv():
    table = mtable.MarkupTable()
    table.set_data(data, header, encoding='utf8')
    print('''
csv table
---------
output test.csv
    ''')
    table.to_csv('test.csv')


def test_html():
    table = mtable.MarkupTable()
    table.set_data(data, header, encoding='utf8')
    print('''
html table
----------
output test.html
    ''')
    table.to_html('test.html', full=True)


def test_json():
    table = mtable.MarkupTable()
    table.set_data(data, header, encoding='utf8')
    print('''
json table
----------
output test.json
    ''')
    table.to_json('test.json')


def test_from_csv():
    print('''
csv table
---------
read test.csv
    ''')
    csv_file = 'test.csv'
    with open(csv_file, 'rb') as f:
        encoding = chardet.detect(f.read(4096)).get('encoding')
        if not encoding or encoding == 'ascii':
            encoding = 'utf-8'
    with open(csv_file, 'rt', encoding=encoding, newline='') as f:
        table = mtable.MarkupTable.from_csv(f)
        print(table.to_rst())


def test_from_html():
    print('''
html table
----------
read test.html
    ''')
    html_file = 'test.html'
    with open(html_file, 'rb') as f:
        encoding = chardet.detect(f.read(4096)).get('encoding')
        if not encoding or encoding == 'ascii':
            encoding = 'utf-8'
    with open(html_file, 'rt', encoding=encoding, newline='') as f:
        tables = mtable.MarkupTable.from_html(f.read())
    for table in tables:
        print(table.to_rst())


def test_from_html2():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = 'https://specifications.freedesktop.org/icon-naming-spec/latest/ar01s04.html'

    r = urllib.request.urlopen(url)
    html = r.read()

    encoding = chardet.detect(html).get('encoding')
    if not encoding or encoding == 'ascii':
        encoding = 'utf-8'

    tables = mtable.MarkupTable.from_html(html.decode(encoding, errors='ignore'))
    for table in tables:
        print(table.to_rst())


def test_from_rst():
    print('''
from rst
--------''')
    rst_file = 'test.rst'
    with open(rst_file, 'rb') as f:
        encoding = chardet.detect(f.read(4096)).get('encoding')
        if not encoding or encoding == 'ascii':
            encoding = 'utf-8'
    with open(rst_file, 'rt', encoding=encoding, newline='') as f:
        tables = mtable.MarkupTable.from_rst(f.read())
    for table in tables:
        print(table.to_rst())


def test_from_md():
    print('''
from md
-------''')
    md_file = 'test.md'
    with open(md_file, 'rb') as f:
        encoding = chardet.detect(f.read(4096)).get('encoding')
        if not encoding or encoding == 'ascii':
            encoding = 'utf-8'
    with open(md_file, 'rt', encoding=encoding, newline='') as f:
        tables = mtable.MarkupTable.from_md(f.read())
    for table in tables:
        print(table.to_rst())


def test_from_txt():
    print('''
from text
---------''')
    txt_file = 'test.txt'
    with open(txt_file, 'rb') as f:
        encoding = chardet.detect(f.read(4096)).get('encoding')
        if not encoding or encoding == 'ascii':
            encoding = 'utf-8'
    with open(txt_file, 'rt', encoding=encoding, newline='') as f:
        table = mtable.MarkupTable.from_txt(f.read())
        print(table.to_rst())


if __name__ == '__main__':
    test_rst()
    test_rst_noheader()
    test_md()
    test_html()
    test_csv()
    test_json()
    test_from_html()
    # test_from_html2()
    test_from_csv()
    test_from_rst()
    test_from_md()
    test_from_txt()
