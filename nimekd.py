import os
import requests
import time
import aiohttp
import asyncio
from tabulate import tabulate
from tqdm import tqdm
from bs4 import BeautifulSoup
loop = asyncio.get_event_loop()
session = requests.Session()
session_headers = {'User-Agent': 'Mozilla/5.0'}

# Bisma Mods
# Simple Anime Downloader

def string_short(str, max):
    if (max >= len(str)):
        return str

    str2 = ''
    for n in range(max):
        str2 += str[n]
    str2 += '...'

    return str2

def string_leftTrim(str, max, inden):
    str = str.split(inden)
    str2 = ""

    for n in range(max):
        str2 += str[n]
        if (n != max):
            str2 += inden

    return str2

def string_rightTrim(str, skip, inden):
    str = str.split(inden)
    lenn = len(str)
    str2 = ""

    for n in range(skip):
        str2 += str[(lenn - skip) + n]
        if (n != skip):
            str2 += inden

    return str2

def endpoint_parse(data):
    try:
        name = data.split("/")[3]
    except:
        name = data
    return f"https://otakudesu-anime-api.vercel.app/api/v1/detail/{name}"

# Asynchronous http request
class reqasync:
    quene_task = []
    def clear():
        reqasync.quene_task.clear()

    def get(url, datatype, payload, callb, param):
        task = loop.create_task(reqasync.execute_send(
            {"url": url, "mode": "get", "datatype": datatype, "payload": payload, "callb": callb, "param": param}
        ))

        reqasync.quene_task.append(task)
    def post(url, datatype, payload, callb, param):
        task = loop.create_task(reqasync.execute_send(
            {"url": url, "mode": "post", "datatype": datatype, "payload": payload, "callb": callb, "param": param}
        ))

        reqasync.quene_task.append(task)

    async def execute_send(data):
        async with aiohttp.ClientSession(headers=session_headers) as aiosession:
            url = data['url']
            callb = data['callb']
            param = data['param']
            mode = data['mode']
            datatype = data['datatype']
            session_payload = data['payload']
            
            if (mode == 'post'):
                if (session_payload != None):
                    ress = await aiosession.post(url, data=session_payload)
                else:
                    ress = await aiosession.post(url)

                if (datatype == "json"):
                    ress = await ress.json()

                callb(ress, param)
            
            elif (mode == 'get'):
                if (session_payload != None):
                    ress = await aiosession.get(url, data=session_payload)
                else:
                    ress = await aiosession.get(url)

                if (datatype == "json"):
                    ress = await ress.json()
                
                callb(ress, param)
                    
    def execute_waiting():
        async def task_start():
            return await asyncio.wait(reqasync.quene_task)
        
        loop.run_until_complete(task_start())
        loop.close()
        reqasync.clear()

# Redirect for Instant Download via downloaddesu
def downloaddesu_parse(url):
    try:
        data = []
        docc = session.get(url, headers=session_headers)
        docc = BeautifulSoup(docc.text, "html.parser")
        docc = docc.find("div", {"class": "download"}).find_next('ul')

        for ldoc in docc:
            ldoc = ldoc.find_next('li')
            judul = ldoc.find_next('strong')
            if (judul != None):
                judul = judul.get_text()
                link = ldoc.find_next('a').get('href')
                anime = string_rightTrim(url, 1, "/").replace("-", "_").replace("/", "")

                data.append({'judul': judul, 'url': link, 'anime': anime})

        return data
    except:
        return []

