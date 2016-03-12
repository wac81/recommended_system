# -*- coding:utf-8 -*-
import logging
import json
import os
from flask import Flask, request, abort,g,current_app

#logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

app = Flask(__name__)
@app.route('/getfiles/<input_text>',methods=['GET', 'POST'])
def getfiles(input_text):
    files=object
    if request.method == 'POST':
        files = request.form['files']
        # name = request.form['name']
    else:
        try:
            files = input_text  # 获取GET参数，没有参数就赋值 0
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

if __name__ == '__main__':
    with app.app_context():
        print current_app.name
    app.run(debug=False, host='0.0.0.0', port=3100)
