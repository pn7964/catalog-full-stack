from flask import Flask, render_template
from flask import request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
from flask import session as login_session
from datetime import datetime

import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


# Facebook Authetication
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    access_token = access_token.decode()
    # print("access token received %s " % access_token)

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1].decode()

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v4.0/me"
    '''
        Due to the formatting for the result from the server token exchange
        we have to split the token first on commas and select the first index
        which gives us the key : value for the server access token then we
        split it on colons to pull out the actual token value and replace the
        remaining quotes with nothing so that it can be used directly in the
        graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v4.0/me?access_token=%s&fields=name, \
    id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print("url sent for API access:%s"% url)
    # print("API JSON result: %s" % result)
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v4.0/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("You are now logged in as %s" % login_session['username'])
    return output

# Google Authetication


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# Show catalog, with latest added items in each category


@app.route('/')
def showCatalog():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(desc(Item.added_date_time)).all()
    latest_items = []
    for item in items:
        exists = False
        for latest_item in latest_items:
            if(latest_item.category_id == item.category_id):
                exists = True
                break
        if not exists:
            latest_items.append(item)

    if 'username' not in login_session:
        return render_template('publiccatalog.html', items=latest_items, categories=categories)
    else:
        return render_template('catalog.html', items=latest_items, categories=categories)


# Shows all items of a selected Category


@app.route('/catalog/<string:category_name>/')
@app.route('/catalog/<string:category_name>/items')
def showCategory(category_name):
    categories = session.query(Category).all()
    items = []
    for category in categories:
        if(category.name == category_name):
            items = session.query(Item).filter_by(category_id=category.id).all()

    return render_template('publiccategory.html', items=items,
                           categories=categories,
                           category_name=category_name, no_of_items=len(items))

# Show Details of an Item


@app.route('/catalog/<string:category_name>/<string:item_title>')
def showItem(category_name, item_title):
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(Item).filter(Item.category_id == category.id,
                                      Item.title == item_title).first()
    creator = getUserInfo(item.user_id)
    # print(login_session['user_id'],creator.id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicitem.html', item=item)
    else:
        return render_template('item.html', item=item)


#  JSON API - Generates Catalog info in JSON format
@app.route('/catalog/JSON')
def catalogJSON():
    jcategories = []
    categories = session.query(Category).all()
    for category in categories:
        items = session.query(Item).filter_by(category_id=category.id).all()
        category = category.serialize
        items=[i.serialize for i in items]
        category["items"]=items
        jcategories.append(category)
    return jsonify(jcategories) 


# Add new Item

@app.route('/catalog/newItem', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        print(request.form['title'],request.form['description'],
        request.form['category'],login_session['user_id'])
        newItem = Item( title=request.form['title'], 
                        description=request.form['description'],
                        category_id=request.form['category'],
                        user_id=login_session['user_id'],
                        added_date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                       )
        session.add(newItem)
        flash('New item %s successfully added' % request.form['title'])
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        categories = session.query(Category).all()
        return render_template('newitem.html',categories=categories)



# Edit an Item

@app.route('/catalog/<string:category_name>/edit', methods=['GET', 'POST'])
def editItem(category_name):
    item_id=request.args["item_id"]
    editedItem = session.query(
        Item).filter_by(id=item_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedItem.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to edit this Item. Please create your own item in order to edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['title']:
            editedItem.title = request.form['title']
        if request.form['description']:
            editedItem.description = request.form['description']
        if(request.form['category']):
            editedItem.category_id = request.form['category']
        flash('Item Successfully Edited %s' % editedItem.title)
        return redirect(url_for('showCatalog'))
    else:
        categories=session.query(Category).all()
        return render_template('edititem.html', item=editedItem,categories=categories)


# Delete a restaurant


@app.route('/catalog/<string:category_name>/delete', methods=['GET', 'POST'])
def deleteItem(category_name):
    print(request.args["item_id"])
    item_id=request.args["item_id"]
    itemToDelete = session.query(
        Item).filter_by(id=item_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if itemToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized to delete this item. Please create your own item in order to delete.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        flash('%s Successfully Deleted' % itemToDelete.title)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteItem.html', item=itemToDelete)


# # Delete a menu item
# @app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods=['GET', 'POST'])
# def deleteMenuItem(restaurant_id, menu_id):
#     if 'username' not in login_session:
#         return redirect('/login')
#     restaurant = session.query(Restaurant).filter_by(id=restaurant_id).one()
#     itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()
#     if login_session['user_id'] != restaurant.user_id:
#         return "<script>function myFunction() {alert('You are not authorized to delete menu items to this restaurant. Please create your own restaurant in order to delete items.');}</script><body onload='myFunction()'>"
#     if request.method == 'POST':
#         session.delete(itemToDelete)
#         session.commit()
#         flash('Menu Item Successfully Deleted')
#         return redirect(url_for('showMenu', restaurant_id=restaurant_id))
#     else:
#         return render_template('deleteMenuItem.html', item=itemToDelete)
#
#
# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalog'))

# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response



@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000, threaded=False)
