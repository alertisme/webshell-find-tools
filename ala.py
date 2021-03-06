#!/usr/bin/python
# -*- coding: utf-8 -*-
# Name    : Access Log Analyzer
# Author  : wofeiwo#80sec.com
# Version : 1.0
# Date    : 2010-1-29

#分析访问日志并按照访问次数、存在性排序。去除所有静态文件

import sys,os,string,re,datetime,getopt,time
try:
    import hashlib as md5hash
except:
    import md5 as md5hash

#####################################################
__version__ = "1.1"
__license__ = """Released under the same terms as Perl.
See: http://dev.perl.org/licenses/
"""
__author__ = "Harry Fuecks <hfuecks@gmail.com>"
__contributors__ = [
    "Peter Hickman <peterhi@ntlworld.com>",
    "Loic Dachary <loic@dachary.org>"
    ]

class ApacheLogParserError(Exception):
    pass

class parser:
    
    def __init__(self, format):
        """
        Takes the log format from an Apache configuration file.

        Best just copy and paste directly from the .conf file
        and pass using a Python raw string e.g.
        
        format = r'%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"'
        p = apachelog.parser(format)
        """
        self._names = []
        self._regex = None
        self._pattern = ''
        self._parse_format(format)
    
    def _parse_format(self, format):
        """
        Converts the input format to a regular
        expression, as well as extracting fields

        Raises an exception if it couldn't compile
        the generated regex.
        """
        format = format.strip()
        format = re.sub('[ \t]+',' ',format)
        
        subpatterns = []

        findquotes = re.compile(r'^\\"')
        findreferreragent = re.compile('Referer|User-Agent')
        findpercent = re.compile('^%.*t$')
        lstripquotes = re.compile(r'^\\"')
        rstripquotes = re.compile(r'\\"$')
        self._names = []
        
        for element in format.split(' '):

            hasquotes = 0
            if findquotes.search(element): hasquotes = 1

            if hasquotes:
                element = lstripquotes.sub('', element)
                element = rstripquotes.sub('', element)
            
            self._names.append(self.alias(element))
            
            subpattern = '(\S*)'
            
            if hasquotes:
                if element == '%r' or findreferreragent.search(element):
                    subpattern = r'\"([^"\\]*(?:\\.[^"\\]*)*)\"'
                else:
                    subpattern = r'\"([^\"]*)\"'
                
            elif findpercent.search(element):
                subpattern = r'(\[[^\]]+\])'
                
            elif element == '%U':
                subpattern = '(.+?)'
            
            subpatterns.append(subpattern)
        
        self._pattern = '^' + ' '.join(subpatterns) + '$'
        try:
            self._regex = re.compile(self._pattern)
        except Exception, e:
            raise ApacheLogParserError(e)
        
    def parse(self, line):
        """
        Parses a single line from the log file and returns
        a dictionary of it's contents.

        Raises and exception if it couldn't parse the line
        """
        line = line.strip()
        match = self._regex.match(line)
        
        if match:
            data = {}
            for k, v in zip(self._names, match.groups()):
                data[k] = v
            return data
        
        raise ApacheLogParserError("Unable to parse: %s with the %s regular expression" % ( line, self._pattern ) )

    def alias(self, name):
        """
        Override / replace this method if you want to map format
        field names to something else. This method is called
        when the parser is constructed, not when actually parsing
        a log file
        
        Takes and returns a string fieldname
        """
        return name

    def pattern(self):
        """
        Returns the compound regular expression the parser extracted
        from the input format (a string)
        """
        return self._pattern

    def names(self):
        """
        Returns the field names the parser extracted from the
        input format (a list)
        """
        return self._names

months = {
    'Jan':'01',
    'Feb':'02',
    'Mar':'03',
    'Apr':'04',
    'May':'05',
    'Jun':'06',
    'Jul':'07',
    'Aug':'08',
    'Sep':'09',
    'Oct':'10',
    'Nov':'11',
    'Dec':'12'
    }

def parse_date(date):
    """
    Takes a date in the format: [05/Dec/2006:10:51:44 +0000]
    (including square brackets) and returns a two element
    tuple containing first a timestamp of the form
    YYYYMMDDHH24IISS e.g. 20061205105144 and second the
    timezone offset as is e.g.;

    parse_date('[05/Dec/2006:10:51:44 +0000]')  
    >> ('20061205105144', '+0000')

    It does not attempt to adjust the timestamp according
    to the timezone - this is your problem.
    """
    date = date[1:-1]
    elems = [
        date[7:11],
        months[date[3:6]],
        date[0:2],
        date[12:14],
        date[15:17],
        date[18:20],
        ]
    return (''.join(elems),date[21:])


"""
Frequenty used log formats stored here
"""
formats = {
    # Common Log Format (CLF)
    'common':r'%h %l %u %t \"%r\" %>s %b',

    # Common Log Format with Virtual Host
    'vhcommon':r'%v %h %l %u %t \"%r\" %>s %b',

    # NCSA extended/combined log format
    'extended':r'%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\"',
    }

