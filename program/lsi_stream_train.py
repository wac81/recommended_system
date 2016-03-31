#! /usr/bin/env python
# -*- coding:utf-8 -*-

import codecs
import jieba
from gensim import corpora, models, similarities
from gensim.models import lsimodel, LsiModel
from collections import defaultdict
from pprint import pprint
import sys
import os
import logging
import time
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
# lsipath = './lsi/'
# articleDir = './a/'
# project_path = './'



# def getFile():
#     count = 0
#     for filename in os.listdir(articleDir.decode('utf-8')):
#         count += 1
#         print count
#         yield codecs.open(articleDir + filename, encoding='UTF-8').read()

# class MyCorpus(object):
#     def __iter__(self):
#         for file in getFile():
#             yield dictionary.doc2bow(jieba.lcut(file))

#num_topics 定义主题数量，默认300，处理4w以下文件数量，google推荐300-500
def getLsiModel(lsipath='./lsi/', num_topics=300):
    # 加载字典
    dictionary = corpora.Dictionary.load(lsipath + 'viva.dict')
    print '字典加载完毕'
    # 语料库
    corpus = corpora.MmCorpus(lsipath +'viva.mm')
    print ('mm load')

    t31 = time.time()

    # tfidf
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = tfidf[corpus]
    t32 = time.time()
    print "tfidf_corpus time = ", t32 - t31

    # baobao change 3 lines
    # corpus = MyCorpus()
    # lsi = models.LsiModel(corpus, id2word=dictionary, num_topics=NUM_TOPIC,power_iters=2,chunksize=50000,onepass=True,distributed=False)
    # lsi = lsimodel.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=num_topics,chunksize=20000)
    lsi = lsimodel.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=NUM_TOPIC, chunksize=50000)  #其他参数都是默认

    lsi.save(lsipath  + 'viva.lsi')
    print('lsi模型保存完毕')
    return  lsi

if __name__ == '__main__':
    NUM_TOPIC = 300  # 主题的数量，默认为 300
    lsipath = '../nlsi/'
    lsimodel = getLsiModel(lsipath=lsipath, num_topics=NUM_TOPIC)
