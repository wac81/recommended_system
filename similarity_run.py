# -*- coding:utf-8 -*-
import os
import sys
# import shutil
sys.path.append("./program/")
import time
# def f(x):
    # return corpora.Dictionary(jieba.lcut('我们可以'))
time_before = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
print time_before

import jieba.posseg as pseg
import codecs
# from program import *
stopwords = codecs.open('./program/stopwords.txt', encoding='UTF-8').read()

def delstopwords(content):
    # words = jieba.lcut(content)
    result=''
    # for w in words:
    #     if w not in stopwords:
    #         result += w.encode('utf-8')  # +"/"+str(w.flag)+" "  #去停用词

    words = pseg.lcut(content)
    for word, flag in words:
        if (word not in stopwords and flag not in ["/x","/zg","/uj","/ul","/e","/d","/uz","/y"]): #去停用词和其他词性，比如非名词动词等
            result += word.encode('utf-8')  # +"/"+str(w.flag)+" "  #去停用词
            print result
    return result

# doc = delstopwords('你们觉得天地会的人真心把他当自己人仅仅是因为他滑头？康熙把他当最珍贵的【划去】基【/划去】朋友仅仅是因为他胆子大？')
# print doc
if __name__ == '__main__':
	filesaved = 'article.sql'
	docpath='./nnews/'
	lsipath='./nlsi/'
	NUM_TOPIC = 300		# 主题的数量，默认为 300
	NUM_DOC = -1		# 所选取的语料集中的文件数量

	# if os.path.exists(docpath):
	# 	shutil.rmtree(docpath)  # 删除目录
	# if os.path.exists(lsipath):
	# 	shutil.rmtree(lsipath)  # 删除目录
	t01 = time.time()
	if  os.path.exists(docpath):
		from ar import filebyfileHandle
		filebyfileHandle(docpath,100,4,NUM_DOC)   #100字符内的文件抛掉不处理,多进程默认 multiprocess=4
	t02 = time.time()

	t11 = time.time()
	from dict_stream_train import getDictionary
	dict = getDictionary(lsipath=lsipath, docpath=docpath)
	t12 = time.time()

	t21 = time.time()
	from corpus_stream_train import getCorpus
	corpus = getCorpus(lsipath=lsipath, docpath=docpath)
	t22 = time.time()

	t31 = time.time()
	from lsi_stream_train import getLsiModel
	lsimodel = getLsiModel(lsipath=lsipath, num_topics=NUM_TOPIC)
	t32 = time.time()

	t41 = time.time()
	from index_stream_train import getIndex
	getIndex(lsipath, NUM_TOPIC)	#change by baobao ,add NUM_TOPIC
	t42 = time.time()

	print "prepare time = ", t02-t01
	print "dict time = ", t12-t11
	print "corpus time = ", t22-t21
	print "lsimodel time = ", t32-t31
	print "getIndex time = ", t42-t41
	# p = Pool(5)
    # d = corpora.Dictionary(jieba.cut('我们可以'))
    # print d
    # print( corpora.Dictionary(jieba.lcut('我们可以')))
    # print(p.map(f, ['aa', 'ab', 'ac']))

timenow = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
print time_before
print timenow