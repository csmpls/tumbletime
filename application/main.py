from flask import Flask, redirect, url_for, session, request
from flask import g, session, request, url_for, flash
from flask import redirect, render_template, jsonify
from flask_oauthlib.client import OAuth
import pytumblr


SECRET_KEY = 'a555c33332'
DEBUG = True

CONSUMER_KEY = 'eGV5NNygl2TLbDezHeUfcgArAPY6YSk3fE2dRUaNHOclQumJfu'
CONSUMER_SECRET = 'NBw7MOnMTuuOrQ7ofa586QJAOkNMGsxKx3MJwMIKDIQtcQJl4J'

app = Flask(__name__)
app.debug = DEBUG
app.secret_key = SECRET_KEY
oauth = OAuth()

tumblr = oauth.remote_app('tumblr',
    base_url='http://www.tumblr.com',
    request_token_url='/oauth/request_token',
    access_token_url='/oauth/access_token',
    authorize_url='/oauth/authorize',
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
)

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
    if g.user:

        oauth_token, oauth_token_secret = get_tumblr_token()
        client = pytumblr.TumblrRestClient(CONSUMER_KEY,CONSUMER_SECRET,oauth_token, oauth_token_secret)

        # this gives first 20 posts
        response = client.dashboard(type='photo')
        posts.extend(response['posts'])

        # now let's fetch the next 80
        for i in range (4):
            response = client.dashboard(type='photo', offset=20*(i+1))
            posts.extend(response['posts'])

        return render_template('index.html', posts=posts)

    return render_template('index.html', posts=None)


@app.route('/login')
def login():
    callback_url = url_for('oauthorized', next=request.args.get('next'))
    return tumblr.authorize(callback=callback_url or request.referrer or None)


@app.route('/logout')
def logout():
    session.pop('tumblr_oauth', None)
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
    print('ok got it')
    return jsonify(status='ok')

if __name__ == '__main__':
    app.run()