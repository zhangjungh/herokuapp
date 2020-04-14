# -*- coding: UTF-8 -*-
import web
import base64
import requests
from bs4 import BeautifulSoup
import json
import logging
from whitenoise import WhiteNoise
import mathgen
import model

# parse url functions
def parse_url(url):
    if 'jsmlny.' in url:
        return parse_url_json(url)
    else:
        return parse_url_lazy(url)

def parse_url_lazy(url):
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 9; motorola one power) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Mobile Safari/537.36"}
    r = requests.get(url, headers=headers)
    logger.info(url + ' status_code: ' +  str(r.status_code))
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, features='lxml')
        title = soup.head.title.text
        images = [i.get('data-original') for i in soup.find_all('img', class_='lazy')]
        #    print(i.get('data-original'))

        pre = url.split('/chapter')[0]
        links = []
        def get_link(s, n, pre, a):
            g = s.find_all('a', text=n)
            #print(g)
            if g:
                h = g[0].get('href')
                if h:
                    b = '/?data=' + base64.b64encode((pre+h).encode('ascii')).decode('ascii')
                    a.append((b, n))

        get_link(soup, '上一章', pre, links)
        get_link(soup, '上一页', pre, links)
        get_link(soup, '下一页', pre, links)
        get_link(soup, '下一章', pre, links)
        return (title, images, links)
    else:
        return ()

def parse_url_json(url):
    ru = 'https://comiccdnhw.jsmlny.top/hcomic/chaptercontent?chapterId='
    title = url.split('chapterId=')[1]
    url = ru + title
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 9; motorola one power) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Mobile Safari/537.36"}
    r = requests.get(url, headers=headers)
    logger.info(url + ' status_code: ' +  str(r.status_code))
    if r.status_code == 200:
        j = json.loads(r.text)
        #title = 'title'
        images = [i['content'] for i in j['data']['chapterContentList']]

        #pre = url.split('/chapter')[0]
        links = []
        def get_link(n, pre, a):
            b = '/?data=' + base64.b64encode(pre.encode('ascii')).decode('ascii')
            a.append((b, n))

        get_link('上一章', ru+str(int(title)-1), links)
        get_link('下一章', ru+str(int(title)+1), links)
        return (title, images, links)
    else:
        return ()


render = web.template.render('templates/')

urls = (
    '/', 'index',
    '/math', 'mymath',
    '/favicon.ico', 'icon')

app = web.application(urls, globals()).wsgifunc()
app = WhiteNoise(app, root='static/', prefix='static/')

logger = logging.getLogger('gunicorn.error')

# process all requests here except specified 
class index: 
    def response(self, url):
        try:
            sitesxml = ('cswhcs.', 'dreamartscenter.', 'muamh.', 'jsmlny.')
            if any(s in url for s in sitesxml):
                a, b, c = parse_url(url)
                #print(a, b, c)
                if b:
                    return render.image(a, b, c)
        except:
            return render.formtest('Error: ' + web.ctx['ip'])

    def GET(self): 
        input = web.input()
        if 'data' in input:
            b = base64.b64decode(input.data.encode('ascii'))
            url = b.decode('ascii')
            return self.response(url)
        else:
            return render.formtest('Hello: ' + web.ctx['ip'])

    def POST(self): 
        input = web.input()
        #print(input)
        if 'tar' in input:
            return self.response(input.tar)
        else:
            return render.formtest('Hello: ' + web.ctx['ip'])

# Process favicon.ico requests
class icon:
    def GET(self): raise web.seeother("/static/favico.png")

# process math requests
class mymath:
    def GET(self):
        model.init('db.conf.ini')
        answers = model.get_answers()
        return render.math(answers)

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()
