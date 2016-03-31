# -*- coding:utf-8 -*-

import os
import re
import jieba
import codecs
import jieba.posseg as pseg
from multiprocessing import Pool as ThreadPool
filesPath='./news/'
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


# 停用词
stopwords = codecs.open('stopwords.txt', encoding='UTF-8').read().split(u'\n')
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
    global filesPath
    filesPath = fileSavedPath
    rejectOfDocSize=rejectOfDocSize
    list = os.listdir(fileSavedPath)

    if(number_doc==-1 or number_doc > len(list)):
        number_doc = len(list)
    # list = sorted(list[:number_doc], key=lambda x: (int(re.sub('\D','',x)),x))

    pool = ThreadPool(multiprocess)
    # try:
    dictionary = pool.map(dealwith_mulitpocess, list)
    # except Exception as e:
    #     print e
    #     pass
    pool.close()
    pool.join()


def dealwith_mulitpocess(file):
    global filesPath
    filepath = os.path.join(filesPath,file)
    if not os.path.isdir(filepath):
        # content = None
        # with open(filepath, 'r') as fp:  #r+是读写
        #     content = fp.read()
        #
        # content = stripTags(content)
        # content = "".join(content.split())
        #
        # if len(content) > rejectOfDocSize:
        #     content = delNOTNeedWords(content,stopwords)
        #     with open(filepath,'w') as fp:
        #         fp.write(content)
        #         print filepath
        # else:
        #     # 文件大小小于特定值就删除文件，不进入模型
        #     os.remove(filepath)


        #truncate  delete file mode  faster 5%
        fp = open(filepath, 'r+') #r+是读写
        content = fp.read()
        content = stripTags(content)
        content = "".join(content.split())

        if len(content) > rejectOfDocSize:
            content = delNOTNeedWords(content,stopwords)
            fp.truncate()
            position = fp.seek(0, 0);
            fp.write(content)
            fp.close()
            # x = x + 1
            print filepath
        else:
            fp.close()
            # 文件大小小于特定值就删除文件，不进入模型
            os.remove(filepath)

if __name__ == '__main__':
    import multiprocessing
    import time
    docpath = '/home/wac/PycharmProjects/recommended_system/nnews/'

    NUM_DOC = -1  # 所选取的语料集中的文件数量
    cpu_num = multiprocessing.cpu_count()
    doc_limit = 100
    t31 = time.time()
    filebyfileHandle(docpath, doc_limit, cpu_num, NUM_DOC)  # 100字符内的文件抛掉不处理,多进程不指定默认 multiprocess=4
    t32 = time.time()
    print "filebyfileHandle time = ", t32 - t31