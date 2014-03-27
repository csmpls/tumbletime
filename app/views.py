from flask import Flask, redirect, url_for, session, request
from flask import g, session, request, url_for, flash
from flask import redirect, render_template, jsonify
from flask_oauthlib.client import OAuth
import pytumblr
from HTMLParser import HTMLParser
from app import app

CONSUMER_KEY = 'FPLOKGJWPtZY8svlFUj2aHCTZM7E84PVA1YYBRLDufiPTMwWwE'
CONSUMER_SECRET = 'Wpl9dCqYrOjuVoJCWh7n9z07A0YxZqnbC59mZpn1PHsmivZZhW'

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
        try: 

            # (this will cause a key error exception
            # if user hasn't picked a blog)
            session['blogname']

            # this gives first 20 posts
            response = client.dashboard(type='photo')
            posts.extend(response['posts'])

            # now let's fetch the next 80
            for i in range (4):
                response = client.dashboard(type='photo', offset=20*(i+1))
                posts.extend(response['posts'])

            for post in posts:
                post['caption'] = strip_tags(post['caption'])

            return render_template('index.html', posts=posts)

        # if we have a session, but user hasn't picked a blog
        except KeyError:

            session['blogname'] = None

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
    return redirect(url_for('index'))

@app.route('/select_blog', methods=['POST'])
def select_blog():
    # get post data
    blog_selection = request.form['blog']

    # save blog name as global, per-thread var
    session['blogname'] = blog_selection

    return redirect(url_for('index'))

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

# if __name__ == '__main__':
#     app.run()