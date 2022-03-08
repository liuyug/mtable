#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import re
import sys
import csv
import json
import copy

from bs4 import BeautifulSoup
from wcwidth import wcswidth


VERSION = '0.1.22'


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

    def set_data(self, data, header=None, footer=None, encoding=None):
        """input list format:
        header = ['title1', 'title2', ...]
        data = [['value1', 'value2', ...], ...]
        """
        if header:
            for h in header:
                self._header.append({
                    'title': self.decode(h, encoding),
                    'render': lambda x: '%s' % x,
                    'align': 'left',
                    'MB': 0,
                })
        else:
            # create fake header
            for h in data[0]:
                self._header.append({
                    'title': None,
                    'render': lambda x: '%s' % x,
                    'align': 'left',
                    'MB': 0,
                })
        self._footer = copy.deepcopy(self._header)
        for record in data:
            row = []
            for value in record:
                if isinstance(value, str):
                    value = self.decode(value, encoding)
                row.append({
                    'data': value,
                    'MB': 0,
                })
            self._data.append(row)
        self._columns_width = [0] * self.column_count()

    def set_dict_data(self, data, header=None, footer=None, encoding=None):
        """header = [{'data': 'key1', 'title': '', 'render': func, 'align': 'left'} {'data': 'key2', }...]
        data = [{'key1': 'value1', 'key2': 'value2', ...}, ...]

        data: column field
        title: column display name
        encoding: title encoding
        """
        # table header
        if not header:
            self._header = [{'data': k, 'title': k, 'render': lambda x: '%s' % x, 'align': 'left'} for k in data[0].keys()]
        elif isinstance(header[0], str):
            self._header = [{'data': k, 'title': k, 'render': lambda x: '%s' % x, 'align': 'left'} for k in header]
        else:
            # header is dict
            for h in header:
                item = {
                    'title': self.decode(h['title'], encoding),
                    'render': h.get('render') or (lambda x: '%s' % x),
                    'align': h.get('align') or 'left',
                    'MB': 0,    # width, internal use.
                }
                # for compatiable old field
                if 'data' in h:
                    item['data'] = h['data']
                elif 'field' in h:
                    item['data'] = h['field']
                self._header.append(item)
        # table footer
        if footer:
            pass
        else:
            self._footer = copy.deepcopy(self._header)
        # table data
        for record in data:
            row = []
            for h in self._header:
                value = record.get(h['data'])
                if isinstance(value, str):
                    value = self.decode(value, encoding)
                cell = {
                    'data': value,
                    'MB': 0,
                }
                row.append(cell)
            self._data.append(row)
        self._columns_width = [0] * self.column_count()

    def set_dataframe_data(self, df, encoding='utf-8'):
        for h in df.columns:
            self._header.append({
                'title': self.decode(h, encoding),
                'render': lambda x: '%s' % x,
                'align': 'left',
                'MB': 0,
            })
        self._footer = copy.deepcopy(self._header)
        for idx in df.index:
            row = []
            for h in df.columns:
                value = df.loc[idx, h]
                if isinstance(value, str):
                    value = self.decode(value, encoding)
                row.append({
                    'data': df.loc[idx, h],
                    'MB': 0,
                })
            self._data.append(row)
        self._columns_width = [0] * self.column_count()

    def feed_header(self, header, footer=None, encoding=None):
        """create table by step with list mode
        """
        for h in header:
            self._header.append({
                'title': self.decode(h, encoding),
                'render': lambda x: '%s' % x,
                'align': 'left',
                'MB': 0,
            })
        self._footer = copy.deepcopy(self._header)

    def feed(self, data, encoding=None):
        for record in data:
            row = []
            for value in record:
                if isinstance(value, str):
                    value = self.decode(value, encoding)
                row.append({
                    'data': value,
                    'MB': 0,
                })
            self._data.append(row)

    def feed_done(self):
        self._columns_width = [0] * self.column_count()

    def clearall(self):
        self._header = []
        self._footer = []
        self._data = []
        self._columns_width = []

    def row_count(self):
        return len(self._data)

    def column_count(self):
        return len(self._header)

    def is_empty(self):
        return len(self._header) == 0 and self.column_count() == 0

    def is_invalid(self):
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
                cell = self.get_cell(0, column, header=True)
                text = self.render_data(0, column, header=True)
                mb = self.cjk_count(text)
                w = wcswidth(text)
                if w < 1:
                    w = len(text) + mb
                self._columns_width[column] = w
                cell['MB'] = mb
            # data
            for row in range(self.row_count()):
                cell = self.get_cell(row, column)
                text = self.render_data(row, column, header=False)
                mb = self.cjk_count(text)
                w = wcswidth(text)
                if w < 1:
                    w = len(text) + mb
                self._columns_width[column] = max(w, self._columns_width[column])
                cell['MB'] = mb
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

    def get_cell(self, row, column, header=False):
        if header:
            return self._header[column]
        else:
            return self._data[row][column]

    def set_align(self, align, rows=None, columns=None):
        """align: left, right, center
        """
        if rows is None:
            rows = range(self.row_count())
        elif isinstance(rows, int):
            rows = [rows]
        if columns is None:
            columns = range(self.column_count())
        elif isinstance(columns, int):
            columns = [columns]
        for row in rows:
            for column in columns:
                self._data[row][column]['align'] = align

    def set_render(self, render_func, rows=None, columns=None):
        """set render function of cell
        """
        if rows is None:
            rows = range(self.row_count())
        elif isinstance(rows, int):
            rows = [rows]
        if columns is None:
            columns = range(self.column_count())
        elif isinstance(columns, int):
            columns = [columns]
        for row in rows:
            for column in columns:
                self._data[row][column]['render'] = render_func

    set_format = set_render

    def get_cell_data(self, row, column, role='data', header=False):
        """get cell data"""
        cell = self.get_cell(row, column, header)
        return cell.get(role)

    def render_data(self, row, column, header=False):
        """render data
        """
        h_cell = self.get_cell(row, column, header=True)
        if header:
            text = h_cell.get('title') or ''
        else:
            cell = self.get_cell(row, column, header=False)
            value = cell['data']
            if value is None:
                text = self._null_char
            else:
                render_func = cell.get('render') or h_cell.get('render')
                text = render_func(value)
        return text

    def render_cell(self, row, column, header=False):
        """render cell
        """
        h_cell = self.get_cell(row, column, header=True)
        if header:
            cell = h_cell
        else:
            cell = self.get_cell(row, column, header=False)
        align = cell.get('align') or h_cell.get('align')
        align = AlignSymbol.get(align)

        text = self.render_data(row, column, header)

        width = self._columns_width[column] - cell['MB']
        if width > 0:
            cell_text = '{:{align}{width}}'.format(text, align=align, width=width)
            return cell_text
        else:
            return text

    @staticmethod
    def from_list(data, header=None):
        mt = MarkupTable()
        mt.set_data(data, header=header)
        return mt

    @staticmethod
    def from_dict(data, header=None):
        mt = MarkupTable()
        mt.set_dict_data(data, header)
        return mt

    @staticmethod
    def from_dataframe(df):
        mt = MarkupTable()
        mt.set_dataframe_data(df)
        return mt

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
                elif tr.find(['th', 'td']):
                    for td in tr.find_all(['th', 'td']):
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

    def to_rst(self, style=None, footer=False):
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
                tr.append(self.render_cell(0, col, header=True))
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
                tr.append(self.render_cell(row, column))
                tr.append(self._right_padding)
                tr.append(v_separator)
            t.append(''.join(tr))
            if not style:
                t.append(''.join(tr_s))
        if footer:
            t.append(t[1])
            if not style:
                t.append(''.join(tr_s))
        if style:
            t.append(''.join(th_s))
        return '\n'.join(t) + '\n'

    def to_md(self, footer=False):
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
                tr.append(self.render_cell(0, col, header=True))
                tr.append(self._right_padding)
                tr.append(v_separator)
            t.append(''.join(tr))
            t.append(''.join(th_s))
        # data
        for row in range(self.row_count()):
            tr = [v_separator]
            for column in range(self.column_count()):
                tr.append(self._left_padding)
                tr.append(self.render_cell(row, column))
                tr.append(self._right_padding)
                tr.append(v_separator)
            t.append(''.join(tr))
        if footer:
            t.append(t[0])
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
                html.append('<th>%s</th>' % self.render_data(0, column, header=True))
            html.append('</tr>')
        # data
        for row in range(self.row_count()):
            html.append('<tr>')
            for column in range(self.column_count()):
                html.append('<td>%s</td>' % self.render_data(row, column))
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
                row_data.append(self.render_data(0, column, header=True))
            data.append('\t'.join(row_data))
        for row in range(self.row_count()):
            row_data = []
            for column in range(self.column_count()):
                row_data.append(self.render_data(row, column))
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
                    row_data.append(self.render_data(0, column, header=True))
                writer.writerow(row_data)
            for row in range(self.row_count()):
                row_data = []
                for column in range(self.column_count()):
                    row_data.append(self.render_data(row, column))
                writer.writerow(row_data)

    def to_json(self, filename):
        dict_data = {}
        header = []
        if self._header:
            for x in range(self.column_count()):
                header.append(self.get_cell_data(0, x, header=True))
        dict_data['header'] = header
        data = []
        if header:
            for y in range(self.row_count()):
                row = {}
                for x in range(self.column_count()):
                    row[header[x]] = self.get_cell_data(y, x)
                data.append(row)
        else:
            for y in range(self.row_count()):
                row = []
                for x in range(self.column_count()):
                    row.append(self.get_cell_data(y, x))
                data.append(row)

        dict_data['data'] = data
        with open(filename, 'w') as f:
            json.dump(dict_data, f)

    def to_dataframe(self):
        import pandas as pd
        header = [h['data'] for h in self._header]
        data = []
        for dd in self._data:
            data.append([d['data'] for d in dd])
        return pd.DataFrame.from_records(data, columns=header)
