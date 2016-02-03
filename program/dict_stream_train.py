#! /usr/bin/env python
# coding=utf-8

import codecs
import jieba
from gensim import corpora, models, similarities
from collections import defaultdict
from pprint import pprint
import sys
import os
import re
import urllib2
from multiprocessing.dummy import Pool as ThreadPool

# lsipath = './lsi/'
def getFile(docpath='./news/'):
	count = 0
	files = os.listdir(docpath)
	files = sorted(files, key=lambda x: (int(re.sub('\D','',x)),x))
	for filename in files:
		count += 1
		print count
		# print codecs.open(docpath + filename, encoding='UTF-8').read()
		try:
			yield codecs.open(docpath + filename).read()
			print filename
		except:
			print filename
			continue

# 并行计算
# def easy_parallize(f, sequence):
# I didn't see gains with .dummy; you might
#     from multiprocessing import Pool.
#     pool = Pool(processes=8)
# from multiprocessing.dummy import Pool
# pool = Pool(16)

# f is given sequence. Guaranteed to be in order
#     result = pool.map(f, sequence)
#     cleaned = [x for x in result if not x is None]
#     cleaned = asarray(cleaned
# not optimal but safe
#     pool.close()
#     pool.join()
#     return cleaned
# def parallel_attribute(f):

#     from functools import partial
# This assumes f has one argument, fairly easy with Python's global scope
#     return partial(easy_parallize, f)


# def some_function_parallel(x, y, z):
#     def some_function(x):
# x is what we want to parallelize over
# complicated computation
#         jieba.lcut(x)
#         return x+y+z
#     return some_function(x, y, z)


# def some_function(x):

#     return jieba.lcut(x)

# dictionary= parallel_attribute(some_function)
def getDictionary(lsipath='./lsi/', docpath='./news/'):
	stopwords = codecs.open('stopwords.txt', encoding='UTF-8').read()
	stopwordSet = set(stopwords.split('\r\n'))
	print('All' + str(len(stopwordSet)) + 'stopwords')

	dictionary = corpora.Dictionary(jieba.lcut(file) for file in getFile(docpath))
	# for  file in getFile():
	#         try:
	#                 dictionary = corpora.Dictionary(jieba.lcut(file) file in getFile())
	#         except:
	#                 print file
	#                 continue
	# def deal_corpora(str):
	#     print str
	# print jieba.lcut(str)
	#     return list(corpora.Dictionary(jieba.lcut(str)))

	# pool=ThreadPool(4)
	# dictionary = pool.map(deal_corpora,  getFile())
	# print 'kkkkkkkkkkkkk'
	# pool.close()
	# pool.join()

	print '过滤前的字典：'
	print dictionary

	stop_ids = [dictionary.token2id[stopword]
	            for stopword in stopwordSet if stopword in dictionary.token2id]
	print '语料中出现过的停词个数：'
	print len(stop_ids)

	once_ids = [tokenid for tokenid,
	            docfreq in dictionary.dfs.iteritems() if docfreq == 1]
	print '全文低频词个数：'
	print len(once_ids)

	dictionary.filter_tokens(stop_ids + once_ids)
	dictionary.compactify()
	print '过滤后的字典：'
	print(dictionary)

	mkdir(lsipath)

	dictionary.save(lsipath + 'viva.dict')
	print('字典保存完毕')
	return dictionary


def mkdir(path):
	# 引入模块
    import os

	# 去除首位空格
    path = path.strip()
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
