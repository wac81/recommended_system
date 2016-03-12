# -*- coding:utf-8 -*-
# coding=utf-8
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
import re
import json
import codecs
import jieba
jieba.initialize()   #manual initialize jieba
import cPickle

import os
from gensim import corpora, models, similarities
from flask import Flask, request, abort,g,current_app
# from werkzeug.contrib.fixers import ProxyFix
app = Flask(__name__)

project_path = './'
docpath='/home/workspace/news'
pkl_file_name = "./prefix_map/filename_map.pkl"

# @app.before_first_request
# @app.before_request
def appd():
    app.config['stopwords'] = codecs.open(project_path + 'stopwords.txt', encoding='UTF-8').read()

    app.config['dictionary'] = corpora.Dictionary.load(project_path + 'lsi/' + 'viva.dict')
    # baobao changed 4 lines
    # app.config['lsi'] = models.LsiModel.load(project_path + 'lsi/' + 'viva.lsi')
    app.config['lsi'] = models.lsimodel.LsiModel.load(project_path + 'lsi/' + 'viva.lsi')
    # app.config['index'] = similarities.MatrixSimilarity.load(project_path + 'lsi/' + 'viva.index')
    app.config['index'] = similarities.docsim.Similarity.load(project_path + 'lsi/' + 'viva.index')
    files = os.listdir('./news/')
    app.config['files'] = sorted(files, key=lambda x: (int(re.search(r'([0-9]+)(_)', x).group(1)),x))

    if os.path.isfile(pkl_file_name):
        t_fp = open(pkl_file_name, 'rb')
        filesd = cPickle.load(t_fp)
        t_fp.close()
    else:
        print("filename_map.pkl have not created")
        filesd = {}
    app.config['files_dict'] = filesd

    print('All loaded')
appd()

@app.route('/similar/<input_text>',methods=['GET', 'POST'])
def similar(input_text):
    re=object
    if request.method == 'POST':
        re = request.form['text']
    else:
        try:
            re = input_text  # 获取GET参数，没有参数就赋值 0
        except ValueError:
            abort(404)      # 返回 404
    result = json.dumps(similar_search(re))
    print result
    return result


@app.route('/')
def index():
    return '相似度推荐 for viva，GET方式：请访问/similar/[传入字串] \n POST方式：请访问/similar/post  post体里text=[传入字串]'

# baobao add whole function
@app.route('/getfiles/<input_text>',methods=['GET', 'POST'])
def getfiles(input_text):
    re=object
    if request.method == 'POST':
        files = request.form['files']
        # name = request.form['name']
    else:
        try:
            re = input_text  # 获取GET参数，没有参数就赋值 0
        except ValueError:
            abort(404)      # 返回 404
    result = json.loads(files)

    # baobao write files
    add_files_path = "./news_post_add/"
    if not os.path.exists(add_files_path):
        os.mkdir(add_files_path)
    else:
        files = os.listdir(add_files_path)
        for i in files:
            os.remove(add_files_path + i)
    for i in result:
        fp = open(add_files_path + i['name'], 'wb')
        fp.write(i['text'])
        fp.close()

    # if len(result)!=0:
    #     from similarity_update import sim_update
    #     sim_update(result)
    print("Run the shell.")
    os.system('./after_update.sh')
    # os.system('sh ../cms/task.sh')
    print("Shell done!")
    print result
    return result


def check_prefix(file_in):
    """
    baobao add for checking files prefix map
    :param file_in:  string
    :return: string
    """

    # try:
    #     file_a = file_in.decode('gbk')
    # except Exception as e:
    file_a = file_in.decode('utf-8')

    # try:
    #     fp = open(, 'rb')
    #     files = cPickle.load(fp)
    #     fp.close()
    # except Exception as e:
    #     files = {}
    filesd = app.config['files_dict']


    if file_a in filesd.keys():
        print("From dict %s" % file_a)
        return filesd[file_a]
    else:
        print("From news %s" % file_in)
        return file_in


def similar_search(request):
    doc = request
    doc = stripTags(doc)
    doc = "".join(doc.split())
    doc = delstopwords(doc)[1]
    vec_bow = app.config['dictionary'].doc2bow(doc)
    vec_lsi = app.config['lsi'][vec_bow]

    # baobao changed
    index = app.config['index']
    index.num_best = 10 # baobao
    sims = index[vec_lsi]
    sort_sims = sims    # baobao
    # print sims
    # sort_sims = sorted(enumerate(sims), key=lambda item: -item[1])    # baobao comment
    # sorted(word_similarities.items(), key=lambda x: x[1],reverse=True)

    no = []
    qz = []
    tempqz=[]
    ss = sort_sims[0:10]
    print len(ss)
    # files = os.listdir('./news/')
    # files = sorted(files, key=lambda x: (int(re.sub('\D','',x)),x))
    files = app.config['files']
    for i in range(len(ss)):
        #if ss[i][1]>=0.99:continue  #将1：0.99相似度的文件剔除

        #取文件真实id，viva

        # print ss[i]
        # print ss[i][0]
        # print files[299]
        fileid=files[ss[i][0]]

        # baobao add 1 line
        fileid = check_prefix(fileid)

        fileid=fileid.split('_')
        singleno = fileid[0]
        singleqz = str(ss[i][1])

        #取正常文章序号
        # singleno = str(ss[i][0])
        # singleqz = str(ss[i][1])

        if len(qz)==0:
            no.append(singleno)
            qz.append(singleqz)
            tempqz.append(singleqz)

        if abs(float(tempqz[len(tempqz)-1])-ss[i][1])>0.0015:
            no.append(singleno)
            qz.append(singleqz)
        tempqz.append(singleqz)

    concat = {'similarNO':no,'similarQZ':qz}
    return concat


def delstopwords(content):
    result=''

    words = jieba.lcut(content)
    return_words = []
    for w in words:
        if w not in app.config['stopwords']:
            result += w.encode('utf-8')  # +"/"+str(w.flag)+" "  #去停用词
            return_words.append(w.encode('utf-8'))

    # words = pseg.lcut(content)
    # with app.test_request_context():
    # for word, flag in words:
    #     if (word not in app.config['stopwords'] and flag not in ["/x","/zg","/uj","/ul","/e","/d","/uz","/y"]): #去停用词和其他词性，比如非名词动词等
    #         result += word.encode('utf-8')  # +"/"+str(w.flag)+" "  #去停用词
    #             print result
    return result,return_words


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


if __name__ == '__main__':
    with app.app_context():
        print current_app.name
    app.run(debug=False, host='0.0.0.0', port=3001)


