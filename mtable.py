#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import re
import sys
import csv
import json

from bs4 import BeautifulSoup


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
        """header = [{'field': 'key1', 'title': ''}, {'field': 'key2', }...]
        data = [{'key1': 'value1', 'key2': 'value2', ...}, ...]
        """
        if not header:
            header = [{'field': k, 'title': k} for k in data[0]]
        if not isinstance(header[0], dict):
            header = [{'field': k, 'title': k} for k in header]
        for h in header:
            self._header.append({
                'data': self.decode(h['title'], encoding),
                'format': lambda x: '%s' % x,
                'align': 'center',
                'MB': 0,
            })
        for dd in data:
            row = []
            for h in header:
                row.append({
                    'data': self.decode(dd.get(h['field']), encoding),
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

    def is_empty(self):
        return len(self._header) == 0 and self.column_count() == 0

    def is_invalid(self):
        cols = self.column_count()
        if self._header:
            if len(self._header) != cols:
                return True
        for row in self._data:
            if len(row) != cols:
                return True
        return False

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
    def from_rst(rst_text, header=True):
        def parse_table1(text):
            header = None
            data = []
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.startswith('+-'):
                    continue
                if line.startswith('+='):
                    header = data.pop(-1)
                    continue
                line = line.strip('|')
                data.append([item.strip() for item in line.split('|')])

            mt = MarkupTable()
            mt.set_data(data, header)
            return mt

        def parse_table2(text):
            header = None
            data = []
            for line in text.split('\n'):
                line = line.strip()
                while '  ' in line:
                    line = line.replace('  ', ' ')
                if not line:
                    continue
                if line.startswith('=='):
                    if data:
                        header = data.pop(-1)
                    continue
                data.append(line.split(' '))

            mt = MarkupTable()
            mt.set_data(data, header)
            return mt

        tokens = [
            ('table1',
             re.compile(
                 r'''(\r\n?|\n|^)( *)\+-[\-+]{3,}((\r\n?|\n)\2[\|+].+)+\2[\-+]{3,}(\r\n?|\n|$)''',
                 re.UNICODE),
             ),
            ('table2',
             re.compile(
                 r'''(\r\n?|\n|^)( *)={2,} +=[= ]+((\r\n?|\n)\2.{4,})+\2={2,} [= ]+(\r\n?|\n$)''',
                 re.UNICODE),
             ),
        ]
        tables = []
        for key, tok in tokens:
            mo_list = tok.finditer(rst_text)
            for mo in mo_list:
                mt = eval('parse_%s' % key)(mo.group(0))
                tables.append(mt)
        return tables

    @staticmethod
    def from_md(md_text):
        def parse_table(text):
            header = None
            data = []
            for line in text.split('\n'):
                line = line.strip()
                while '  ' in line:
                    line = line.replace('  ', ' ')
                if not line:
                    continue
                line = line.strip('|')
                data.append([item.strip() for item in line.split('|')])

            if data[1][0].startswith('--'):
                header = data.pop(0)
                data.pop(0)

            mt = MarkupTable()
            mt.set_data(data, header)
            return mt

        tok = re.compile(
            r'''(\r\n?|\n|^)( *)\|.+\| *(\r\n?|\n)\2\|[ \-\|]+ *((\r\n?|\n)\2\|.+\| *)+(\r\n?|\n|$)''',
            re.UNICODE)
        tables = []
        mo_list = tok.finditer(md_text)
        for mo in mo_list:
            mt = parse_table(mo.group(0))
            tables.append(mt)
        return tables

    @staticmethod
    def from_txt(text, delimeter=None):
        """+ '|' as table column separator
        + may miss end column
        + null item
        """
        delimeter = delimeter or '|'
        column = 0
        header = None
        data = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('+'):
                line = line.strip('+')
                row = [item.strip() for item in line.split('+')]
                if row[0].startswith('--') or row[0].startswith('=='):
                    if data and not header:
                        header = True
                continue
            line = line.strip(delimeter)
            row = [item.strip() for item in line.split(delimeter)]
            column = max(len(row), column)
            if row[0].startswith('--') or row[0].startswith('=='):
                if data and not header:
                    header = True
            else:
                data.append(row)

        # fix data
        for row in data:
            diff = column - len(row)
            row.extend([''] * diff)
        if header:
            header = data.pop(0)

        mt = MarkupTable()
        mt.set_data(data, header)
        return mt

    @staticmethod
    def from_csv(fobj, header=True):
        mt = MarkupTable()
        reader = csv.reader(fobj)
        if header:
            mt.feed_header(reader.__next__())
        for row in reader:
            mt.feed([row])
        mt.feed_done()
        return mt

    @staticmethod
    def from_html(html_text):
        def strip_text(text):
            text = text.replace('\r\n', ' ')
            text = text.replace('\r', ' ')
            text = text.replace('\n', ' ')
            text = text.replace('\t', ' ')
            while '  ' in text:
                text = text.replace('  ', ' ')
            return text

        tables = []
        soup = BeautifulSoup(html_text, 'html5lib')
        for table in soup.find_all('table'):
            mt = MarkupTable()
            column_count = 0
            for tr in table.find_all('tr'):
                row = []
                if not mt._header and tr.find('th'):
                    for th in tr.find_all('th'):
                        text = strip_text(' '.join(th.stripped_strings))
                        row.append(text)
                        if th.get('colspan'):
                            row.extend([' '] * (int(th.get('colspan')) - 1))
                    mt.feed_header(row)
                    column_count = len(row)
                elif tr.find('td'):
                    for td in tr.find_all('td'):
                        text = strip_text(' '.join(td.stripped_strings))
                        row.append(text)
                        if td.get('colspan'):
                            row.extend([' '] * (int(td.get('colspan')) - 1))
                    if column_count == 0:
                        column_count = len(row)
                    diff = column_count - len(row)
                    row.extend([None] * diff)
                    mt.feed([row])
            mt.feed_done()
            tables.append(mt)
        return tables

    def to_rst(self, style=None):
        """two styles: False or True
        """
        if self.is_empty() or self.is_invalid():
            return ''
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
        if self.is_empty() or self.is_invalid():
            return ''
        t = []
        widths = self._calc_widths()
        v_separator = '|'
        th_s = [v_separator]
        for w in widths:
            th_s.append(self._left_padding + '-' * w + self._right_padding)
            th_s.append(v_separator)
        # header
        if self._header:
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
        if self.is_empty() or self.is_invalid():
            return ''
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
        else:
            print('\n'.join(html) + '\n')

    def to_tab(self):
        if self.is_empty() or self.is_invalid():
            return ''
        data = []
        if self._header:
            row_data = []
            for column in range(self.column_count()):
                row_data.append(self.get_item_text(0, column, header=True))
            data.append('\t'.join(row_data))
        for row in range(self.row_count()):
            row_data = []
            for column in range(self.column_count()):
                row_data.append(self.get_item_text(row, column))
            data.append('\t'.join(row_data))
        return '\n'.join(data)

    def to_csv(self, filename):
        if self.is_empty() or self.is_invalid():
            return ''
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

    def to_json(self, filename):
        dict_data = {}
        header = []
        if self._header:
            for x in range(self.column_count()):
                header.append(self.get_data(0, x, header=True))
        dict_data['header'] = header
        data = []
        if header:
            for y in range(self.row_count()):
                row = {}
                for x in range(self.column_count()):
                    row[header[x]] = self.get_data(y, x)
                data.append(row)
        else:
            for y in range(self.row_count()):
                row = []
                for x in range(self.column_count()):
                    row.append(self.get_data(y, x))
                data.append(row)

        dict_data['data'] = data
        with open(filename, 'w') as f:
            json.dump(dict_data, f)
