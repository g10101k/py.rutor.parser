#coding=utf-8
import requests
import sqlite3
import time
import random
import sys
import argparse
 
from lxml import html
from datetime import datetime


site = 'http://live-rutor.org'
postfix = '/browse/%s/0/0/0/'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'}

def createParser ():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-e', '--end', default=10, type=int)
    parser.add_argument ('-s', '--start', default=0, type=int)
    parser.add_argument ('-u', '--url', default='') 
    return parser


def HTMLencode(str):
    arr = [('&#1040;', 'А'), ('&#1041;', 'Б'), ('&#1042;', 'В'), ('&#1043;', 'Г'),('&#1044;', 'Д'),('&#1045;', 'Е'),('&#1046;', 'Ж'),('&#1047;', 'З'),('&#1048;', 'И'),('&#1049;', 'Й'),('&#1050;', 'К'),('&#1051;', 'Л'),('&#1052;', 'М'),('&#1053;', 'Н'),('&#1054;', 'О'),('&#1055;', 'П'),('&#1056;', 'Р'),('&#1057;', 'С'),('&#1058;', 'Т'),('&#1059;', 'У'),('&#1060;', 'Ф'),('&#1061;', 'Х'),('&#1062;', 'Ц'),('&#1063;', 'Ч'),('&#1064;', 'Ш'),('&#1065;', 'Щ'),('&#1066;', 'Ъ'),('&#1067;', 'Ы'),('&#1068;', 'Ь'),('&#1069;', 'Э'),('&#1070;', 'Ю'),('&#1071;', 'Я'),('&#1072;', 'а'),('&#1073;', 'б'),('&#1074;', 'в'),('&#1075;', 'г'),('&#1076;', 'д'),('&#1077;', 'е'),('&#1078;', 'ж'),('&#1079;', 'з'),('&#1080;', 'и'),('&#1081;', 'й'),('&#1082;', 'к'),('&#1083;', 'л'),('&#1084;', 'м'),('&#1085;', 'н'),('&#1086;', 'о'),('&#1087;', 'п'),('&#1088;', 'р'),('&#1089;', 'с'),('&#1090;', 'т'),('&#1091;', 'у'),('&#1092;', 'ф'),('&#1093;', 'х'),('&#1094;', 'ц'),('&#1095;', 'ч'),('&#1096;', 'ш'),('&#1097;', 'щ'),('&#1098;', 'ъ'),('&#1099;', 'ы'),('&#1100;', 'ь'),('&#1101;', 'э'),('&#1102;', 'ю'),('&#1103;', 'я'),('&#1105;', 'ё')]
    for k, v in arr:
        buf = str.replace(k, v)
    return buf

def get_content(url):        
    return requests.get(url, headers = headers).content

def stringify_children(node):
    from lxml.etree import tostring
    from itertools import chain
    parts = ([node.text] +
            list(chain(*([c.text, tostring(c), c.tail] for c in node.getchildren()))) +
            [node.tail])
    # filter removes possible Nones in texts and tails
    return ''.join(filter(None, parts))