def downloaddesu_savefile(url, filepath):
    # Get url redirecting
    docc = session.get(url, headers=session_headers)
    docc = BeautifulSoup(docc.text, "html.parser")
    url = docc.find("textarea", {"readonly": ""}).text
    if (url == None):
        print("Gagal mendapatkan Redirect")
        return ""

    # Get Token
    docc = session.get(url, headers=session_headers)
    docc = BeautifulSoup(docc.text, "html.parser")
    docc = docc.find("form", {"name": "F1"})
    payld_op = docc.find("input", {"name": "op"}).get("value")
    payld_id = docc.find("input", {"name": "id"}).get("value")
    if (payld_op == None or payld_id == None):
        print("Gagal Membuat Token Download")
        return ""

    session_payload = {
        "op": payld_op,
        "id": payld_id,
        "rand": "",
        "referer": "",
        "method_free": "",
        "method_premium": ""
    }
    
    # File Download
    with open(filepath, "wb") as f:
        docc = session.post(url, headers=session_headers, data=session_payload, stream=True)
        length = docc.headers.get('content-length')
        pos = 0

        if (length != None):
            length = int(length)
            download_bar = tqdm(total=length, unit="iB", unit_scale=True, leave=False)
            for chunk in docc.iter_content(chunk_size=4096):
                nsize = len(chunk)
                f.write(chunk)
                download_bar.update(nsize)
                pos += nsize
        else:
            download_bar = tqdm(total=100, unit="%", leave=False)
            download_bar.update(30)
            f.write(docc.content)

        download_bar.clear()
        if (pos != length):
            return ""
        
        return filepath

# First Run
def main():
    start_time = time.time()

    # Api Anime List
    try:
        apires = session.get("https://otakudesu-anime-api.vercel.app/api/v1/completed/1", headers=session_headers)
        json_nimek = apires.json()
    except:
        json_nimek = {'status': False}

    if (json_nimek['status'] != True):
        print("Anime gagal di lihat")
        exit()
    
    # Data Nanti
    json_nimek = json_nimek['completed']
    jumlah = len(json_nimek)
    data_animek = []
    data_download = [None] * jumlah
    loading_bar = tqdm(total=25, unit="%", desc="Loading...", ncols=50, leave=False)
    
    # Pilihan Anime
    for no in range(jumlah):
        judul = json_nimek[no]['title']
        tanggal = json_nimek[no]['updated_on']
        endpoint = endpoint_parse(json_nimek[no]['endpoint'])
        
        def deskripsi_get(data, param):
            no = param['nomor']
            # sinopsis
            sinopsis = data['anime_detail']['sinopsis']
            sinopsis = "".join(sinopsis)
            data_animek[no][2] = string_short(sinopsis, 30)

            # link download
            data_download[no] = data['episode_list']
            loading_bar.update(1)
            return

        data_animek.append([
            f"{no + 1}. {string_short(judul, 16)}",
            tanggal,
            "..."
        ])

        reqasync.get(endpoint, "json", None, deskripsi_get, {'nomor': no})

    reqasync.execute_waiting()
    loading_bar.close()

    # Display Anime
    table_head = ["judul", "tanggal", "deskripsi"]
    print(tabulate(data_animek, headers=table_head))
    print("")

    pilih = int(input("Pilih Anime yg mau di download? ")) - 1
    print("\n")
    #print("Waiting Program", (time.time() - start_time))

    # Pilihan Episode
    list_episode = []
    table_episode = []
    no = 0
    for data in data_download[pilih]:
        judul = data['episode_title']
        judul = string_short(judul, 60)
        endpoint = data['episode_endpoint']

        if (endpoint.find("episode") != -1):
            table_episode.append([f"{no + 1}. {judul}"])
            list_episode.append(endpoint)
            no += 1
    
    # Display Episode
    table_head = ["judul"]
    print(tabulate(table_episode, headers=table_head))
    print("")

    pilih = int(input("Pilih Episode yg mau di download? ")) - 1
    urldownload = list_episode[pilih]
    print(urldownload)
    urldownload = f"https://otakudesu.lol/episode/{urldownload}"
    print("\n")

    # Pilihan Resolusi
    table_download = []
    list_download = downloaddesu_parse(urldownload)
    for no in range(len(list_download)):
        table_download.append([f"{no + 1}. {list_download[no]['judul']}"])

    # Display Resolusi
    table_head = ["download list"]
    print(tabulate(table_download, headers=table_head))
    print("")

    pilih = int(input("Pilih file? ")) - 1

    if (os.path.exists("download") == False):
        os.mkdir("download")
    downloaddesu_savefile(list_download[pilih]['url'], f"download\{list_download[pilih]['anime']}.mp4")

if __name__ == '__main__':
   main()