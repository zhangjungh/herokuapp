# -*- coding: UTF-8 -*-
import os
import web
import base64
import hashlib
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

# urls
urls = (
    '/ip', 'ipecho',
    '/login', 'login',
    '/math', 'mymath',
    '/favicon.ico', 'icon',
    '/.*', 'index')

# wsgi or not
appwsgi = None

#allow sessions work
web.config.debug = False
app = web.application(urls, globals())
logger = logging.getLogger()

if not os.getenv('WEB_RUN'):
    appwsgi = app.wsgifunc()
    appwsgi = WhiteNoise(appwsgi, root='static/', prefix='static/')
    logger = logging.getLogger('gunicorn.error')

# sessions can be work in debug mode
if web.config.get('_session') is None:
    session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'login': 0, 'privilege': 0})
    web.config._session = session
else:
    session = web.config._session

if appwsgi is not None:
    app = appwsgi

# renders with session context
render = web.template.render('templates/', globals={'context': session})

def getRealIP():
    forward = 'HTTP_X_FORWARDED_FOR'
    real_ip = 'HTTP_X_REAL_IP'
    if forward in web.ctx.env:
        return web.ctx.env[forward].split(',')[0]
    if real_ip in web.ctx.env:
        return web.ctx.env[real_ip]    
    return web.ctx['ip']

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
            return render.index('Error: ' + getRealIP())

    def GET(self):
        if session.get('login', 0):
            input = web.input()
            if 'data' in input:
                b = base64.b64decode(input.data.encode('ascii'))
                url = b.decode('ascii')
                return self.response(url)
            else:
                return render.index('Hello: ' + getRealIP())
        else:
            raise web.seeother('/login')

    def POST(self):
        if session.get('login', 0):
            input = web.input()
            #print(input)
            if 'tar' in input:
                return self.response(input.tar)
            else:
                return render.index('Hello: ' + getRealIP())
        else:
            raise web.seeother('/login')

# Process favicon.ico requests
class icon:
    def GET(self): raise web.seeother("/static/favico.png")

# process math requests
class mymath:
    def GET(self):
        if session.get('login', 0):
            model.init('db.conf.ini')
            answers = model.get_answers()
            return render.math(answers)
        else:
            raise web.seeother('/login')

# process ip requests
class ipecho:
    def GET(self):
        return getRealIP()
    def POST(self):
        #web.header('Access-Control-Allow-Origin',      '*')
        #web.header('Access-Control-Allow-Credentials', 'true')
        #web.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        try:
            data = json.loads(web.data())
            key = data['key']
            id = data['id']
            if not key == 'queryImage':
                raise ValueError('wrong parameter!')
            model.init('db.conf.ini')
            image = model.get_image(id)
            if not image:
                raise ValueError('wrong id!')
            web.header('Content-Type', 'application/json')
            return json.dumps(image.data, ensure_ascii=False)
        except:
            ip = {'ip': getRealIP()}
            return json.dumps(ip)

# login
class login:
    def GET(self):
        if session.get('login', 0):
            raise web.seeother('/')
        else:
            return render.login('Plese Login')

    def POST(self):
        model.init('db.conf.ini')
        name, passwd = web.input().user, web.input().passwd + model.salt
        ident = model.get_user(name)
        try:
            pwd = hashlib.sha1(passwd.encode()).hexdigest()
            if pwd == ident['password']:
                session.login = 1
                session.privilege = ident['privilege']
                return render.index('Hello: ' + getRealIP())
            else:
                session.login = 0
                session.privilege = 0
                return render.login('Wrong username or password!')
        except:
            session.login = 0
            session.privilege = 0
            return render.login('Error happens!')

if __name__=="__main__":
    app.run()

#todo list:
# scheme wrong user db, block by ip with max try
# scheme mv

# nginx to host
# apply ssl on CF 65536.io/2020/03/607.html or certbot
# redirect http to https
# allow CF cache; ip whitelist
# new domain proxied with 80/443 port open
# apply new VM???
# fix postgres ip

# pgweb server?
# bitwarden server?