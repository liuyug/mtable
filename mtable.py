#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import re
import csv
import json

from bs4 import BeautifulSoup
from wcwidth import wcswidth


VERSION = '0.2.22'


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

    def __init__(self, data=None, header=0, footer=0):
        """
        input data = [
            [h, h, h...], # header = 1
            [d, d, d...],
            [d, d, d...],
            ...
        ]
        """
        self._header = header
        self._footer = footer
        self._data = []

        if data:
            for rows in data:
                row_data = []
                for cell in rows:
                    row_data.append({
                        'data': cell,
                        'render': lambda x: '%s' % x,
                        'align': 'left',
                        'MB': 0,  # cell width
                    })
                self._data.append(row_data)

    def __repr__(self):
        return '<Markup Table: %s rows, %s cols>' % (
            self.row_count(), self.column_count()
        )

    def append_row(self, row):
        row_data = []
        for value in row:
            row_data.append({
                'data': value,
                'render': lambda x: '%s' % x,
                'align': 'left',
                'MB': 0,  # cell width
            })
        self._data.append(row_data)

    def append_rows(self, rows):
        for row in rows:
            self.append_rows(row)

    def clearall(self):
        self._header = 0
        self._footer = 0
        self._data = []

    def row_count(self):
        return 0 if self.is_empty() else len(self._data)

    def column_count(self):
        return 0 if self.is_empty() else len(self._data[0])

    def is_empty(self):
        return len(self._data) == 0

    def is_invalid(self):
        return False

    def _calc_widths(self):
        self._columns_width = [0] * self.column_count()
        for column in range(self.column_count()):
            # data
            for row in range(self.row_count()):
                cell = self.get_cell(row, column)
                text = self.render_data(row, column)
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

    def get_cell(self, row, column):
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

    def set_format(self, render_func, rows=None, columns=None):
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

    def render_data(self, row, column):
        """render data
        """
        cell = self.get_cell(row, column)
        value = cell['data']
        if value is None:
            text = self._null_char
        else:
            render_func = cell.get('render')
            text = render_func(value)
        return text

    def render_cell(self, row, column):
        """render cell
        """
        cell = self.get_cell(row, column)
        align = cell.get('align')
        align = AlignSymbol.get(align)

        text = self.render_data(row, column)

        width = self._columns_width[column] - cell['MB']
        if width > 0:
            cell_text = '{:{align}{width}}'.format(text, align=align, width=width)
            return cell_text
        else:
            return text

    # def from_dataframe(self, df, encoding='utf-8'):
    #     for h in df.columns:
    #         self._data.append({
    #             'data': h,
    #             'render': lambda x: '%s' % x,
    #             'align': 'left',
    #             'MB': 0,
    #         })
    #     self._header = 1
    #     self._footer = 0

    #     for idx in df.index:
    #         row = []
    #         for h in df.columns:
    #             row.append({
    #                 'data': df.loc[idx, h],
    #                 'MB': 0,
    #             })
    #         self._data.append(row)
    #     self._columns_width = [0] * self.column_count()

    # @staticmethod
    # def from_dataframe(df):
    #     mt = MarkupTable()
    #     mt.set_dataframe_data(df)
    #     return mt

    @staticmethod
    def from_rst(rst_text):
        def parse_table1(text):
            header = 0
            data = []
            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.startswith('+-'):
                    continue
                if line.startswith('+='):
                    header = 1
                    continue
                line = line.strip('|')
                data.append([item.strip() for item in line.split('|')])

            mt = MarkupTable(data, header=header)
            return mt

        def parse_table2(text):
            header = 0
            data = []
            for line in text.split('\n'):
                line = line.strip()
                while '  ' in line:
                    line = line.replace('  ', ' ')
                if not line:
                    continue
                if line.startswith('=='):
                    if data:
                        header = 1
                    continue
                data.append(line.split(' '))

            mt = MarkupTable(data, header=header)
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
            header = 0
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
                header = 1
                data.pop(1)

            mt = MarkupTable(data, header=header)
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
    def from_csv(fobj, header=True):
        mt = MarkupTable()
        reader = csv.reader(fobj)
        if header:
            mt.append_row(reader.__next__())
        for row in reader:
            mt.append_row(row)
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
                if tr.find(['th', 'td']):
                    for td in tr.find_all(['th', 'td']):
                        text = strip_text(' '.join(td.stripped_strings))
                        row.append(text)
                        if td.get('colspan'):
                            row.extend([' '] * (int(td.get('colspan')) - 1))
                    if column_count == 0:
                        column_count = len(row)
                    diff = column_count - len(row)
                    row.extend([None] * diff)
                mt.append_row(row)
            tables.append(mt)
        return tables

    def to_txt(self, simple=True):
        h_sep = '-'
        d_sep = '-'
        v_sep = '|'
        c_sep = '+'

        if self.is_empty() or self.is_invalid():
            return ''
        t = []
        widths = self._calc_widths()

        h_separator = h_sep
        d_separator = d_sep
        v_separator = v_sep
        c_separator = c_sep
        th_s = [c_separator]
        tr_s = [c_separator]

        for w in widths:
            # data
            tr_s.append(d_separator * (
                len(self._left_padding) + w + len(self._right_padding)))
            tr_s.append(c_separator)

            # header
            th_s.append(h_separator * (
                len(self._left_padding) + w + len(self._right_padding)))
            th_s.append(c_separator)

        # header
        if self._header > 0:
            for h in range(self._header):
                if simple:
                    t.append(''.join(th_s))
                else:
                    t.append(''.join(tr_s))

                tr = [v_separator]
                for col in range(self.column_count()):
                    tr.append(self._left_padding)
                    tr.append(self.render_cell(h, col))
                    tr.append(self._right_padding)
                    tr.append(v_separator)
                t.append(''.join(tr))
            t.append(''.join(th_s))
        else:
            if simple:
                t.append(''.join(th_s))
            else:
                t.append(''.join(tr_s))
        # data
        for row in range(self._header, self.row_count()):
            tr = [v_separator]
            for column in range(self.column_count()):
                tr.append(self._left_padding)
                tr.append(self.render_cell(row, column))
                tr.append(self._right_padding)
                tr.append(v_separator)
            t.append(''.join(tr))
            if not simple:
                t.append(''.join(tr_s))
        if simple:
            t.append(''.join(th_s))
        return '\n'.join(t) + '\n'

    def to_rst(self, simple=True):
        """two styles: False or True
        """
        h_sep = '='
        d_sep = '-'
        v_sep = '|'
        c_sep = '+'
        if self.is_empty() or self.is_invalid():
            return ''
        t = []
        widths = self._calc_widths()

        h_separator = h_sep
        d_separator = d_sep
        if simple:
            v_separator = ' '
            c_separator = ' '
            th_s = []
            tr_s = []
        else:
            v_separator = v_sep
            c_separator = c_sep
            th_s = [c_separator]
            tr_s = [c_separator]

        for w in widths:
            # data
            tr_s.append(d_separator * (
                len(self._left_padding) + w + len(self._right_padding)))
            tr_s.append(c_separator)

            # header
            th_s.append(h_separator * (
                len(self._left_padding) + w + len(self._right_padding)))
            th_s.append(c_separator)
        # header
        if self._header > 0:
            for h in range(self._header):
                if simple:
                    t.append(''.join(th_s))
                    tr = []
                else:
                    t.append(''.join(tr_s))
                    tr = [v_separator]
                for col in range(self.column_count()):
                    tr.append(self._left_padding)
                    tr.append(self.render_cell(h, col))
                    tr.append(self._right_padding)
                    tr.append(v_separator)
                t.append(''.join(tr))
            t.append(''.join(th_s))
        else:
            if simple:
                t.append(''.join(th_s))
            else:
                t.append(''.join(tr_s))
        # data
        for row in range(self._header, self.row_count()):
            if simple:
                tr = []
            else:
                tr = [v_separator]
            for column in range(self.column_count()):
                tr.append(self._left_padding)
                tr.append(self.render_cell(row, column))
                tr.append(self._right_padding)
                tr.append(v_separator)
            t.append(''.join(tr))
            if not simple:
                t.append(''.join(tr_s))
        # if footer:
        #     t.append(t[1])
        #     if not simple:
        #         t.append(''.join(tr_s))
        if simple:
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
        for h in range(self._header):
            tr = [v_separator]
            for col in range(self.column_count()):
                tr.append(self._left_padding)
                tr.append(self.render_cell(h, col))
                tr.append(self._right_padding)
                tr.append(v_separator)
            t.append(''.join(tr))
        t.append(''.join(th_s))

        # data
        for row in range(self._header, self.row_count()):
            tr = [v_separator]
            for column in range(self.column_count()):
                tr.append(self._left_padding)
                tr.append(self.render_cell(row, column))
                tr.append(self._right_padding)
                tr.append(v_separator)
            t.append(''.join(tr))
        # TODO
        # if self._footer:
        #     t.append(t[0])
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
        if self._header > 0:
            for h in range(self._header):
                html.append('<tr>')
                for column in range(self.column_count()):
                    html.append('<th>%s</th>' % self.render_data(h, column))
                html.append('</tr>')
        # data
        for row in range(self._header, self.row_count()):
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

        for y in range(self.row_count()):
            row = []
            for x in range(self.column_count()):
                cell = self.get_cell(y, x)
                row.append(cell['data'])
            data.append('\t'.join(row))

        return '\n'.join(data)

    def to_csv(self, filename):
        if self.is_empty() or self.is_invalid():
            return ''
        with open(filename, 'wt', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(
                f, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

            for y in range(self.row_count()):
                row = []
                for x in range(self.column_count()):
                    # cell = self.get_cell(y, x)
                    # row.append(cell['data'])
                    row.append(self.render_data(y, x))
                writer.writerow(row)

    def to_json(self, filename):
        data = []
        for y in range(self.row_count()):
            row = []
            for x in range(self.column_count()):
                cell = self.get_cell(y, x)
                row.append(cell['data'])
            data.append(row)

        with open(filename, 'w') as f:
            json.dump(data, f)

    def to_dataframe(self):
        import pandas as pd
        data = []
        for y in range(self.row_count()):
            row = []
            for x in range(self.column_count()):
                cell = self.get_cell(y, x)
                row.append(cell['data'])
            data.append(row)

        if self.header > 0:
            return pd.DataFrame.from_records(data[1:], columns=data[0])
        else:
            return pd.DataFrame.from_records(data)
