#!/usr/bin/env python
# -*- encoding:utf-8 -*-

AlignSymbol = {
    'left': '<',
    'center': '^',
    'right': '>',
}

CjkRange = (
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

    def setData(self, data, header=None, encoding=None):
        if header:
            self._header = []
            for h in header:
                self._header.append({
                    'data': h.decode(encoding) if encoding else h,
                    'format': lambda x: '%s' % x,
                    'align': 'center',
                    'MB': 0,
                })
        self._data = []
        for dd in data:
            row = []
            for d in dd:
                row.append({
                    'data': d.decode(encoding) if encoding else d,
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

    def _calc_widths(self, columns=None):
        if columns is None:
            columns = range(self.column_count())
        elif isinstance(columns, int):
            columns = [columns]
        for column in columns:
            # header
            if self._header:
                item = self._header[column]
                mb = self.cjk_count(self.get_item_text(item))
                self._columns_width[column] = self.get_item_text_length(item) + mb
            # data
            for row in range(self.row_count()):
                item = self._data[row][column]
                mb = self.cjk_count(self.get_item_text(item))
                w = self.get_item_text_length(item) + mb
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

    def get_item_text(self, item):
        value = item['data']
        if value is None:
            text = self._null_char
        else:
            text = item['format'](value)
        return text

    def get_item_text_length(self, item):
        text = self.get_item_text(item)
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

    def get_data(self, row, column, role='data'):
        item = self._data[row][column]
        return item.get(role)

    def csv(self, filename):
        with open(filename, 'wt') as f:
            for row in self._data:
                line = ','.join([r['data'] for r in row]) + '\n'
                f.write(line)

    def get_view_data_item(self, row, column, header=False):
        """call before function _calc_widths
        """
        if header:
            item = self._header[column]
        else:
            item = self._data[row][column]
        width = self._columns_width[column] - item['MB']
        align = AlignSymbol.get(item['align'])
        text = self.get_item_text(item)
        view = '{:{align}{width}}'.format(text, align=align, width=width)
        return view

    def rst_table(self, style=None):
        """style:
        nosep: no separater
        """
        t = []
        widths = self._calc_widths()
        if style == 'nosep':
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
            if style == 'nosep':
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
            if style == 'nosep':
                t.append(''.join(th_s))
            else:
                t.append(''.join(tr_s))
        # data
        for row in range(self.row_count()):
            if style == 'nosep':
                tr = []
            else:
                tr = [v_separator]
            for column in range(self.column_count()):
                tr.append(self._left_padding)
                tr.append(self.get_view_data_item(row, column))
                tr.append(self._right_padding)
                tr.append(v_separator)
            t.append(''.join(tr))
            if style != 'nosep':
                t.append(''.join(tr_s))
        if style == 'nosep':
            t.append(''.join(th_s))
        return '\n'.join(t) + '\n'
