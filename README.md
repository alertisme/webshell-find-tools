Webshell find tools
===

[![License](https://img.shields.io/github/license/wofeiwo/webshell-find-tools.svg)](https://github.com/wofeiwo/webshell-find-tools/LICENSE)

## 介绍

这里面包含两个小脚本，主要是用来在Web服务器上查找Webshell而写的小程序。

创建于2010年，当时的我还很年轻。所以，别太苛求脚本的质量。It works, right?

## 安装

* 要求：python >= 2.5
* 直接运行脚本查看 help

## ala.py (Access Log Analyzer)

这个脚本的思路是：
> 分析Accesslog文件，然后按照访问次数、存在性排序所有请求的路径。去除所有静态文件。如果是个访问量较大的网站，通常访问最少的几个文件就是Webshell。

### Useage

```

  -l, --logfile=filepath                Apache access logfile
  -o, --output=filepath                 Result tmpfile path
  -w, --webroot=webpath                 Real web root path
  -n, --number=number                   Display result numbers(default:all result)
  -f, --format=logformat                Apache access log format(default:combined. avlible: common, combined or a valid log format string)
  -v, --verbosity                       Display verbosity information  
  -m, --minrequest                      Display result sort by min request numbers
  -M, --maxrequest                      Display result sort by max request numbers
  -e, --exists                          Display result sort by exists
  -E, --lost                            Display result sort by lost
  -s, --showstatic                      Display static files as well(js, images, css, zip, gz)
  -h, --help                            Display this help and exit

```

通常情况下使用这一种模式就可以分析了：


```
python ala.py -l access_log -w /var/www -n 100 -f combined
```

注意这个`combined`是accesslog的格式，常用的还有`common`格式。详细请参考Apache的配置文件。此工具必须按照固定格式去分析日志。如果日志中有不能解析的内容，将会跳过此记录不纳入统计。

你也可以自己定义日志格式。请直接使用`-f`指定格式串。

`-w`参数代表着另一个工具的功能，这个参数指定了真正的webroot目录。如果分析的日志中有访问的文件但是真实目录下又不存在，那么结果中也就可以按照存在与否进行排序。通过这个也可以简单的去推测是否是webshell。当然你也可以不使用这个参数。

## fca.py (File Changes Analyzer)

fca改名了，因为这一次是大升级，因此不单单只是ctime分组的功能，改名为`File Changes Analyzer`。

这个脚本的思路是：
> 1. 将文件系统中的文件按照改动时间区段分组。一般情况下，web目录下的文件创建时间是集中的。如果某些文件创建时间比较不合群，那么这个文件是webshell的可能性就很大。
> 2. 根据给定的文件属主，将Web目录下不同属主的文件显示出来。这些文件很可能就是webserver生成的异常文件。
> 3. 通过MySQL导出的webshell很常见，而MySQL导出的文件又有一定的特殊性，所有导出文件的权限都是666。通过这个过滤出所有MySQL导出的web脚本。很可能就是webshell。

### Useage

```
  -a, --action=actionname               What to do(ctimegroup, ownerdiff, mysqlfile, default = all)
  -u, --user=owner                      Onwer name of the webpath files(default = current user)
  -m, --mysqluser=mysqluser             User name of the mysql(default = mysql)
  -e, --ext=php,asp,jsp                 Filter the ext, only show these files(default = 'php', 'jsp', 'asp', 'pl', 'py', 'aspx', 'cer', 'asa')
  -w, --webroot=webpath                 Real web root path
  -n, --number=filenumber               Files less than this number, display the them(default:5) (for ctimegroup)
  -t, --timedelta=time                  Time group (minutes, default = 5)
  -h, --help                            Display this help and exit
  
  example: %s -a ctimegroup -w /var/www -n 5 -t 10
  example: %s -a mysqlfile -w /var/www -m database
  example: %s -w /var/www # show all abnormal files
```

他的必要参数只有一个，那就是`webroot`路径。

* `ctimegroup`参数: 
  1. `-t`: 分组的时间最小区段(分钟)
  2. `-n`: 不合群的文件小于此值，就会输出出来方便排查。

* `ownerdiff`参数:
  1. `-u`: web文件默认的属主，所有web文件应该都是这个属主，否则就为异常

* `mysqluser`参数:
  1. `-m`: mysql默认的运行用户。所有mysql导出文件应该都是这个属主，可以通过这个过滤出Mysql导出的文件。

Copyright (c) 2013-2017 wofeiwo, released under the Apache license