============
Markup Table
============

format data to Table

Output table
------------
+ reStructuredText
+ Markdown
+ html
+ csv
+ pandas.dataframe

Read table from
---------------
+ html
+ csv
+ rst
+ md

Example
=======

::

    data = [
        [h, h, h...], # header = 1
        [d, d, d...],
        [d, d, d...],
        ...
    ]

    table = MarkupTable(data, header=1)
    print(table.to_rst())
    print(table.to_md())
    print(table.to_csv('csv_file'))

    table.append_row(['a', 'b', 'c', 'd', 'e'])
    table.set_align('center', rows=[0])
    table.set_align('left',rows=range(1, table.row_count(), columns=[3])
    table.set_align('right',rows=range(1, table.row_count(), columns=[4])

    table.set_format(lambda x: '{:,.2f} %'.format(x), rows=range(1, table.row_count()), columns=[4])

    table = MarkupTable.from_html(open('html_file').read())
    print(table.to_rst())

    table = MarkupTable.from_csv(open('csv_file').read())
    print(table.to_rst())
