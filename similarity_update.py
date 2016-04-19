# -*- coding:utf-8 -*-
import codecs
import jieba
from gensim import corpora, models, similarities, matutils
from gensim.models import lsimodel, LsiModel, tfidfmodel
import jieba.posseg as pseg
import codecs
import shutil
import os
import re
import sys
import time
import itertools

sys.path.append("./program/")

# constants
lsipath = './lsi/'
lsitemp = './lsitemp/'
docpath = './news/'  # text posted one by one, otherwise docpath="./news_add/"
news_post_add = "./news_post_add/"
DECAY_FACTOR = 0.999  # decay factor[0.0, 1.0] for merging two decomposed matrix
NUM_TOPIC = 300
chunksize = 60000
stopwords = codecs.open('stopwords.txt', encoding='UTF-8').read().split(u'\n')


# functions
def delstopwords(content):
    result = ''
    words = pseg.lcut("".join(content.split()))
    for word, flag in words:
        if word not in stopwords and flag not in ["/x", "/zg", "/uj", "/ul", "/e", "/d", "/uz",
                                                  "/y"]:  # 去停用词和其他词性，比如非名词动词等
            result += word.encode('utf-8')  # +"/"+str(w.flag)+" "  #去停用词
    return result


def sim_update(results):
    """
    Update Models.
    :param results:
    :return:
    """

    shutil.rmtree(lsitemp,ignore_errors=False)
    mkdir(lsitemp)


    t_total_begin = time.time()

    # print("Checking repeat ...")
    # results_temp = check_repet_new(results)
    results_temp = results
    # print("Check repeat complete!")
    print("Prefix mapping ...")
    results = prefix_map(results_temp)
    print("Prefix map complete!")
    del results_temp

    print("Building LSI model ...")

    # Extended Dictionary
    dictionary = corpora.Dictionary.load(lsipath + 'viva.dict')
    # Load Models
    corpus_raw = corpora.MmCorpus(lsipath + 'viva.mm')
    lsi = lsimodel.LsiModel.load(lsipath + 'viva.lsi')  # 将 mm 文件中的 corpus 映射到 LSI 空间当中

    mkdir(news_post_add)

    # Preporcessing text. Get corpus_add.
    for postfile in results:
        deltags = stripTags(postfile['text'])
        text_del = delstopwords("".join(deltags.split()))
        # text_vec = jieba.lcut(text_del)
        # del and
        with open(news_post_add + postfile['name'], 'w') as fp:
            fp.write(text_del)

    files = os.listdir(news_post_add)
    for i in files:
        shutil.copy(news_post_add + i, docpath)

    from dict_stream_train import getDictionary
    dict2 = getDictionary(lsipath=lsitemp, docpath=news_post_add)
    dict2 = corpora.Dictionary.load(lsitemp + 'viva.dict')

    from corpus_stream_train import getCorpus
    corpus2 = getCorpus(lsipath=lsitemp, docpath=news_post_add)
    corpus2 = corpora.MmCorpus(lsitemp + 'viva.mm')

    dict2_to_dict1 = dictionary.merge_with(dict2)
    # dict2_to_dict1.save(lsipath + 'viva2.dict')
    # dict2_to_dict1 = corpora.Dictionary.load(lsipath + 'viva2.dict')

    merged_corpus = itertools.chain(corpus_raw, dict2_to_dict1[corpus2])
    corpora.MmCorpus.serialize(lsipath + 'viva.mm', [i for i in merged_corpus])
    merged_corpus = corpora.MmCorpus(lsipath + 'viva.mm')

    # Get TF-IDF vecters of documents
    tfidf = tfidfmodel.TfidfModel(merged_corpus)
    print("Building tfidf model ...")
    corpus_tfidf = tfidf[merged_corpus]
    print("Building corpus_tfidf model ...")
    # Updated LSI Model

    # lsi.add_documents(corpus_tfidf, chunksize=chunksize, decay=DECAY_FACTOR)
    # # lsi.add_documents(corpus_tfidf, chunksize=chunksize)
    #
    # print("Builded lsi add documents to model ...")
    # # Updated Corpus
    # if not os.path.exists(lsipath):
    #     os.mkdir(lsipath)
    # # corpus = corpora.MmCorpus.serialize(lsipath + 'viva.mm', itertools.chain(corpus_raw, corpus2))

    lsi = lsimodel.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=NUM_TOPIC, chunksize=chunksize, power_iters=2, onepass=True)  # 其他参数都是默认

    lsi.save(lsipath + 'viva.lsi')
    lsi = models.lsimodel.LsiModel.load(lsipath + 'viva.lsi')
    index = similarities.docsim.Similarity(lsipath + 'viva.index', lsi[merged_corpus], num_features=NUM_TOPIC)
    # Save Models

    index.save(lsipath + 'viva.index')
    print("LSI model saved!")

    # Print elasped time
    t2 = time.time()
    print "Total elapsed time is: ", t2 - t_total_begin, "s"


def prefix_map(result_in):
    """

    :param result_in: [{}{}{}]
    :return:[{}{}{}]
    """
    import cPickle
    import os
    mapdir = "./prefix_map/"
    mkdir(mapdir)
    pkl_file_name = mapdir + "filename_map.pkl"
    if os.path.isfile(pkl_file_name):
        t_fp = open(pkl_file_name, 'rb')
        name_dict = cPickle.load(t_fp)
        t_fp.close()
    else:
        print("filename_map.pkl have not created")
        name_dict = {}

    # Get max prefix value
    files = os.listdir("./news/")
    files_order = sorted(files, key=lambda x: (int(re.search(r'([0-9]+)(_)', x).group(1)), x))
    max_prefix = int(re.search(r'([0-9]+)(_)', files_order[-1]).group(1)) + 1
    result_out = []
    fp = open(pkl_file_name, 'wb')
    for i in result_in:
        old_name = i['name']
        new_name = re.sub(r'([0-9]+)(_)', str(max_prefix) + '_', old_name)
        name_dict[new_name] = old_name
        max_prefix += 1
        result_out.append({'name': new_name, 'text': i['text']})
    cPickle.dump(name_dict, fp)
    fp.close()
    return result_out


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


