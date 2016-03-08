# -*- coding:utf-8 -*-
import logging
import json
import os
from flask import Flask, request, abort,g,current_app

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

app = Flask(__name__)
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
        fp.write(i['text'].encode('utf-8'))
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
    import cPickle
    # try:
    #     file_a = file_in.decode('gbk')
    # except Exception as e:
    file_a = file_in.decode('utf-8')

    try:
        fp = open("./prefix_map/filename_map.pkl", 'rb')
        files = cPickle.load(fp)
        fp.close()
    except Exception as e:
        files = {}

    if files.has_key(file_a):
        print("From dict %s" % file_a)
        return files[file_a]
    else:
        print("From news %s" % file_in)
        return file_in

if __name__ == '__main__':
    with app.app_context():
        print current_app.name
    app.run(debug=False, host='0.0.0.0', port=3000)
