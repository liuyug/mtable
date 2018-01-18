#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import sys
import csv


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
    _left_padding = ' '
    _right_padding = ' '
    _null_char = '--'

    def __init__(self):
        self._columns_width = []

    def __repr__(self):
        return '<Markup Table: %s rows, %s cols>' % (
            self.row_count(), self.column_count()
        )

    def set_data(self, data, header=None, encoding=None):
        if header:
            self._header = []
            for h in header:
                self._header.append({
                    'data': self.decode(h, encoding),
                    'format': lambda x: '%s' % x,
                    'align': 'center',
                    'MB': 0,
                })
        self._data = []
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

    def row_count(self):
        return len(self._data)

    def column_count(self):
        return len(self._data[0])

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
                    self.get_item_text_length(0, column, header=True) + mb
                item['MB'] = mb
            # data
            for row in range(self.row_count()):
                item = self.get_item(row, column)
                mb = self.cjk_count(self.get_item_text(row, column))
                w = self.get_item_text_length(row, column) + mb
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

    def get_item_text_length(self, row, column, header=False):
        text = self.get_item_text(row, column, header)
        return len(text)

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

    def to_csv(self, filename):
        with open(filename, 'wt', newline='') as f:
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
