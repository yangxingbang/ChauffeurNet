import requests
import os

def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params = { 'id' : id }, stream = True)
    token = get_confirm_token(response)

    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)

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
    # 创建data文件夹
    if not os.path.exists("data"):
        os.mkdir("data")
    # 下载素材
    for pair in required_files:
        # 虽不能下载到有效数据，但是下载id和文件路径文件名是存在的，所以这里不会进入if
        if not os.path.exists(pair[1]):
            print ("downloading file from drive", pair[1])
            download_file_from_google_drive(pair[0], pair[1])
