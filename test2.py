#!/usr/bin/env python3
# -*- encoding:utf-8 -*-

import io
import sys
import urllib.request

import chardet
import mtable


def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = 'https://specifications.freedesktop.org/icon-naming-spec/latest/ar01s04.html'

    r = urllib.request.urlopen(url)
    html = r.read()

    encoding = chardet.detect(html).get('encoding')
    if not encoding or encoding == 'ascii':
        encoding = 'utf-8'

    tables = mtable.MarkupTable.from_html(io.StringIO(html.decode(encoding)))
    for table in tables:
        print(table.to_rst())


if __name__ == '__main__':
    main()
