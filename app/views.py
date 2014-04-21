from flask import Flask, redirect, url_for, session, request
from flask import g, session, request, url_for, flash
from flask import redirect, render_template, jsonify
from flask_oauthlib.client import OAuth
import pytumblr, json
from datetime import datetime
from HTMLParser import HTMLParser
from random import choice
from app import app


load_messages = ['reaching into the void.......',
'loading shit hold up .....',
'wait........',
'1 sec..........',
'hold up........',
'summoning........',
'siphoning your things thru the ether.........',
'pulling thangs finding thangs......',
'loading thangs.......',
'it is loading.........',
'loadin shouldnt take 2 long....',
'pushing things thru the tubes....',
'420 blaze it',
'h/o......',
'brt......',
'coming....',
'purveying bits...........',
'loadin just be a sec.......']

CONSUMER_KEY = 'T4SwozU8g0zcSvTlq3C3OVfIVYLUFV0q2Tlo5mlcbPMI3mU0pS'
CONSUMER_SECRET = 'ivdHt8jOIzwNP8vijjz43i18cM82g8gVWb36YkPjAlJtVJmlaQ'

oauth = OAuth()

tumblr = oauth.remote_app('tumblr',
    base_url='http://www.tumblr.com',
    request_token_url='/oauth/request_token',
    access_token_url='/oauth/access_token',
    authorize_url='/oauth/authorize',
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
)

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def get_load_message():
    return choice(load_messages)

@tumblr.tokengetter
def get_tumblr_token():
    if 'tumblr_oauth' in session:
        resp = session['tumblr_oauth']
        return resp['oauth_token'], resp['oauth_token_secret']


@app.before_request
def before_request():
    g.user = None
    if 'tumblr_oauth' in session:
        g.user = session['tumblr_oauth']


@app.route('/')
def index():

    posts = [] 

    # do we have a session going?
    if g.user:

        # authenticate the user
        oauth_token, oauth_token_secret = get_tumblr_token()
        client = pytumblr.TumblrRestClient(CONSUMER_KEY,CONSUMER_SECRET,oauth_token, oauth_token_secret)

        # if user has picked a blog,
        # fetch posts
        if 'blogname' in session: 

            # this gives first 20 posts
            response = client.dashboard(type='photo')
            posts.extend(response['posts'])

            for post in posts:
                post['caption'] = strip_tags(post['caption'])


            # create a session var keep track off where our user is in the feed
            session['offset'] = 1

            return render_template('index.html', posts=posts, load_message=get_load_message())

        # if we have a session, but user hasn't picked a blog
        else:
            # redirect user to a blog selection interface
            user_blogs = client.info()['user']['blogs']
            return render_template('whichblog.html', user_blogs=user_blogs)

    return render_template('index.html', posts=None)

@app.route('/login')
def login():
    callback_url = url_for('oauthorized', next=request.args.get('next'))
    return tumblr.authorize(callback=callback_url or request.referrer or None)


@app.route('/logout')
def logout():
    session.pop('tumblr_oauth', None)
    session.pop('blogname', None)
    return redirect(url_for('index'))

@app.route('/select_blog', methods=['POST'])
def select_blog():
    # get post data
    blog_selection = request.form['blog']

    # save blog name as session var
    session['blogname'] = blog_selection

    return redirect(url_for('index'))


@app.route('/more', methods=['GET'])
def get_more():

    posts = []

    session['offset'] += 1

    if g.user and 'blogname' in session:

         # authenticate the user
        oauth_token, oauth_token_secret = get_tumblr_token()
        client = pytumblr.TumblrRestClient(CONSUMER_KEY,CONSUMER_SECRET,oauth_token, oauth_token_secret)


        # give next 20 posts from offset 
        response = client.dashboard(type='photo', offset=20*session['offset'])
        posts.extend(response['posts'])

        for post in posts:
            post['caption'] = strip_tags(post['caption'])

        return render_template('show_posts.html', posts=posts, load_message=get_load_message())



@app.route('/oauthorized')
@tumblr.authorized_handler
def oauthorized(resp):
    if resp is None:
        flash('You denied the request to sign in.')
    else:
        session['tumblr_oauth'] = resp
    return redirect(url_for('index'))

@app.route('/reblog', methods=['POST'])
def reblog():

    # get post data
    post_id = request.form['post_id']
    reblog_key = request.form['reblog_key']

    # authenticate
    oauth_token, oauth_token_secret = get_tumblr_token()
    client = pytumblr.TumblrRestClient(CONSUMER_KEY,CONSUMER_SECRET,oauth_token, oauth_token_secret)

    client.reblog(session['blogname'], id=post_id, reblog_key=reblog_key)

    return jsonify(status='ok')

@app.route('/like', methods=['POST'])
def like():

    # get post data
    post_id = request.form['post_id']
    reblog_key = request.form['reblog_key']

    # authenticate
    oauth_token, oauth_token_secret = get_tumblr_token()
    client = pytumblr.TumblrRestClient(CONSUMER_KEY,CONSUMER_SECRET,oauth_token, oauth_token_secret)

    client.like(id=post_id, reblog_key=reblog_key)

    return jsonify(status='ok')

@app.route('/steal', methods=['POST'])
def steal():

    # get post data
    photo_url = request.form['img']

    # authenticate
    oauth_token, oauth_token_secret = get_tumblr_token()
    client = pytumblr.TumblrRestClient(CONSUMER_KEY,CONSUMER_SECRET,oauth_token, oauth_token_secret)

    client.create_photo(session['blogname'], source=photo_url)

    return jsonify(status='ok')

@app.route('/done', methods=['POST'])
def done():

    # get post data
    keylog = request.json

    # write the json into a file with the current timestamp
    title = datetime.now().strftime("%d-%m-%y_%H:%M")
    with open('logs/'+str(title)+'.json', 'w') as outfile:
        json.dump(keylog, outfile)

    return jsonify(status='ok')
