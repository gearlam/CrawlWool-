import threading
import time

import pandas as pd
import requests
import re
from threading import Thread, Lock

# import  urllib.request as request
# req=urllib.request.Request(rawUrl)
# res = urllib.request.urlopen(req)
# html = res.read().decode('GB2312')

from requests.adapters import HTTPAdapter

# 284
# 337
# 超时重试
s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=3))
s.mount('https://', HTTPAdapter(max_retries=3))

rawUrl = r'https://www.xd0.com'
aspUrl = r'/ajax/wz.ajax.asp?menu=fy&?menu=fy&page='

MaxPageNum = 560

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/51.0.2704.63 Safari/537.36'}

df = pd.DataFrame(columns=['文章标题', '百度云盘地址', '内容描述图片地址', '分类','文章地址'])

semaphore = threading.Semaphore(0)

def climbPage(list):

            for num in range(0,MaxPageNum):
                try:
                    url = rawUrl + aspUrl + str(num)
                    # print(url + "请求中")
                    html = requests.get(url, timeout=10, headers=headers).text
                    print("第"+str(num+1)+"页数据请求成功，正在解析")

                    pattern = re.compile("<a href=\"/(.*?)\"")
                    list += re.findall(pattern, html)
                    # print("挂起")
                    semaphore.acquire()
                except requests.exceptions.RequestException as e:
                    print(e)
            df.to_excel('D:\\小刀网所有数据.xls', encoding='utf-8', index=False, header=True)


def handleHtml(url,html):
    # 挖百度云地址

    panPWPattern = re.compile(">(https://pan.baidu.com.+?)&nbsp")

    # 和上面的带密码的重复 老资源舍弃
    # panOldBtnNPWPattern=re.compile("href=\"(https://pan.baidu.com.+?)\"")
    panNewBtnNPWPattern = re.compile("window.open\('(https://pan.baidu.com.+?)'")
    panUrlList = re.findall(panPWPattern, html)
    # panUrlList+=re.findall(panOldBtnNPWPattern,html)
    panUrlList += re.findall(panNewBtnNPWPattern, html)
    panUrlList = list(map(lambda item: re.sub(r"</a>", " ", item), panUrlList))

    if len(panUrlList)==0:
        # 挖标题
        # titleUrlPattern = re.compile("<h2 class=\"post-title\">(.+?)</h2>")
        # titleList = re.findall(titleUrlPattern, html)
        # if len(titleList)!=0:
        #     title=titleList[0]
        # else:
        #     title="无标题"
        # print("网页标题："+title+" 地址："+url+" 没有资源")
        return
    # 挖图片
    newImgPattern = re.compile("<a class=\"pics\" href=\"(.+?)\"")
    oldImgPattern = re.compile("<P align=center><IMG border=0 src=\"(.+?.jpg)\"></P>")
    imgUrlList = re.findall(newImgPattern, html)
    imgUrlList += re.findall(oldImgPattern, html)

    # 挖标题
    titleUrlPattern = re.compile("<h2 class=\"post-title\">(.+?)</h2>")
    titleList = re.findall(titleUrlPattern, html)

    # 挖分类
    categoryPattern = re.compile("rel=\"category tag\">(.*?)</a>")
    categoryList = re.findall(categoryPattern, html)

    panUrlStr=''
    imgUrlStr=''
    titleStr=''
    categoryStr=''
    for index  in range(0,len(panUrlList)):
        panUrlStr+=panUrlList[index]+'\r'

    for index in range(0, len(imgUrlList)):
        imgUrlStr += imgUrlList[index] + '\r'

    for index in range(0, len(titleList)):
        titleStr += titleList[index] + '\r'

    for index in range(0, len(categoryList)):
        categoryStr += categoryList[index] + '\r'

    rowList=[]
    rowList.append(titleList[0])
    rowList.append(panUrlStr)
    rowList.append(rawUrl+'/'+imgUrlStr)
    rowList.append(categoryStr)
    rowList.append(url)
    row=df.shape[0]+1
    df.loc[row]=rowList
    # print(row)
    # if row %100==0:
    # filename=time.strftime('%Y_%m_%d_%H_%M_%S',time.localtime(time.time()))
    # while row !=1:
    #     df.drop(row-1)


def climbSrc(list):
        time.sleep(5)
        while True:
            try:
                if len(list)==0:
                    continue
                for indexUrl in list:
                    url=rawUrl +'/'+ indexUrl
                    html = requests.get(url, timeout=10, headers=headers).text
                    # print("请求成功")

                    handleHtml(url,html)

                list.clear()
                # print("释放")
                print("数据解析完成")
                semaphore.release()
                df.to_excel('D:\\小刀网当前数据.xls', encoding='utf-8', index=False, header=True)
            except requests.exceptions.RequestException as e:
                print(e)


if __name__ == '__main__':
    articleUrlList=[]
    # cond = threading.Condition()
    # threading.Thread(target=climbPage, args=(articleUrlList,cond)).start()
    # threading.Thread(target=climbSrc, args=(articleUrlList,cond)).start()
    climbPageThread=Thread(target=climbPage,args=(articleUrlList))
    climbSrcThread=Thread(target=climbSrc,args=(articleUrlList))
    climbSrcThread.start()
    climbPageThread.start()
    climbPageThread.join()
    climbSrcThread.join()
    print("OK")