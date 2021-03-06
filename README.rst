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
+ list data
+ dict data
+ html
+ csv
+ rst
+ md

Example
=======

rst table
---------

+------+-----------------+------------------+--------+
| 名字 |      网站       |       备注       |  其它  |
+======+=================+==================+========+
| 百度 |  www.baidu.com  | 搜索，网盘，地图 |   --   |
+------+-----------------+------------------+--------+
| 新浪 | www.sina.com.cn |       新闻       |   --   |
+------+-----------------+------------------+--------+
| 腾讯 |   www.qq.com    |       聊天       |  微信  |
+------+-----------------+------------------+--------+
| 网易 |   www.163.com   |       邮箱       | １２３ |
+------+-----------------+------------------+--------+

====== ================= ================== ========
 名字        网站               备注          其它
====== ================= ================== ========
 百度    www.baidu.com    搜索，网盘，地图     --
 新浪   www.sina.com.cn         新闻           --
 腾讯     www.qq.com            聊天          微信
 网易     www.163.com           邮箱         １２３
====== ================= ================== ========


rst table with no header
------------------------

+------+-----------------+------------------+--------+
|      |                 |                  |        |
+======+=================+==================+========+
| 百度 |  www.baidu.com  | 搜索，网盘，地图 |   --   |
+------+-----------------+------------------+--------+
| 新浪 | www.sina.com.cn |       新闻       |   --   |
+------+-----------------+------------------+--------+
| 腾讯 |   www.qq.com    |       聊天       |  微信  |
+------+-----------------+------------------+--------+
| 网易 |   www.163.com   |       邮箱       | １２３ |
+------+-----------------+------------------+--------+

====== ================= ================== ========

====== ================= ================== ========
 百度    www.baidu.com    搜索，网盘，地图     --
 新浪   www.sina.com.cn         新闻           --
 腾讯     www.qq.com            聊天          微信
 网易     www.163.com           邮箱         １２３
====== ================= ================== ========

md table
--------

| 名字 |      网站       |       备注       |  其它  |
| ---- | --------------- | ---------------- | ------ |
| 百度 |  www.baidu.com  | 搜索，网盘，地图 |   --   |
| 新浪 | www.sina.com.cn |       新闻       |   --   |
| 腾讯 |   www.qq.com    |       聊天       |  微信  |
| 网易 |   www.163.com   |       邮箱       | １２３ |