def parse_film(link):
    try:
        rutor_ar = link.split('/')
        rutor_id = rutor_ar[len(rutor_ar)-2] 
        link_page = site + "/torrent/" + rutor_id + "/"
        cnt = get_content(link_page)
        tree = html.fromstring(cnt)
        
        h1 = tree.xpath("//h1")[0].text.encode('utf-8','ignore')
        #TODO: Проверка на 404
                 
        div_download = tree.xpath("//div[@id='download']")[0]
        try: magnet_link = div_download.xpath("//div[@id='download']/a/@href")[0]
        except: magnet_link = "null"
        try:    
            torrent_link = div_download.xpath("//div[@id='download']/a/@href")[1]
            torrent_link = site + torrent_link
        except: torrent_link = "null"
         
        table_detail = html.fromstring(html.tostring(div_download.xpath("//table[@id='details']")[0]))
        
        td = table_detail.xpath("//td")[1]
        td_text = html.tostring(td)
        td_el = html.fromstring(td_text)
        try:
            links = td_el.xpath("//a")
            kp = ""
            kp_text = ""
            kp_site = ""
            kp_vote = ""
            imbb = ""
            imbb_vote = ""
            for l in links:
                link_text = html.tostring(l)

                if "www.kinopoisk.ru" in link_text: 
                    link_el = html.fromstring(link_text)
                    kp_text = link_el.xpath("//a/@href")[0]
                    kp_link = kp_text.split('/')
                    kp_link = kp_link[len(kp_link)-2] 
                    kp_site = 'https://rating.kinopoisk.ru/%s.xml' % kp_link   
                    content = get_content(kp_site);
                    tree = html.fromstring(content)
                    try: kp = tree.xpath('//kp_rating')[0].text
                    except Exception: kp = "" 
                    try: kp_vote = tree.xpath('//kp_rating/@num_vote')[0]
                    except Exception: kp_vote = "" 
                    try: imbb = tree.xpath('//imdb_rating')[0].text
                    except Exception: imbb = ""  
                    try: imbb_vote = tree.xpath('//imdb_rating/@num_vote')[0]
                    except Exception: imbb_vote = ''
                    break
                
        except: print datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S"), "[ERROR]: ", link_page, sys.exc_info()[0]
        buf = html.tostring(table_detail).replace('<br>', '\n').replace('<tr>', '\n')
        desc = html.fromstring(buf).text_content().replace('\'', '\\\'').replace('\"', '').encode('utf-8','ignore')
        h1 = h1.replace('\'', '\\\'').replace('\"', '')
        sql_insert = 'INSERT OR REPLACE INTO movie VALUES ({0}, "{1}", "{2}", "{3}", "{4}", "{5}", "{6}", "{7}", "{8}", "{9}")'.format(rutor_id,  h1 + " [{0}]".format(kp), desc,  magnet_link,  torrent_link,  kp_text,  kp,  kp_vote,  imbb,  imbb_vote)
        cur.execute(sql_insert)
        conn.commit()
    except :
        print datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S"), "[INFO ]: TRY WITHOUT DESC", link_page, sys.exc_info()[0] 
        try:
            sql_insert = 'INSERT OR REPLACE INTO movie VALUES ({0}, "{1}", "{2}", "{3}", "{4}", "{5}", "{6}", "{7}", "{8}", "{9}")'.format(rutor_id,  h1 + " [{0}]".format(kp), "",  magnet_link,  torrent_link,  kp_text,  kp,  kp_vote,  imbb,  imbb_vote)
            cur.execute(sql_insert)
            conn.commit()
        except:  
            print datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S"), "[ERROR]: ", link_page, h1, sys.exc_info()[0] 
            f = open("error.txt", 'a')
            f.write(link_page + "\n")
            f.close()
        return None
    
def parse_list_page(cnt):
    list_page = html.fromstring(cnt, None, parser=html.HTMLParser(encoding='utf-8'))
    div_e = list_page.xpath("//div[@id='index']")[0] # get first ul element
    div_text = html.tostring(div_e)  # get text ul element
    div_tree = html.fromstring(div_text)  
    tr_list = div_tree.xpath('//tr')
    for item in tr_list:
        item_e = html.fromstring(html.tostring(item))
        a = item_e.xpath("//a/@href")        
        if len(a) > 1:
            splited = a[1]
            last = site + splited
            parse_film(last)
    return None  
  
try:
  
    # Получаем параметры запуска
    if __name__ == '__main__':
        parser = createParser()
        namespace = parser.parse_args(sys.argv[1:])
    # Подключаемся к бд
    conn = sqlite3.connect('db.sqlite')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS movie (movieid INTEGER PRIMARY KEY, name TEXT, desc TEXT, magnet TEXT, torrent TEXT, kp_link TEXT, kp TEXT, kp_vote TEXT, imbb text, imbb_vote TEXT);')
     
    if namespace.url == '':
        i = namespace.start
        while i <= namespace.end:
            url = site + postfix % i
            print datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S"), "[INFO ]:", url
            cnt = get_content(url)
            link = parse_list_page(cnt) 
            conn.commit()
            #time.sleep(random.randint(1, 3))
            i = i + 1
    else:
        parse_film(namespace.url)        

finally: 
    conn.close() 
    print datetime.strftime(datetime.now(), "%Y.%m.%d %H:%M:%S"), "[INFO ]: Was fulfilled"