if __name__ == '__main__':
    # result = [
    #     # {'name':u'4_不能写入二', 'text':u'<p>“ 这些照片拍摄于1925年，看到这些照片后,希特勒要求霍夫曼毁掉底片，但他没有照做。而是发表在他的回忆录“希特勒是我的朋友”中，1955年出版。</p><p>1925年希特勒在镜子前练习演讲,</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width9238f74daf98ae5e07e71ca6c0a546d448da63dc.jpg\"></span></p><p>希特勒的演讲不单单只是抓住了人民的心底最可怕的好战情绪和第一次战败的耻辱。更关键的是。在他演讲的时候。你完全不会觉得他是在有意的让你去做某些事情。</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width058a206e9d52ef5580b9fa9d2ca34b7bf4eb7e29.jpg\"></span></p><p>希特勒的某些细节把握的非常好。他知道听众要听什么。</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width990ceb2ee4bc0e269966acca5655337d35e350f4.jpg\"></span></p><p>希特勒的演讲像是一个歌手在开演唱会，他能细腻的表达和抓住观众的心情，从而制造出 最大的 欢呼声。在不知不觉中 民众就会 陷入 狂热状态。失去理智，从而坚定信念。</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width30afbd98af5082d906f6fce5a694e31e58810e8a.jpg\"></span></p><p>希特勒所演讲的内容。和他内心高度统一。所以他是在释放他狂热的思想。完全不会显得做作。所以大家找不出他的虚假。更真实更狂热。</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width897f307f8d7cf78353ea59cee43f4e7749d50bb2.jpg\"></span></p><p>宣传最好的办法就是在对方还未察觉你的动态时直接灌输与他们你的思想。希特勒就是这样。</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width98022df90102c66c84d961754aed69a43fdbdc7a.jpg\"></span></p><p>真实可信。狂热民族主义。都是他的演讲成功的重要手段。从而成为他掌握国家走向的正治手段。</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width43e17deda875f50fdef1713292315ed0b043f506.jpg\"></span></p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width1bf20e753c9726299cc0cb06f850894296e23c25.jpg\"></span></p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width1735c6f9af92af90d2f331825f442d24ded13d13.jpg\"></span></p>","name":"3546083768298267441_图志丨1925年希特勒在镜子前练习演讲的照片曝光'},
    #     # {'name':u'4036351344334950000000000003014_探索涠洲岛的各种可能性', 'text':u'探索涠洲岛可能性中国国家旅游2015月刊涠洲岛位于北部湾中部中国最大地质年龄年轻火山岛中国确认火山地质遗迹已有不少唯一海岛建立火山地质遗迹保护区涠洲岛面积大约25平方公里鼓浪屿倍流量控制每天允许岛游客数量相当于鼓浪屿实际上岛游客没有太商业化矫饰深蓝色海等待挖掘旅行无限可能完探索涠洲岛可能性中国国家旅游2015月刊涠洲岛位于北部湾中部中国最大地质年龄年轻火山岛中国确认火山地质遗迹已有不少唯一海岛建立火山地质遗迹保护区涠洲岛面积大约25平方公里鼓浪屿倍流量控制每天允许岛游客数量相当于鼓浪屿实际上岛游客没有太商业化矫饰深蓝色海等待挖掘旅行无限可能完探索涠洲岛可能性中国国家旅游2015月刊涠洲岛位于北部湾中部中国最大地质年龄年轻火山岛中国确认火山地质遗迹已有不少唯一海岛建立火山地质遗迹保护区涠洲岛面积大约25平方公里鼓浪屿倍流量控制每天允许岛游客数量相当于鼓浪屿实际上岛游客没有太商业化矫饰深蓝色海等待挖掘旅行无限可能完探索涠洲岛可能性中国国家旅游2015月刊涠洲岛位于北部湾中部中国最大地质年龄年轻火山岛中国确认火山地质遗迹已有不少唯一海岛建立火山地质遗迹保护区涠洲岛面积大约25平方公里鼓浪屿倍流量控制每天允许岛游客数量相当于鼓浪屿实际上岛游客没有太商业化矫饰深蓝色海等待挖掘旅行无限可能完'},
    #     # {'name':u'4036351344334950000000000003015_读木心', 'text':u'读木心时尚健康2015月刊上读木心成年之后事当年张爱玲找出来二十出头年纪读张爱玲刚好适合黄磊北京电影学院教师导演演员歌手每次读随意自由语句漂泊不定流亡者却有着一颗充满美妙心嘲弄嘲笑闹跳跃木心目空一切不屑于提及目空一切木心想住熟悉乌镇竟然没有一丝冲动想要找到索要签名合影后来丹青老师喜欢木心却找他时竟然回答出最为准确感受懂事儿回答养老读者不该打扰丹青老师赞教养心中想法却是害怕不知所措无法熟悉文字本人对应连接如同面对故乡情怯过世几年倒不算一件大事世界生死具体化鱼丽宴写到独自空身走手帕般大曙光现代人早已不用手帕知道私人曙光闭上眼想着空身走的确无关生死死殉道易死殉道难择难几年读木心似乎流行热捧一再强调文坛直接引用原话所谓文坛木心一生传奇木心其实躲角落里抽纸烟老家伙独享一份小规模荡气回肠如果说曾经忽略想今天没有忽略知道读同样忽略刚好完全不在乎忽略忽略无足轻重世界早已习惯世界没有世界没有刚刚木心先生世界大家热这一阵子找曾经模糊不清孤独出来翻热烈讨论喝采一起把头扎堆找模糊不清孤独空身向前头回木心先生其实太后世读解读者关心写文字够有时重读书重读当初一旁写下读后笔记重温木心重温这种感觉好极了木心先生独立所有中文作者或者说根本没有打算写作写渴望解救字字救出来究竟束缚绑架掠去自由身心问题老寻根问底找到答案恐怕难若真找到整盘端上来恐怕吓人字字写下去不会有人读下去信仰信仰信仰木心先生如是说信其实书不算真正认识了解几次宏谈志木心像是老父亲听心中一片浮想浮想浮起来愈发模糊木心样子原本在我心中文字机敏短句感叹变成血肉骨骼俱全老头子夹烟卷戴顶灰褐色毛线帽斜倚乌镇东栅靠近逢源双桥回廊美目光不连贯记忆牙齿眼神松动烟灰掉裤腰腿风吹散落青石板铺就小路上游客兴高采烈走过双桥财神湾走高声议论部电视剧拍前面不远处男主角修书书院没有人会注意昏昏欲睡老人一如喧嚣世界木心先生样子也许样子不论是真实样子记忆字句清晰一条一天到晚游泳鱼柔肠百转一天天冷酷起来少年郎坚决表示请包括包括调笑认真想着叼纸烟天堂骑白马入地狱字字句句才真真正正清清楚楚读木心成年之后事当年张爱玲找出来二十出头年纪读张爱玲刚好适合情爱故事机锋设计成年之后读故事相信信不会投入投入一下子没睡熟尿憋醒读木心正合适一句一句单独拎出来看到放放下闭上眼心里放不下盘来绕去一两句笑出来才睡不想挤兑任何人如今一大堆挤兑别人写字不好写一手矫情字儿木心估计不会应该压根没有看过知名度来自误解误解知名度成正比误解知名度高如今谈木心写木心包括加入想必有着不少误解写突然想到河岸边坐老头子抽口香烟烟雾缭绕笑木心先生其实太后世读解读者关心写文字够有时重读书重读当初一旁写下读后笔记重温木心重温这种感觉好极了读木心时尚健康2015月刊上读木心成年之后事当年张爱玲找出来二十出头年纪读张爱玲刚好适合黄磊北京电影学院教师导演演员歌手每次读随意自由语句漂泊不定流亡者却有着一颗充满美妙心嘲弄嘲笑闹跳跃木心目空一切不屑于提及目空一切木心想住熟悉乌镇竟然没有一丝冲动想要找到索要签名合影后来丹青老师喜欢木心却找他时竟然回答出最为准确感受懂事儿回答养老读者不该打扰丹青老师赞教养心中想法却是害怕不知所措无法熟悉文字本人对应连接如同面对故乡情怯过世几年倒不算一件大事世界生死具体化鱼丽宴写到独自空身走手帕般大曙光现代人早已不用手帕知道私人曙光闭上眼想着空身走的确无关生死死殉道易死殉道难择难几年读木心似乎流行热捧一再强调文坛直接引用原话所谓文坛木心一生传奇木心其实躲角落里抽纸烟老家伙独享一份小规模荡气回肠如果说曾经忽略想今天没有忽略知道读同样忽略刚好完全不在乎忽略忽略无足轻重世界早已习惯世界没有世界没有刚刚木心先生世界大家热这一阵子找曾经模糊不清孤独出来翻热烈讨论喝采一起把头扎堆找模糊不清孤独空身向前头回木心先生其实太后世读解读者关心写文字够有时重读书重读当初一旁写下读后笔记重温木心重温这种感觉好极了木心先生独立所有中文作者或者说根本没有打算写作写渴望解救字字救出来究竟束缚绑架掠去自由身心问题老寻根问底找到答案恐怕难若真找到整盘端上来恐怕吓人字字写下去不会有人读下去信仰信仰信仰木心先生如是说信其实书不算真正认识了解几次宏谈志木心像是老父亲听心中一片浮想浮想浮起来愈发模糊木心样子原本在我心中文字机敏短句感叹变成血肉骨骼俱全老头子夹烟卷戴顶灰褐色毛线帽斜倚乌镇东栅靠近逢源双桥回廊美目光不连贯记忆牙齿眼神松动烟灰掉裤腰腿风吹散落青石板铺就小路上游客兴高采烈走过双桥财神湾走高声议论部电视剧拍前面不远处男主角修书书院没有人会注意昏昏欲睡老人一如喧嚣世界木心先生样子也许样子不论是真实样子记忆字句清晰一条一天到晚游泳鱼柔肠百转一天天冷酷起来少年郎坚决表示请包括包括调笑认真想着叼纸烟天堂骑白马入地狱字字句句才真真正正清清楚楚读木心成年之后事当年张爱玲找出来二十出头年纪读张爱玲刚好适合情爱故事机锋设计成年之后读故事相信信不会投入投入一下子没睡熟尿憋醒读木心正合适一句一句单独拎出来看到放放下闭上眼心里放不下盘来绕去一两句笑出来才睡不想挤兑任何人如今一大堆挤兑别人写字不好写一手矫情字儿木心估计不会应该压根没有看过知名度来自误解误解知名度成正比误解知名度高如今谈木心写木心包括加入想必有着不少误解写突然想到河岸边坐老头子抽口香烟烟雾缭绕笑木心先生其实太后世读解读者关心写文字够有时重读书重读当初一旁写下读后笔记重温木心重温这种感觉好极了读木心时尚健康2015月刊上读木心成年之后事当年张爱玲找出来二十出头年纪读张爱玲刚好适合黄磊北京电影学院教师导演演员歌手每次读随意自由语句漂泊不定流亡者却有着一颗充满美妙心嘲弄嘲笑闹跳跃木心目空一切不屑于提及目空一切木心想住熟悉乌镇竟然没有一丝冲动想要找到索要签名合影后来丹青老师喜欢木心却找他时竟然回答出最为准确感受懂事儿回答养老读者不该打扰丹青老师赞教养心中想法却是害怕不知所措无法熟悉文字本人对应连接如同面对故乡情怯过世几年倒不算一件大事世界生死具体化鱼丽宴写到独自空身走手帕般大曙光现代人早已不用手帕知道私人曙光闭上眼想着空身走的确无关生死死殉道易死殉道难择难几年读木心似乎流行热捧一再强调文坛直接引用原话所谓文坛木心一生传奇木心其实躲角落里抽纸烟老家伙独享一份小规模荡气回肠如果说曾经忽略想今天没有忽略知道读同样忽略刚好完全不在乎忽略忽略无足轻重世界早已习惯世界没有世界没有刚刚木心先生世界大家热这一阵子找曾经模糊不清孤独出来翻热烈讨论喝采一起把头扎堆找模糊不清孤独空身向前头回木心先生其实太后世读解读者关心写文字够有时重读书重读当初一旁写下读后笔记重温木心重温这种感觉好极了木心先生独立所有中文作者或者说根本没有打算写作写渴望解救字字救出来究竟束缚绑架掠去自由身心问题老寻根问底找到答案恐怕难若真找到整盘端上来恐怕吓人字字写下去不会有人读下去信仰信仰信仰木心先生如是说信其实书不算真正认识了解几次宏谈志木心像是老父亲听心中一片浮想浮想浮起来愈发模糊木心样子原本在我心中文字机敏短句感叹变成血肉骨骼俱全老头子夹烟卷戴顶灰褐色毛线帽斜倚乌镇东栅靠近逢源双桥回廊美目光不连贯记忆牙齿眼神松动烟灰掉裤腰腿风吹散落青石板铺就小路上游客兴高采烈走过双桥财神湾走高声议论部电视剧拍前面不远处男主角修书书院没有人会注意昏昏欲睡老人一如喧嚣世界木心先生样子也许样子不论是真实样子记忆字句清晰一条一天到晚游泳鱼柔肠百转一天天冷酷起来少年郎坚决表示请包括包括调笑认真想着叼纸烟天堂骑白马入地狱字字句句才真真正正清清楚楚读木心成年之后事当年张爱玲找出来二十出头年纪读张爱玲刚好适合情爱故事机锋设计成年之后读故事相信信不会投入投入一下子没睡熟尿憋醒读木心正合适一句一句单独拎出来看到放放下闭上眼心里放不下盘来绕去一两句笑出来才睡不想挤兑任何人如今一大堆挤兑别人写字不好写一手矫情字儿木心估计不会应该压根没有看过知名度来自误解误解知名度成正比误解知名度高如今谈木心写木心包括加入想必有着不少误解写突然想到河岸边坐老头子抽口香烟烟雾缭绕笑木心先生其实太后世读解读者关心写文字够有时重读书重读当初一旁写下读后笔记重温木心重温这种感觉好极了读木心时尚健康2015月刊上读木心成年之后事当年张爱玲找出来二十出头年纪读张爱玲刚好适合黄磊北京电影学院教师导演演员歌手每次读随意自由语句漂泊不定流亡者却有着一颗充满美妙心嘲弄嘲笑闹跳跃木心目空一切不屑于提及目空一切木心想住熟悉乌镇竟然没有一丝冲动想要找到索要签名合影后来丹青老师喜欢木心却找他时竟然回答出最为准确感受懂事儿回答养老读者不该打扰丹青老师赞教养心中想法却是害怕不知所措无法熟悉文字本人对应连接如同面对故乡情怯过世几年倒不算一件大事世界生死具体化鱼丽宴写到独自空身走手帕般大曙光现代人早已不用手帕知道私人曙光闭上眼想着空身走的确无关生死死殉道易死殉道难择难几年读木心似乎流行热捧一再强调文坛直接引用原话所谓文坛木心一生传奇木心其实躲角落里抽纸烟老家伙独享一份小规模荡气回肠如果说曾经忽略想今天没有忽略知道读同样忽略刚好完全不在乎忽略忽略无足轻重世界早已习惯世界没有世界没有刚刚木心先生世界大家热这一阵子找曾经模糊不清孤独出来翻热烈讨论喝采一起把头扎堆找模糊不清孤独空身向前头回木心先生其实太后世读解读者关心写文字够有时重读书重读当初一旁写下读后笔记重温木心重温这种感觉好极了木心先生独立所有中文作者或者说根本没有打算写作写渴望解救字字救出来究竟束缚绑架掠去自由身心问题老寻根问底找到答案恐怕难若真找到整盘端上来恐怕吓人字字写下去不会有人读下去信仰信仰信仰木心先生如是说信其实书不算真正认识了解几次宏谈志木心像是老父亲听心中一片浮想浮想浮起来愈发模糊木心样子原本在我心中文字机敏短句感叹变成血肉骨骼俱全老头子夹烟卷戴顶灰褐色毛线帽斜倚乌镇东栅靠近逢源双桥回廊美目光不连贯记忆牙齿眼神松动烟灰掉裤腰腿风吹散落青石板铺就小路上游客兴高采烈走过双桥财神湾走高声议论部电视剧拍前面不远处男主角修书书院没有人会注意昏昏欲睡老人一如喧嚣世界木心先生样子也许样子不论是真实样子记忆字句清晰一条一天到晚游泳鱼柔肠百转一天天冷酷起来少年郎坚决表示请包括包括调笑认真想着叼纸烟天堂骑白马入地狱字字句句才真真正正清清楚楚读木心成年之后事当年张爱玲找出来二十出头年纪读张爱玲刚好适合情爱故事机锋设计成年之后读故事相信信不会投入投入一下子没睡熟尿憋醒读木心正合适一句一句单独拎出来看到放放下闭上眼心里放不下盘来绕去一两句笑出来才睡不想挤兑任何人如今一大堆挤兑别人写字不好写一手矫情字儿木心估计不会应该压根没有看过知名度来自误解误解知名度成正比误解知名度高如今谈木心写木心包括加入想必有着不少误解写突然想到河岸边坐老头子抽口香烟烟雾缭绕笑木心先生其实太后世读解读者关心写文字够有时重读书重读当初一旁写下读后笔记重温木心重温这种感觉好极了'},
    #     {'name':u'4036351344334950000000000003016_黄振效牙雕海水云龙火镰套清', 'text':u'牙雕海水云龙火镰套长８cm宽7.2cm厚4.1cm火镰套盒荷包状盖盒部分组成盖盒口边缘呈覆钟式刻双线垂如意蟠夔纹全器采用浮雕技法两面共凸刻大小行龙条大龙条小龙条火珠颗器物满布苍龙纹饰龙足边露出飞溅浪花纹盒两侧分刻楷书乾隆壬戌1742振效恭制款盖顶盒底长方形小孔一条苏绣明黄缎带穿带上饰雕成莲叶形珊瑚连珠坠缎带连接盒内软囊囊细米珍珠穿成寿字共用珠164粒软囊内盛镂空錾夔龙纹金火镰一把玛瑙火石数块火引一小叠火镰工精纹美小巧玲珑这种雕刻精细火镰套盒紫禁城内不多见此件龙纹火镰盒皇帝御用之物清宫造办制作留有制作者黄振效名款一件珍品牙雕海水云龙火镰套长８cm宽7.2cm厚4.1cm火镰套盒荷包状盖盒部分组成盖盒口边缘呈覆钟式刻双线垂如意蟠夔纹全器采用浮雕技法两面共凸刻大小行龙条大龙条小龙条火珠颗器物满布苍龙纹饰龙足边露出飞溅浪花纹盒两侧分刻楷书乾隆壬戌1742振效恭制款盖顶盒底长方形小孔一条苏绣明黄缎带穿带上饰雕成莲叶形珊瑚连珠坠缎带连接盒内软囊囊细米珍珠穿成寿字共用珠164粒软囊内盛镂空錾夔龙纹金火镰一把玛瑙火石数块火引一小叠火镰工精纹美小巧玲珑这种雕刻精细火镰套盒紫禁城内不多见此件龙纹火镰盒皇帝御用之物清宫造办制作留有制作者黄振效名款一件珍品牙雕海水云龙火镰套长８cm宽7.2cm厚4.1cm火镰套盒荷包状盖盒部分组成盖盒口边缘呈覆钟式刻双线垂如意蟠夔纹全器采用浮雕技法两面共凸刻大小行龙条大龙条小龙条火珠颗器物满布苍龙纹饰龙足边露出飞溅浪花纹盒两侧分刻楷书乾隆壬戌1742振效恭制款盖顶盒底长方形小孔一条苏绣明黄缎带穿带上饰雕成莲叶形珊瑚连珠坠缎带连接盒内软囊囊细米珍珠穿成寿字共用珠164粒软囊内盛镂空錾夔龙纹金火镰一把玛瑙火石数块火引一小叠火镰工精纹美小巧玲珑这种雕刻精细火镰套盒紫禁城内不多见此件龙纹火镰盒皇帝御用之物清宫造办制作留有制作者黄振效名款一件珍品牙雕海水云龙火镰套长８cm宽7.2cm厚4.1cm火镰套盒荷包状盖盒部分组成盖盒口边缘呈覆钟式刻双线垂如意蟠夔纹全器采用浮雕技法两面共凸刻大小行龙条大龙条小龙条火珠颗器物满布苍龙纹饰龙足边露出飞溅浪花纹盒两侧分刻楷书乾隆壬戌1742振效恭制款盖顶盒底长方形小孔一条苏绣明黄缎带穿带上饰雕成莲叶形珊瑚连珠坠缎带连接盒内软囊囊细米珍珠穿成寿字共用珠164粒软囊内盛镂空錾夔龙纹金火镰一把玛瑙火石数块火引一小叠火镰工精纹美小巧玲珑这种雕刻精细火镰套盒紫禁城内不多见此件龙纹火镰盒皇帝御用之物清宫造办制作留有制作者黄振效名款一件珍品'},
    #     {'name':u'1_苏醒的黑夜', 'text':u'苏醒黑夜旅游世界2015日刊杰马夫纳广场马拉喀什精神中心夜幕降临座精神中心越发变得魔幻起来人潮拥挤摩肩接踵人们伸长脖子往前眉上满汗珠广场内伊斯兰教宣礼员再度召唤信徒祷告每天五次千年不变最后一丝声音消失拉长阴影中后如雷般的喧闹声随即响起手推车广场四面八方奔来战车奔赴战场每辆手推车后面一堆铁桶支架钢烤架搁桌板震耳欲聋铁锤敲打声大家匆忙搭建几十个小吃摊千年不变形成对比不远处麦地那商铺传统手工艺品越来越充斥便宜运动鞋廉价足球衣移动电话房顶卫星天线马拉喀什住三个晚上如同居民每天晚上落后活动跟着全家人起来广场免费节目每晚如约而至整整齐齐排列小吃摊道每个摊位有人负责招揽生意喜欢哪家店食物记住号码明天离开小吃摊圈不远处一群群分别聚集人群中间说书人耍猴表演打拳击绕开一字排开煮蜗牛吃逛累爬视野最好餐厅露台挤满露台边缘等待位置坐下慢慢欣赏千姿百态夜间集市远处小吃摊烟慢慢升起恍惚来到千年之前苏醒黑夜旅游世界2015日刊杰马夫纳广场马拉喀什精神中心夜幕降临座精神中心越发变得魔幻起来人潮拥挤摩肩接踵人们伸长脖子往前眉上满汗珠广场内伊斯兰教宣礼员再度召唤信徒祷告每天五次千年不变最后一丝声音消失拉长阴影中后如雷般的喧闹声随即响起手推车广场四面八方奔来战车奔赴战场每辆手推车后面一堆铁桶支架钢烤架搁桌板震耳欲聋铁锤敲打声大家匆忙搭建几十个小吃摊千年不变形成对比不远处麦地那商铺传统手工艺品越来越充斥便宜运动鞋廉价足球衣移动电话房顶卫星天线马拉喀什住三个晚上如同居民每天晚上落后活动跟着全家人起来广场免费节目每晚如约而至整整齐齐排列小吃摊道每个摊位有人负责招揽生意喜欢哪家店食物记住号码明天离开小吃摊圈不远处一群群分别聚集人群中间说书人耍猴表演打拳击绕开一字排开煮蜗牛吃逛累爬视野最好餐厅露台挤满露台边缘等待位置坐下慢慢欣赏千姿百态夜间集市远处小吃摊烟慢慢升起恍惚来到千年之前苏醒黑夜旅游世界2015日刊杰马夫纳广场马拉喀什精神中心夜幕降临座精神中心越发变得魔幻起来人潮拥挤摩肩接踵人们伸长脖子往前眉上满汗珠广场内伊斯兰教宣礼员再度召唤信徒祷告每天五次千年不变最后一丝声音消失拉长阴影中后如雷般的喧闹声随即响起手推车广场四面八方奔来战车奔赴战场每辆手推车后面一堆铁桶支架钢烤架搁桌板震耳欲聋铁锤敲打声大家匆忙搭建几十个小吃摊千年不变形成对比不远处麦地那商铺传统手工艺品越来越充斥便宜运动鞋廉价足球衣移动电话房顶卫星天线马拉喀什住三个晚上如同居民每天晚上落后活动跟着全家人起来广场免费节目每晚如约而至整整齐齐排列小吃摊道每个摊位有人负责招揽生意喜欢哪家店食物记住号码明天离开小吃摊圈不远处一群群分别聚集人群中间说书人耍猴表演打拳击绕开一字排开煮蜗牛吃逛累爬视野最好餐厅露台挤满露台边缘等待位置坐下慢慢欣赏千姿百态夜间集市远处小吃摊烟慢慢升起恍惚来到千年之前苏醒黑夜旅游世界2015日刊杰马夫纳广场马拉喀什精神中心夜幕降临座精神中心越发变得魔幻起来人潮拥挤摩肩接踵人们伸长脖子往前眉上满汗珠广场内伊斯兰教宣礼员再度召唤信徒祷告每天五次千年不变最后一丝声音消失拉长阴影中后如雷般的喧闹声随即响起手推车广场四面八方奔来战车奔赴战场每辆手推车后面一堆铁桶支架钢烤架搁桌板震耳欲聋铁锤敲打声大家匆忙搭建几十个小吃摊千年不变形成对比不远处麦地那商铺传统手工艺品越来越充斥便宜运动鞋廉价足球衣移动电话房顶卫星天线马拉喀什住三个晚上如同居民每天晚上落后活动跟着全家人起来广场免费节目每晚如约而至整整齐齐排列小吃摊道每个摊位有人负责招揽生意喜欢哪家店食物记住号码明天离开小吃摊圈不远处一群群分别聚集人群中间说书人耍猴表演打拳击绕开一字排开煮蜗牛吃逛累爬视野最好餐厅露台挤满露台边缘等待位置坐下慢慢欣赏千姿百态夜间集市远处小吃摊烟慢慢升起恍惚来到千年之前'},
    #     # {'name':u'2_14天魔鬼训练，天使身材', 'text':u'魔鬼训练天使身材健康女性2015月刊反手摸肚脐腰腹上线锁骨搁硬币无敌长腿网络传播人际传播整个夏天生生女人心理崩溃节奏不要焦虑WH做好全盘准备急救计划让你在数据比较变得充满说服力据说现在社交网络流行带头拍最让人自豪照片永远炫腹一种比照坚持跑步练习平板三个之后看到腹部刚出现线条Instagram上有非常受欢迎修身教练乔伊维克斯Instagram发布研究设计修身计划型瘦Leanin15健康餐单分钟之内准备健康瘦身餐指导身体发生意想不到改变绝对滤镜美图真的诚意做出改变心愿迫切维克斯便是找男人WH出难题必须周之内看到效果型瘦分钟练习接下来天里只能休息足套修身训练每套训练之前分钟热身热身必须针对性膝盖原地慢走箭步蹲必须做好拉伸需要一副哑铃受力东西才能真正帮消耗脂肪打造美好肌肉线条还要高低合适椅子健身垫身体推向极限意味着感觉累累维克斯指出才能充分提高新陈代谢效率脂肪才得到燃烧第一天有氧训练第二天上半身训练第三天有氧训练第四天下半身训练第五天休息第六天有氧训练第七天休息第八天休息第九天上半身训练第十天有氧训练第十一天下半身训练第十二天休息第十三天全身训练第十四天全身训练有氧训练每个动作练习至少秒休息40秒循环至少重复1.交叉登山式时间秒目标核心肌肉三头肌股四头肌做好平板式俯卧撑体式身体一条直线提高右脚触碰肩收回右脚换边练习提速2.蛙腿时间秒目标全身初始动作俯卧撑双手分开稍稍超过肩宽右脚向前放在右手外侧看起来蓄势待发青蛙腿后撤不停转换左右两边进行练习3.抬膝运动时间秒目标腿髋部屈肌站双臂弯曲呈直角手肘紧贴身体两边手掌朝向地面加速原地跑每次尽量膝盖抬到最高手掌触碰到大腿膝盖4.摆臂运动时间秒目标手臂肩膀胸部身体保持直立弯曲双臂贴身体两侧最快速度向前摆动手臂身体一定保持静止不动看上去奇怪绝对帮甩掉拜拜肉5.跃身跳时间秒目标全身站蹲下双手身体前方摸地双腿跳形成平板式俯卧撑收回双脚空中用力跃起膝盖触碰到胸部上半身训练30秒次数尽可能身体姿势走形休息30秒重复至少可能觉得好像垮掉1.椅子三头肌下沉练习时间30秒目标三头肌肩膀背部坐在椅子慢慢滑椅子向前伸直双腿放在对面一把椅子上半身滑出椅子双手撑住椅面双脚双手支撑身体重量放低手臂形成直角反向俯卧撑重复拜拜拜拜肉2.半俯卧撑时间30秒目标手臂肩膀胸部核心肌肉背部手臂平板式双手放在身体正下方肩膀稍稍宽出一点点伸直身体放低身体地面慢慢贴近身体地面保持平行保持秒继续放低胸部好像刚刚要触碰到地面推回到平板式初始动作第二天知道厉害3.屈腕卷二头肌时间30秒目标二头肌双手举一只哑铃手掌朝向天花板内弯曲手腕上半部分手臂保持静止向上抬哑铃呼气吸气放低哑铃重复练习4.弯曲划桨时间30秒目标背部手臂双脚分开肩宽双手握一只哑铃微微弯曲双膝慢慢向上拉回哑铃过程双臂紧贴身体两侧收紧肩胛骨5.肩推哑铃时间30秒目标背部三头肌坐在椅子双腿收紧双手握住一只哑铃高举双臂肩膀高度手肘弯曲正好形成直角掌心向前放低重复练习下半身训练每个练习至少30秒休息30秒最后全套练习重复全新美美翘臀正在1.哑铃拱桥式时间30秒目标臀肌跟腱平躺地面弯曲膝盖一只哑铃放在骨盆抬高臀部身体形成一条直线来回重复动作抬高用力收紧臀部肌肉感受一股力量2.平行溜冰式时间30秒目标股肌跟腱双脚分开臀宽右脚向前左腿手臂甩漂亮注意套动作连贯性带爆发力特别转换左右两边3.快速箭步蹲时间30秒目标腿部臀肌站左脚向前左腿形成直角放下右膝几乎触碰到地面向上跳换边蹲下形成一个箭步蹲越快越好可别腿叠一块儿4.空中蛙跳时间30秒目标股肌臀肌快速站起身双脚分开肩宽半蹲挺直胸部背部充分利用腹肌力量向上跳身体旋转180度向下地时身体再次旋转原来位置5.相扑蹲时间30秒目标腿股肌臀部双脚分开肩宽约1.5倍脚趾打开双手抓住一只哑铃放在胸前蛙蹲脚跟保持挺直背部不断练习向下蹲加油全身训练OK最后冲刺阶段以下30秒练习30秒休息重复至少想要抬膝运动半俯卧撑跃身跳空中蛙跳交叉登山式完魔鬼训练天使身材健康女性2015月刊反手摸肚脐腰腹上线锁骨搁硬币无敌长腿网络传播人际传播整个夏天生生女人心理崩溃节奏不要焦虑WH做好全盘准备急救计划让你在数据比较变得充满说服力据说现在社交网络流行带头拍最让人自豪照片永远炫腹一种比照坚持跑步练习平板三个之后看到腹部刚出现线条Instagram上有非常受欢迎修身教练乔伊维克斯Instagram发布研究设计修身计划型瘦Leanin15健康餐单分钟之内准备健康瘦身餐指导身体发生意想不到改变绝对滤镜美图真的诚意做出改变心愿迫切维克斯便是找男人WH出难题必须周之内看到效果型瘦分钟练习接下来天里只能休息足套修身训练每套训练之前分钟热身热身必须针对性膝盖原地慢走箭步蹲必须做好拉伸需要一副哑铃受力东西才能真正帮消耗脂肪打造美好肌肉线条还要高低合适椅子健身垫身体推向极限意味着感觉累累维克斯指出才能充分提高新陈代谢效率脂肪才得到燃烧第一天有氧训练第二天上半身训练第三天有氧训练第四天下半身训练第五天休息第六天有氧训练第七天休息第八天休息第九天上半身训练第十天有氧训练第十一天下半身训练第十二天休息第十三天全身训练第十四天全身训练有氧训练每个动作练习至少秒休息40秒循环至少重复1.交叉登山式时间秒目标核心肌肉三头肌股四头肌做好平板式俯卧撑体式身体一条直线提高右脚触碰肩收回右脚换边练习提速2.蛙腿时间秒目标全身初始动作俯卧撑双手分开稍稍超过肩宽右脚向前放在右手外侧看起来蓄势待发青蛙腿后撤不停转换左右两边进行练习3.抬膝运动时间秒目标腿髋部屈肌站双臂弯曲呈直角手肘紧贴身体两边手掌朝向地面加速原地跑每次尽量膝盖抬到最高手掌触碰到大腿膝盖4.摆臂运动时间秒目标手臂肩膀胸部身体保持直立弯曲双臂贴身体两侧最快速度向前摆动手臂身体一定保持静止不动看上去奇怪绝对帮甩掉拜拜肉5.跃身跳时间秒目标全身站蹲下双手身体前方摸地双腿跳形成平板式俯卧撑收回双脚空中用力跃起膝盖触碰到胸部上半身训练30秒次数尽可能身体姿势走形休息30秒重复至少可能觉得好像垮掉1.椅子三头肌下沉练习时间30秒目标三头肌肩膀背部坐在椅子慢慢滑椅子向前伸直双腿放在对面一把椅子上半身滑出椅子双手撑住椅面双脚双手支撑身体重量放低手臂形成直角反向俯卧撑重复拜拜拜拜肉2.半俯卧撑时间30秒目标手臂肩膀胸部核心肌肉背部手臂平板式双手放在身体正下方肩膀稍稍宽出一点点伸直身体放低身体地面慢慢贴近身体地面保持平行保持秒继续放低胸部好像刚刚要触碰到地面推回到平板式初始动作第二天知道厉害3.屈腕卷二头肌时间30秒目标二头肌双手举一只哑铃手掌朝向天花板内弯曲手腕上半部分手臂保持静止向上抬哑铃呼气吸气放低哑铃重复练习4.弯曲划桨时间30秒目标背部手臂双脚分开肩宽双手握一只哑铃微微弯曲双膝慢慢向上拉回哑铃过程双臂紧贴身体两侧收紧肩胛骨5.肩推哑铃时间30秒目标背部三头肌坐在椅子双腿收紧双手握住一只哑铃高举双臂肩膀高度手肘弯曲正好形成直角掌心向前放低重复练习下半身训练每个练习至少30秒休息30秒最后全套练习重复全新美美翘臀正在1.哑铃拱桥式时间30秒目标臀肌跟腱平躺地面弯曲膝盖一只哑铃放在骨盆抬高臀部身体形成一条直线来回重复动作抬高用力收紧臀部肌肉感受一股力量2.平行溜冰式时间30秒目标股肌跟腱双脚分开臀宽右脚向前左腿手臂甩漂亮注意套动作连贯性带爆发力特别转换左右两边3.快速箭步蹲时间30秒目标腿部臀肌站左脚向前左腿形成直角放下右膝几乎触碰到地面向上跳换边蹲下形成一个箭步蹲越快越好可别腿叠一块儿4.空中蛙跳时间30秒目标股肌臀肌快速站起身双脚分开肩宽半蹲挺直胸部背部充分利用腹肌力量向上跳身体旋转180度向下地时身体再次旋转原来位置5.相扑蹲时间30秒目标腿股肌臀部双脚分开肩宽约1.5倍脚趾打开双手抓住一只哑铃放在胸前蛙蹲脚跟保持挺直背部不断练习向下蹲加油全身训练OK最后冲刺阶段以下30秒练习30秒休息重复至少想要抬膝运动半俯卧撑跃身跳空中蛙跳交叉登山式完魔鬼训练天使身材健康女性2015月刊反手摸肚脐腰腹上线锁骨搁硬币无敌长腿网络传播人际传播整个夏天生生女人心理崩溃节奏不要焦虑WH做好全盘准备急救计划让你在数据比较变得充满说服力据说现在社交网络流行带头拍最让人自豪照片永远炫腹一种比照坚持跑步练习平板三个之后看到腹部刚出现线条Instagram上有非常受欢迎修身教练乔伊维克斯Instagram发布研究设计修身计划型瘦Leanin15健康餐单分钟之内准备健康瘦身餐指导身体发生意想不到改变绝对滤镜美图真的诚意做出改变心愿迫切维克斯便是找男人WH出难题必须周之内看到效果型瘦分钟练习接下来天里只能休息足套修身训练每套训练之前分钟热身热身必须针对性膝盖原地慢走箭步蹲必须做好拉伸需要一副哑铃受力东西才能真正帮消耗脂肪打造美好肌肉线条还要高低合适椅子健身垫身体推向极限意味着感觉累累维克斯指出才能充分提高新陈代谢效率脂肪才得到燃烧第一天有氧训练第二天上半身训练第三天有氧训练第四天下半身训练第五天休息第六天有氧训练第七天休息第八天休息第九天上半身训练第十天有氧训练第十一天下半身训练第十二天休息第十三天全身训练第十四天全身训练有氧训练每个动作练习至少秒休息40秒循环至少重复1.交叉登山式时间秒目标核心肌肉三头肌股四头肌做好平板式俯卧撑体式身体一条直线提高右脚触碰肩收回右脚换边练习提速2.蛙腿时间秒目标全身初始动作俯卧撑双手分开稍稍超过肩宽右脚向前放在右手外侧看起来蓄势待发青蛙腿后撤不停转换左右两边进行练习3.抬膝运动时间秒目标腿髋部屈肌站双臂弯曲呈直角手肘紧贴身体两边手掌朝向地面加速原地跑每次尽量膝盖抬到最高手掌触碰到大腿膝盖4.摆臂运动时间秒目标手臂肩膀胸部身体保持直立弯曲双臂贴身体两侧最快速度向前摆动手臂身体一定保持静止不动看上去奇怪绝对帮甩掉拜拜肉5.跃身跳时间秒目标全身站蹲下双手身体前方摸地双腿跳形成平板式俯卧撑收回双脚空中用力跃起膝盖触碰到胸部上半身训练30秒次数尽可能身体姿势走形休息30秒重复至少可能觉得好像垮掉1.椅子三头肌下沉练习时间30秒目标三头肌肩膀背部坐在椅子慢慢滑椅子向前伸直双腿放在对面一把椅子上半身滑出椅子双手撑住椅面双脚双手支撑身体重量放低手臂形成直角反向俯卧撑重复拜拜拜拜肉2.半俯卧撑时间30秒目标手臂肩膀胸部核心肌肉背部手臂平板式双手放在身体正下方肩膀稍稍宽出一点点伸直身体放低身体地面慢慢贴近身体地面保持平行保持秒继续放低胸部好像刚刚要触碰到地面推回到平板式初始动作第二天知道厉害3.屈腕卷二头肌时间30秒目标二头肌双手举一只哑铃手掌朝向天花板内弯曲手腕上半部分手臂保持静止向上抬哑铃呼气吸气放低哑铃重复练习4.弯曲划桨时间30秒目标背部手臂双脚分开肩宽双手握一只哑铃微微弯曲双膝慢慢向上拉回哑铃过程双臂紧贴身体两侧收紧肩胛骨5.肩推哑铃时间30秒目标背部三头肌坐在椅子双腿收紧双手握住一只哑铃高举双臂肩膀高度手肘弯曲正好形成直角掌心向前放低重复练习下半身训练每个练习至少30秒休息30秒最后全套练习重复全新美美翘臀正在1.哑铃拱桥式时间30秒目标臀肌跟腱平躺地面弯曲膝盖一只哑铃放在骨盆抬高臀部身体形成一条直线来回重复动作抬高用力收紧臀部肌肉感受一股力量2.平行溜冰式时间30秒目标股肌跟腱双脚分开臀宽右脚向前左腿手臂甩漂亮注意套动作连贯性带爆发力特别转换左右两边3.快速箭步蹲时间30秒目标腿部臀肌站左脚向前左腿形成直角放下右膝几乎触碰到地面向上跳换边蹲下形成一个箭步蹲越快越好可别腿叠一块儿4.空中蛙跳时间30秒目标股肌臀肌快速站起身双脚分开肩宽半蹲挺直胸部背部充分利用腹肌力量向上跳身体旋转180度向下地时身体再次旋转原来位置5.相扑蹲时间30秒目标腿股肌臀部双脚分开肩宽约1.5倍脚趾打开双手抓住一只哑铃放在胸前蛙蹲脚跟保持挺直背部不断练习向下蹲加油全身训练OK最后冲刺阶段以下30秒练习30秒休息重复至少想要抬膝运动半俯卧撑跃身跳空中蛙跳交叉登山式完魔鬼训练天使身材健康女性2015月刊反手摸肚脐腰腹上线锁骨搁硬币无敌长腿网络传播人际传播整个夏天生生女人心理崩溃节奏不要焦虑WH做好全盘准备急救计划让你在数据比较变得充满说服力据说现在社交网络流行带头拍最让人自豪照片永远炫腹一种比照坚持跑步练习平板三个之后看到腹部刚出现线条Instagram上有非常受欢迎修身教练乔伊维克斯Instagram发布研究设计修身计划型瘦Leanin15健康餐单分钟之内准备健康瘦身餐指导身体发生意想不到改变绝对滤镜美图真的诚意做出改变心愿迫切维克斯便是找男人WH出难题必须周之内看到效果型瘦分钟练习接下来天里只能休息足套修身训练每套训练之前分钟热身热身必须针对性膝盖原地慢走箭步蹲必须做好拉伸需要一副哑铃受力东西才能真正帮消耗脂肪打造美好肌肉线条还要高低合适椅子健身垫身体推向极限意味着感觉累累维克斯指出才能充分提高新陈代谢效率脂肪才得到燃烧第一天有氧训练第二天上半身训练第三天有氧训练第四天下半身训练第五天休息第六天有氧训练第七天休息第八天休息第九天上半身训练第十天有氧训练第十一天下半身训练第十二天休息第十三天全身训练第十四天全身训练有氧训练每个动作练习至少秒休息40秒循环至少重复1.交叉登山式时间秒目标核心肌肉三头肌股四头肌做好平板式俯卧撑体式身体一条直线提高右脚触碰肩收回右脚换边练习提速2.蛙腿时间秒目标全身初始动作俯卧撑双手分开稍稍超过肩宽右脚向前放在右手外侧看起来蓄势待发青蛙腿后撤不停转换左右两边进行练习3.抬膝运动时间秒目标腿髋部屈肌站双臂弯曲呈直角手肘紧贴身体两边手掌朝向地面加速原地跑每次尽量膝盖抬到最高手掌触碰到大腿膝盖4.摆臂运动时间秒目标手臂肩膀胸部身体保持直立弯曲双臂贴身体两侧最快速度向前摆动手臂身体一定保持静止不动看上去奇怪绝对帮甩掉拜拜肉5.跃身跳时间秒目标全身站蹲下双手身体前方摸地双腿跳形成平板式俯卧撑收回双脚空中用力跃起膝盖触碰到胸部上半身训练30秒次数尽可能身体姿势走形休息30秒重复至少可能觉得好像垮掉1.椅子三头肌下沉练习时间30秒目标三头肌肩膀背部坐在椅子慢慢滑椅子向前伸直双腿放在对面一把椅子上半身滑出椅子双手撑住椅面双脚双手支撑身体重量放低手臂形成直角反向俯卧撑重复拜拜拜拜肉2.半俯卧撑时间30秒目标手臂肩膀胸部核心肌肉背部手臂平板式双手放在身体正下方肩膀稍稍宽出一点点伸直身体放低身体地面慢慢贴近身体地面保持平行保持秒继续放低胸部好像刚刚要触碰到地面推回到平板式初始动作第二天知道厉害3.屈腕卷二头肌时间30秒目标二头肌双手举一只哑铃手掌朝向天花板内弯曲手腕上半部分手臂保持静止向上抬哑铃呼气吸气放低哑铃重复练习4.弯曲划桨时间30秒目标背部手臂双脚分开肩宽双手握一只哑铃微微弯曲双膝慢慢向上拉回哑铃过程双臂紧贴身体两侧收紧肩胛骨5.肩推哑铃时间30秒目标背部三头肌坐在椅子双腿收紧双手握住一只哑铃高举双臂肩膀高度手肘弯曲正好形成直角掌心向前放低重复练习下半身训练每个练习至少30秒休息30秒最后全套练习重复全新美美翘臀正在1.哑铃拱桥式时间30秒目标臀肌跟腱平躺地面弯曲膝盖一只哑铃放在骨盆抬高臀部身体形成一条直线来回重复动作抬高用力收紧臀部肌肉感受一股力量2.平行溜冰式时间30秒目标股肌跟腱双脚分开臀宽右脚向前左腿手臂甩漂亮注意套动作连贯性带爆发力特别转换左右两边3.快速箭步蹲时间30秒目标腿部臀肌站左脚向前左腿形成直角放下右膝几乎触碰到地面向上跳换边蹲下形成一个箭步蹲越快越好可别腿叠一块儿4.空中蛙跳时间30秒目标股肌臀肌快速站起身双脚分开肩宽半蹲挺直胸部背部充分利用腹肌力量向上跳身体旋转180度向下地时身体再次旋转原来位置5.相扑蹲时间30秒目标腿股肌臀部双脚分开肩宽约1.5倍脚趾打开双手抓住一只哑铃放在胸前蛙蹲脚跟保持挺直背部不断练习向下蹲加油全身训练OK最后冲刺阶段以下30秒练习30秒休息重复至少想要抬膝运动半俯卧撑跃身跳空中蛙跳交叉登山式完'},
    #     # {'name':u'3_不能写入一', 'text':u'<p>“ 这些照片拍摄于1925年，看到这些照片后,希特勒要求霍夫曼毁掉底片，但他没有照做。而是发表在他的回忆录“希特勒是我的朋友”中，1955年出版。</p><p>1925年希特勒在镜子前练习演讲,</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width9238f74daf98ae5e07e71ca6c0a546d448da63dc.jpg\"></span></p><p>希特勒的演讲不单单只是抓住了人民的心底最可怕的好战情绪和第一次战败的耻辱。更关键的是。在他演讲的时候。你完全不会觉得他是在有意的让你去做某些事情。</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width058a206e9d52ef5580b9fa9d2ca34b7bf4eb7e29.jpg\"></span></p><p>希特勒的某些细节把握的非常好。他知道听众要听什么。</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width990ceb2ee4bc0e269966acca5655337d35e350f4.jpg\"></span></p><p>希特勒的演讲像是一个歌手在开演唱会，他能细腻的表达和抓住观众的心情，从而制造出 最大的 欢呼声。在不知不觉中 民众就会 陷入 狂热状态。失去理智，从而坚定信念。</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width30afbd98af5082d906f6fce5a694e31e58810e8a.jpg\"></span></p><p>希特勒所演讲的内容。和他内心高度统一。所以他是在释放他狂热的思想。完全不会显得做作。所以大家找不出他的虚假。更真实更狂热。</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width897f307f8d7cf78353ea59cee43f4e7749d50bb2.jpg\"></span></p><p>宣传最好的办法就是在对方还未察觉你的动态时直接灌输与他们你的思想。希特勒就是这样。</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width98022df90102c66c84d961754aed69a43fdbdc7a.jpg\"></span></p><p>真实可信。狂热民族主义。都是他的演讲成功的重要手段。从而成为他掌握国家走向的正治手段。</p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width43e17deda875f50fdef1713292315ed0b043f506.jpg\"></span></p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width1bf20e753c9726299cc0cb06f850894296e23c25.jpg\"></span></p><p><span class=\"imgspan\"><img  src=\"http://img.contx.cn/article/2016-01-11/1001798/$content_width1735c6f9af92af90d2f331825f442d24ded13d13.jpg\"></span></p>","name":"3546083768298267441_图志丨1925年希特勒在镜子前练习演讲的照片曝光'}
    # ]
    # num_added = 100
    files = os.listdir(news_post_add)
    num_files = len(files)
    result = []
    print("%s files in \"news_added\"." % num_files)
    for i in range(num_files):
        file_name = files[i]
        t_fp = open(news_post_add + file_name, 'rb')
        text = t_fp.read()
        t_fp.close()
        result.append({'name': file_name.decode('utf-8'), 'text': text.decode('utf-8')})

    shutil.rmtree(news_post_add)

    sim_update(result)