#####################################################


def filterStatic(uri):
    result = re.findall('^([^?]*)\??.*$', uri)
    if (len(result)>0) and (result[0].rfind('.') != -1) and (result[0][result[0].rfind('.')+1:] in ['css', 'js', 'jpg', 'gif', 'jpeg', 'png', 'ico', 'htm', 'html', 'gz', 'swf', 'rar', 'zip', 'csv', 'xls', 'doc', 'tif', 'wav', 'swf', 'asf', 'mp3', 'wma', 'fla', 'flv']):
    #if (len(result)>0) and (result[0].rfind('.') != -1) and (result[0][result[0].rfind('.')+1:] not in ['php', 'inc', 'phtml', 'jsp', 'jspx', 'php3', 'php4', 'phps', 'pl', 'cgi', 'py', 'sh']):
        return ''
    else:
        return result[0]

def sortByRequest(uris):
    # 排序字典
    sortUriList = uris.items()
    sortUriList.sort(lambda (k1,v1),(k2,v2): cmp(v1['count'],v2['count']))
    return sortUriList
    
def sortByExists(uris):
    # 排序字典
    sortUriList = uris.items()
    sortUriList.sort(lambda (k1,v1),(k2,v2): cmp(v2['exists'],v1['exists']))
    return sortUriList
    
def printResult(sortUriList, options):
    print 'Min Request Uri Result:'
    print '--------------------------------------------------------------------------------'
    if options['webroot']: print '%-60s\tExists\tRTimes\tMethodCount\n' % 'RequestUri'
    else: print '%-60s\tRTimes\tMethodCount\n' % 'RequestUri'
    # 显示num行结果
    if options['number'] == 'all' or options['number'] > len(sortUriList): # 是否显示所有结果
        options['number'] = len(sortUriList)
    
    for i in xrange(options['number']):
        methodCount = ''
        for k in sortUriList[i][1].keys():
            if k == 'count' or k == 'exists' : continue
            methodCount += '%s(%d)/' % (k, sortUriList[i][1][k])
        if options['webroot']: print '%-60s\t%-6s\t%-6s\t%s'% ( sortUriList[i][0], str(sortUriList[i][1]['exists']), str(sortUriList[i][1]['count']), methodCount)
        else: print '%-60s\t%-6s\t%s'% ( sortUriList[i][0], str(sortUriList[i][1]['count']), methodCount)
        
    print '--------------------------------------------------------------------------------'

# 分析日志
def parseLog(logFile, output, format = r"%h %l %u %t \"%r\" %>s %b", showstatic = False, webroot = False):
    months = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sep':9, 'Oct':10, 'Nov':11, 'Dec':12}
    uris = {}
    lines = []
    log = {}
    tmp = ''

    import cPickle as pickle
    
    # 读取分析结果
    if os.path.exists(output):
        return pickle.load(open(output, 'r'))
    
    # 如果没有分析过，则开始分析
    #openFile = open(logFile, 'r')
    openFile = logFile
    l = openFile.readline()

    while l:    
        try:
            apalogparser = parser(format)
            data = apalogparser.parse(l)
            
            if data['%>s'] in ['404', '400', '408', '501', '500']:
                l = openFile.readline()
                continue
            
            # 分析一行日志
            logLine = {
                       'status':int(data['%>s']), 
                       'ip':data['%h'], 
                       'time': datetime.datetime(int(data['%t'][8:12]), months[data['%t'][4:7]], int(data['%t'][1:3]), int(data['%t'][13:15]), int(data['%t'][16:18]), int(data['%t'][19:21])), 
                       'method':data['%r'].split(' ')[0],
                       'uri':data['%r'].split(' ')[1],
                       #'protocol':data['%r'].split(' ')[2],
                      }

            if format.find('%{Referer}i') != -1 : logLine['referer'] = data['%{Referer}i']
            if format.find('%{User-Agent}i') != -1 : logLine['user-agent'] = data['%{User-Agent}i']
                      
            # 去除静态文件
            if not showstatic:
                tmp = filterStatic(logLine['uri'])
            
            if tmp != '':
                # 做uri次数统计
                if uris.has_key(tmp):
                    uris[tmp]['count'] += 1
                else:
                    uris[tmp] = {'count' : 1}
                
                # 记录不同的METHOD
                if logLine['method'].upper() == 'GET':
                    if uris[tmp].has_key('GET') : uris[tmp]['GET'] += 1
                    else : uris[tmp]['GET'] = 1
                elif logLine['method'].upper() == 'POST':
                    if uris[tmp].has_key('POST') : uris[tmp]['POST'] += 1
                    else : uris[tmp]['POST'] = 1
                elif logLine['method'].upper() == 'HEAD':
                    if uris[tmp].has_key('HEAD') : uris[tmp]['HEAD'] += 1
                    else : uris[tmp]['HEAD'] = 1
                elif logLine['method'].upper() == 'PUT':
                    if uris[tmp].has_key('PUT') : uris[tmp]['PUT'] += 1
                    else : uris[tmp]['PUT'] = 1
                elif logLine['method'].upper() == 'DELETE':
                    if uris[tmp].has_key('DELETE') : uris[tmp]['DELETE'] += 1
                    else : uris[tmp]['DELETE'] = 1
                else:
                    if uris[tmp].has_key('OTHER') : uris[tmp]['OTHER'] += 1
                    else : uris[tmp]['OTHER'] = 1

                # lines.append(logLine)
            
            l = openFile.readline()
            
        except Exception, e:
            sys.stderr.write('[-] Unable to parse : %s : %s\n' % (l, str(e)))
            l = openFile.readline()
            #sys.exit()
            
    # log['lines'] = lines
    log['uris'] = uris
    
    
    if webroot:
        for item in log['uris'].keys():
            log['uris'][item]['exists'] = compareWebRoot(item, webroot)
    
    log['path'] = os.path.realpath(logFile.name)
    
    # 保存分析结果，方便下次调用
    if not os.path.exists('./output'):
        os.mkdir('output')
    
    pickle.dump(log, open(output, 'w'))
    
    return log
    
