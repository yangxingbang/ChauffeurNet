import requests # requests是一个请求http网页的库，用python写的
import os

def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"

    # 初始化一个网页请求任务的对象
    session = requests.Session()

    # 返回请求网页后的对象
    response = session.get(URL, params = { 'id' : id }, stream = True)
    # 判断下载过程中有没有用户名和密码等需要确认的东西
    token = get_confirm_token(response)

    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)
    # 把从网页请求的结果存在目的地文件夹中
    save_response_content(response, destination)

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    # None是python中的一个特殊的常量，表示一个空的对象。
    # 数据为空并不代表是空对象，例如空列表:[],等都不是None。
    # None有自己的数据类型NoneType，你可以将None赋值给任意对象，但是不能创建一个NoneType对象。
    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

def check_if_data_exists():
    # 不能下载
    #https://drive.google.com/open?id=1KUaeIqIQh8ECjNdIFieVa6MW7DYgVrwg
    required_files = [['1yHerqUo9OK-cLjB5lIQ5sb_ZY-j3aC8s',  'data/world.obj'],
                      ['1pGVNEXhKUkBHpdS2ZpDN-LeSjwLfxXmJ', 'data/recorded_states.pkl'],
                      ['1Wwpa9vaB3XtSaI9b4CPP06u06Gr7mxzI', 'data/ChauffeurNet.pt']]
    # 如果不存在data文件夹，创建它
    if not os.path.exists("data"):
        os.mkdir("data")
    # 下载素材
    for pair in required_files:
        # 虽不能下载到有效数据，但是下载id和文件路径文件名是存在的，所以这里不会进入if，也就不会再下载数据了
        if not os.path.exists(pair[1]):
            print ("downloading file from drive", pair[1])
            download_file_from_google_drive(pair[0], pair[1])
