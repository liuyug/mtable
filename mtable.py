#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import sys
import csv

from bs4 import BeautifulSoup
import chardet


AlignSymbol = {
    'left': '<',
    'center': '^',
    'right': '>',
}

CjkRange = (  # UTF-8
    (0x2E80, 0x9FC3),
    (0xAC00, 0xD7A3),
    (0xF900, 0xFAFF),
    (0xFE30, 0xFE4F),
    (0xFF01, 0xFF60),
    (0xFFE0, 0xFFE6),
)


class MarkupTable(object):
    _header = None
    _data = None
    _columns_width = None
    _left_padding = ' '
    _right_padding = ' '
    _null_char = '--'

    def __init__(self):
        self._header = []
        self._data = []
        self._columns_width = []

    def __repr__(self):
        return '<Markup Table: %s rows, %s cols>' % (
            self.row_count(), self.column_count()
        )

    def set_data(self, data, header=None, encoding=None):
        """header = ['title1', 'title2', ...]
        data = [['value1', 'value2', ...], ...]
        """
        if header:
            for h in header:
                self._header.append({
                    'data': self.decode(h, encoding),
                    'format': lambda x: '%s' % x,
                    'align': 'center',
                    'MB': 0,
                })
        for dd in data:
            row = []
            for d in dd:
                row.append({
                    'data': self.decode(d, encoding),
                    'format': lambda x: '%s' % x,
                    'align': 'left',
                    'MB': 0,
                })
            self._data.append(row)
        self._columns_width = [0] * self.column_count()

    def set_dict_data(self, data, header=None, encoding=None):
        """header = ['key1', 'key2', ...]
        data = [{'key1': ,'value1', 'key2': 'value2', ...}, ...]
        """
        if not header:
            header = list(data[0].keys())
        for h in header:
            self._header.append({
                'data': self.decode(h, encoding),
                'format': lambda x: '%s' % x,
                'align': 'center',
                'MB': 0,
            })
        for dd in data:
            row = []
            for h in header:
                row.append({
                    'data': self.decode(dd[h], encoding),
                    'format': lambda x: '%s' % x,
                    'align': 'left',
                    'MB': 0,
                })
            self._data.append(row)
        self._columns_width = [0] * self.column_count()

    def feed_header(self, header, encoding=None):
        for h in header:
            self._header.append({
                'data': self.decode(h, encoding),
                'format': lambda x: '%s' % x,
                'align': 'center',
                'MB': 0,
            })

    def feed(self, data, encoding=None):
        for dd in data:
            row = []
            for d in dd:
                row.append({
                    'data': self.decode(d, encoding),
                    'format': lambda x: '%s' % x,
                    'align': 'left',
                    'MB': 0,
                })
            self._data.append(row)

    def feed_done(self):
        self._columns_width = [0] * self.column_count()

    def clearall(self):
        self._header = []
        self._data = []
        self._columns_width = []

    def row_count(self):
        return len(self._data)

    def column_count(self):
        return len(self._data[0]) if self._data else 0

    def decode(self, value, encoding=None):
        if not encoding or not isinstance(value, str):
            return value
        if sys.version_info.major == 3:
            return value.encode(encoding).decode('UTF-8')
        else:
            return value.decode(encoding)

    def _calc_widths(self, columns=None):
        if columns is None:
            columns = range(self.column_count())
        elif isinstance(columns, int):
            columns = [columns]
        for column in columns:
            # header
            if self._header:
                item = self.get_item(0, column, header=True)
                mb = self.cjk_count(self.get_item_text(0, column, header=True))
                self._columns_width[column] = \
                    len(self.get_item_text(0, column, header=True)) + mb
                item['MB'] = mb
            # data
            for row in range(self.row_count()):
                item = self.get_item(row, column)
                mb = self.cjk_count(self.get_item_text(row, column))
                w = len(self.get_item_text(row, column)) + mb
                self._columns_width[column] = max(w, self._columns_width[column])
                item['MB'] = mb
        return self._columns_width

    @staticmethod
    def cjk_count(text):
        count = 0
        for ch in text:
            for b, e in CjkRange:
                if b <= ord(ch) <= e:
                    count += 1
                    break
        return count

    def get_item(self, row, column, header=False):
        if header:
            return self._header[column]
        else:
            return self._data[row][column]

    def get_item_text(self, row, column, header=False):
        item = self.get_item(row, column, header)
        value = item['data']
        if value is None:
            text = self._null_char
        else:
            text = item['format'](value)
        return text

    def set_align(self, align, rows=None, columns=None):
        """align: left, right, center
        """
        if rows is None:
            rows = range(self.row_count())
        if isinstance(rows, int):
            rows = [rows]
        if columns is None:
            columns = range(self.column_count())
        if isinstance(columns, int):
            columns = [columns]
        for row in rows:
            for column in columns:
                self._data[row][column]['align'] = align

    def set_format(self, fmt_func, rows=None, columns=None):
        if rows is None:
            rows = range(self.row_count())
        if isinstance(rows, int):
            rows = [rows]
        if columns is None:
            columns = range(self.column_count())
        if isinstance(columns, int):
            columns = [columns]
        for row in rows:
            for column in columns:
                self._data[row][column]['format'] = fmt_func

    def get_data(self, row, column, role='data', header=False):
        item = self.get_item(row, column, header)
        return item.get(role)

    def get_view_data_item(self, row, column, header=False):
        """call before function _calc_widths
        """
        item = self.get_item(row, column, header)
        width = self._columns_width[column] - item['MB']
        align = AlignSymbol.get(item['align'])
        text = self.get_item_text(row, column, header)
        view = u'{:{align}{width}}'.format(text, align=align, width=width)
        return view

    @staticmethod
    def from_csv(filename, header=True):
        mt = MarkupTable()
        with open(filename, 'rb') as f:
            encoding = chardet.detect(f.read(4096)).get('encoding')
            if not encoding or encoding == 'ascii':
                encoding = 'utf-8'
        with open(filename, 'rt', encoding=encoding, newline='') as f:
            reader = csv.reader(f)
            if header:
                mt.feed_header(reader.__next__())
            for row in reader:
                mt.feed([row])
        mt.feed_done()
        return mt

    @staticmethod
    def from_html(filename):
        with open(filename, 'rb') as f:
            encoding = chardet.detect(f.read(4096)).get('encoding')
            if not encoding or encoding == 'ascii':
                encoding = 'utf-8'
        tables = []
        with open(filename, 'rt', encoding=encoding, newline='') as f:
            soup = BeautifulSoup(f.read(), 'html5lib')
            for table in soup.find_all('table'):
                mt = MarkupTable()
                for tr in table.find_all('tr'):
                    row = []
                    if tr.find('th'):
                        for th in tr.find_all('th'):
                            row.append(th.string)
                        mt.feed_header(row)
                    else:
                        for td in tr.find_all('td'):
                            row.append(td.string)
                        mt.feed([row])
                mt.feed_done()
                tables.append(mt)
        return tables

    def to_rst(self, style=None):
        """two styles: False or True
        """
        t = []
        widths = self._calc_widths()
        if style:
            v_separator = ' '
            c_separator = ' '
            th_s = []
            tr_s = []
        else:
            v_separator = '|'
            c_separator = '+'
            th_s = [c_separator]
            tr_s = [c_separator]
        for w in widths:
            tr_s.append('-' * (
                len(self._left_padding) + w + len(self._right_padding)))
            tr_s.append(c_separator)
            th_s.append('=' * (
                len(self._left_padding) + w + len(self._right_padding)))
            th_s.append(c_separator)
        # header
        if self._header:
            if style:
                t.append(''.join(th_s))
                tr = []
            else:
                t.append(''.join(tr_s))
                tr = [v_separator]
            for col in range(self.column_count()):
                tr.append(self._left_padding)
                tr.append(self.get_view_data_item(0, col, header=True))
                tr.append(self._right_padding)
                tr.append(v_separator)
            t.append(''.join(tr))
            t.append(''.join(th_s))
        else:
            if style:
                t.append(''.join(th_s))
            else:
                t.append(''.join(tr_s))
        # data
        for row in range(self.row_count()):
            if style:
                tr = []
            else:
                tr = [v_separator]
            for column in range(self.column_count()):
                tr.append(self._left_padding)
                tr.append(self.get_view_data_item(row, column))
                tr.append(self._right_padding)
                tr.append(v_separator)
            t.append(''.join(tr))
            if not style:
                t.append(''.join(tr_s))
        if style:
            t.append(''.join(th_s))
        return '\n'.join(t) + '\n'

    def to_md(self):
        if not self._header:
            return 'Markdown Table must have a Header.'
        t = []
        widths = self._calc_widths()
        v_separator = '|'
        th_s = [v_separator]
        for w in widths:
            th_s.append('-' * (
                len(self._left_padding) + w + len(self._right_padding)))
            th_s.append(v_separator)
        # header
        tr = [v_separator]
        for col in range(self.column_count()):
            tr.append(self._left_padding)
            tr.append(self.get_view_data_item(0, col, header=True))
            tr.append(self._right_padding)
            tr.append(v_separator)
        t.append(''.join(tr))
        t.append(''.join(th_s))
        # data
        for row in range(self.row_count()):
            tr = [v_separator]
            for column in range(self.column_count()):
                tr.append(self._left_padding)
                tr.append(self.get_view_data_item(row, column))
                tr.append(self._right_padding)
                tr.append(v_separator)
            t.append(''.join(tr))
        return '\n'.join(t) + '\n'

    def to_html(self, filename=None, full=False, encoding=None):
        html = []
        encoding = encoding or 'UTF-8'
        if full:
            html.append('''<!DOCTYPE html>
<html>
<head>
<meta charset="%s" />
<title>Markup Table</title>
</head>
<body>''' % encoding)
        html.append('<table>')
        # header
        if self._header:
            html.append('<tr>')
            for column in range(self.column_count()):
                html.append('<th>%s</th>' % self.get_item_text(0, column, header=True))
            html.append('</tr>')
        # data
        for row in range(self.row_count()):
            html.append('<tr>')
            for column in range(self.column_count()):
                html.append('<td>%s</td>' % self.get_item_text(row, column))
            html.append('</tr>')
        html.append('</table>')
        if full:
            html.append('</body></html>')
        if filename:
            with open(filename, 'w', encoding=encoding) as f:
                f.write('\n'.join(html) + '\n')
        return '\n'.join(html) + '\n'

    def to_csv(self, filename):
        with open(filename, 'wt', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(
                f, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            if self._header:
                row_data = []
                for column in range(self.column_count()):
                    row_data.append(self.get_item_text(0, column, header=True))
                writer.writerow(row_data)
            for row in range(self.row_count()):
                row_data = []
                for column in range(self.column_count()):
                    row_data.append(self.get_item_text(row, column))
                writer.writerow(row_data)