def usage(program = sys.argv[0]):
    print "Usage %s [options]\n" % program
    print \
"""
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
  
  example: %s -l access_log -w /var/www -n 100 -f combined""" % program

# 处理参数    
def parseArgs(args):
    options = {}
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvl:n:f:so:w:mMeE", \
        ["help", "verbosity", "logfile=", "number=", "format=", "showstatic", "output=", "webroot=", "minrequest", "maxrequest", "exists", "lost"])
    except getopt.GetoptError, e:
        sys.stderr.write('[-] %s\n' % str(e))
        usage(sys.argv[0])
        sys.exit(2)
        
    for o, v in opts:
        # print(o, v)
        if o in ["-l", "--logfile"]:
            options['logFile'] = open(os.path.realpath(str(v)))
            
        elif o in ["-o", "--output"]:
            options['output'] = str(v)

        elif o in ["-n", "--number"]:
            options['number'] = int(v)
            
        elif o in ["-f", "--format"]:
            options['format'] = str(v)
    
        elif o in ["-s", "--showstatic"]:
            options['showstatic'] = True
    
        elif o in ["-v", "--verbosity"]:
            options['verbosity'] = True
        
        elif o in ["-m", "--minrequest"]:
            options['minrequest'] = True
        
        elif o in ["-M", "--maxrequest"]:
            options['maxrequest'] = True
        
        elif o in ["-e", "--exists"]:
            options['exists'] = True
        
        elif o in ["-E", "--lost"]:
            options['lost'] = True
            
        elif o in ["-w", "--webroot"]:
            options['webroot'] = os.path.realpath(str(v))

        elif o in ["-h", "--help"]:
            usage(sys.argv[0])
            sys.exit()
            
    if options.has_key('verbosity'):
        options['start'] = time.time() # for test
            
    # 设置一些默认值
    
    if not options.has_key('logFile'):
        #usage(sys.argv[0])
        #sys.exit(2)
        
        # 加入stdin的支持   20100407
        options['logFile'] = sys.stdin
    
    if not options.has_key('output'):
        options['output'] = './output'+md5hash.md5(os.path.basename(os.path.realpath(options['logFile'].name))).hexdigest()
    
    if not options.has_key('format'):
        options['format'] = r"%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" 
    elif options['format'] == 'common':
        options['format'] = r"%h %l %u %t \"%r\" %>s %b"
    elif options['format'] == 'combined':
        options['format'] = r"%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\""
        
    if not options.has_key('number'):
        options['number'] = 'all'
    
    if not options.has_key('showstatic'):
        options['showstatic'] = False
        
    if not options.has_key('webroot'):
        options['webroot'] = False
     
    return options

# 比对日志和物理路径
def compareWebRoot(uri, webroot):
    filePath = os.path.realpath(webroot + uri)
    if os.path.exists(filePath) : return True
    else : return False
    
# 入口，基本就是左调一个函数右调一个函数
def main():    
    
    options = parseArgs(sys.argv)

    sortUriList = []
    
    # 日志解析
    log = parseLog(options['logFile'], options['output'], options['format'], options['showstatic'], options['webroot'])
    
    # 数据排序
    if options.has_key('minrequest'):
        sortUriList = sortByRequest(log['uris'])
    elif options.has_key('maxrequest'):
        sortUriList = sortByRequest(log['uris'])
        sortUriList.reverse()
    elif options.has_key('exists'):
        sortUriList = sortByExists(log['uris'])
    elif options.has_key('lost'):
        sortUriList = sortByExists(log['uris'])
        sortUriList.reverse()
    else : sortUriList = sortByRequest(log['uris'])
    
    printResult(sortUriList, options)
    
if __name__ == '__main__': main()# end if