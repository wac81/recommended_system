# coding=utf8


import os
import re
import jieba
import codecs
import jieba.posseg as pseg
# import sys
# sys.path.append("../../LSI-for-ChineseDocument")
# clear all html tags
# project_path = './'

# jieba.enable_parallel(3)
fileSavedPath='./news/'
rejectOfDocSize=400
x = 0
def stripTags(s):
    ''' Strips HTML tags.
        Taken from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/440481
    '''
    intag = [False]

    def chk(c):
        if intag[0]:
            intag[0] = (c != '>')
            return False
        elif c == '<':
            intag[0] = True
            return False
        return True

    return ''.join(c for c in s if chk(c))


def mkdir(path):
    # 引入模块
    import os

    # 去除首位空格
    path = str(path).strip()
    # 去除尾部 \ 符号
    path = path.rstrip("\\")

    # 判断路径是否存在
    # 存在     True
    # 不存在   False
    isExists = os.path.exists(path)

    # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        print path + ' 创建成功'
        # 创建目录操作函数
        os.makedirs(path)
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        print path + ' 目录已存在'
        return False


# 去除标题中的非法字符 (Windows)
def validateTitle(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/\:*?"<>|'
    new_title = re.sub(rstr, "", title)
    return new_title


# 去停用词
# stopwords = {}.fromkeys([line.rstrip()
                         # for line in open(project_path + 'stopwords.txt')])
stopwords = codecs.open('stopwords.txt', encoding='UTF-8').read()
# print stopwords

def delNOTNeedWords(content,stopwords):
    # words = jieba.lcut(content)
    result=''
    # for w in words:
    #     if w not in stopwords:
    #         result += w.encode('utf-8')  # +"/"+str(w.flag)+" "  #去停用词

    words = pseg.lcut(content)

    for word, flag in words:
        # print word.encode('utf-8')
        if (word not in stopwords and flag not in ["/x","/zg","/uj","/ul","/e","/d","/uz","/y"]): #去停用词和其他词性，比如非名词动词等
            result += word.encode('utf-8')  # +"/"+str(w.flag)+" "  #去停用词
    return result




# def writefile(line):
#     c = str(line)

#     if c.find('INSERT INTO `tmp_article` VALUES (', 0) < 0:
#         return
#     # c = unicode(c, errors='ignore')
#     c = c.split('(', 1)[1]
#     c = c[:-1]

#     cs = c.split('),(')
#     print len(cs)
#     for cc in cs:
#         # print cc
#         if len(cc) > 0:
#             # name = raw_input()
#             name = cc.split(',', 1)[0]
#             name = name[1:-1]
#             # print name
#             if len(cc.split(',')) > 1:
#                 content = cc.split(',', 1)[1]
#                 content = content[1:-1]
#                 # print content

#                 name = os.path.normpath(name)
#                 content = content.replace(r'\n', '').replace(
#                     r'▉', '').replace(r'\t', '').replace(' ', '')
#                 content = stripTags(content)
#                 content = delstopwords(content)
#                 if len(content) > 400:
#                     try:
#                         fnew = open(
#                             mkpath + '/' + validateTitle(name.decode('utf-8', 'ignore')) + '.txt', 'w')
#                     except:
#                         continue

#                     fnew.write(stripTags(content))
#                     fnew.close()


# from multiprocessing.dummy import Pool as ThreadPool
# pool = ThreadPool(400)
# dictionary = pool.map(writefile,fp)
# pool.close()
# pool.join()
def filebyfileHandleSingleProcess(SavedPath='./news/',rejectOfDocSize=400):
    # mkdir(fileSavedPath)
    # fp = open(fileSavedPath, 'r')
    x = 0
    global fileSavedPath
    fileSavedPath=SavedPath
    list = os.listdir(fileSavedPath)
    list = sorted(list, key=lambda x: (int(re.sub('\D','',x)),x))
    for l in list:
        dealwith_mulitpocess(l)


def filebyfileHandle(fileSavedPath='./news/',rejectOfDocSize=400,multiprocess=4,number_doc=-1):
    # mkdir(fileSavedPath)
    # fp = open(fileSavedPath, 'r')
    x = 0
    fileSavedPath=fileSavedPath
    rejectOfDocSize=rejectOfDocSize
    list = os.listdir(fileSavedPath)

    if(number_doc==-1 or number_doc > len(list)):
        number_doc = len(list)
    list = sorted(list[:number_doc], key=lambda x: (int(re.sub('\D','',x)),x))
    from multiprocessing import Pool as ThreadPool
    pool = ThreadPool(multiprocess)
    try:
        dictionary = pool.map(dealwith_mulitpocess,  list)
    except Exception as e:
        print e
        pass
    pool.close()
    pool.join()

    
    # for file in list:
    #     filepath = os.path.join(fileSavedPath,file)
    #     if not os.path.isdir(filepath):
    #         fp = open(filepath, 'r+')
    #         content=''
            
    #         for line in fp:
    #             content = content + line
    #         # print content
    #         content = content.replace(r'\n', '').replace(r'▉', '').replace(r'\t', '').replace(' ', '')
    #         # content = re.sub(p, '', content)
    #         content = stripTags(content)
    #         content = delNOTNeedWords(content,stopwords)
    #         if len(content) > rejectOfDocSize:
    #             fp.write(stripTags(content))
    #             fp.close()
    #             x = x + 1
    #             print x

def dealwith_mulitpocess(file):
    filepath = os.path.join(fileSavedPath,file)
    if not os.path.isdir(filepath):
        fp = open(filepath, 'r+')
        content=''

        for line in fp:
            content = content + line
        # print content
        content = content.replace(r'\n', '').replace(r'▉', '').replace(r'\t', '').replace(' ', '')
        # content = re.sub(p, '', content)
        content = stripTags(content)
        content = delNOTNeedWords(content,stopwords)
        if len(content) > rejectOfDocSize:
            fp.truncate(0)
            position = fp.seek(0, 0);
            fp.write(content)
            fp.close()
            # x = x + 1
            print filepath

# filebyfileHandle('../news',100,1)
# p = re.compile('\s+')

# 第一个参数需要分割的文件位置。
# 第二个参数分割完文件存储目录。
# 第三个参数最多分割的文件数量，0表示分割完所有文件。
# 第四个参数表示拒绝文档大小，小于此数值的全都不存储不做处理
def spiltDocument(spiltfileloc,fileSavedPath='./news/',total=0,rejectOfDocSize=400):
    # print fileSavedPath
    mkdir(fileSavedPath)
    fp = open(spiltfileloc, 'r')
    x = 0
    for line in fp:
        # print total
        if (total!=0 and x>=total):return  #如果大于输入的total数量则程序终止，决定多少个
        c = str(line)

        if c.find('INSERT INTO `tmp_article` VALUES (', 0) < 0:
            continue
        # c = unicode(c, errors='ignore')
        c = c.split('(', 1)[1]
        c = c[:-1]
        # print c
        # print c
        cs = c.split('),(')
        print len(cs)
        for cc in cs:
            # print cc
            if len(cc) > 0:
                # name = raw_input()
                name = cc.split(',', 1)[0]
                name = name[1:-1]
                name = os.path.normpath(name)
                name = validateTitle(name)
                # print name
                if len(cc.split(',')) > 1:
                    content = cc.split(',', 1)[1]
                    content = content[1:-1]
                    # print content

                    

                    # name = eval("'%s'" % name)
                    # name = raw_input(name.decode('utf8'))
                    content = content.replace(r'\n', '').replace(
                        r'▉', '').replace(r'\t', '').replace(' ', '')
                    # content = re.sub(p, '', content)
                    content = stripTags(content)
                    content = delNOTNeedWords(content,stopwords)
                    if len(content) > rejectOfDocSize:
                        try:
                            fnew = open(
                                fileSavedPath + '/' + str(x)+name.decode('utf-8', 'ignore') + '.txt', 'w')
                        except:
                            # print EOFError
                            continue
                            # continue

                        # fnew.write(stripTags(content.decode('gbk','ignore').encode('utf-8','ignore')))
                        fnew.write(stripTags(content))
                        fnew.close()

                        x = x + 1
                        print x


    # for line in fp:
    #     c = str(line)
    #     cx = cx + c
    # 打开一个新文件写
    # fnew=open(mkpath+'/'+c.split('<')[0]+'.txt','w')  //
    #     if len(c) > 0:
    #         if c[len(c) - 2] == '\\':
    #             continue

    #         name = cx.split('   ')[0]
    #         name = os.path.normpath(name)
    #         try:
    #             fnew = open(mkpath + '/' + name.decode('utf8') + '.txt', 'w')
    #         except:
    #             cx = ''
    #             continue
    # fnew=open(mkpath+'/'+cx[0:20]+'.txt','w')
    #         fnew.write(stripTags(cx))
    #         fnew.close()
    #         cx = ''
    fp.close()
