
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash, Markup

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DATABASEURI = "postgresql://asm2265:proj75pw@34.73.36.248/project1" # Modify this with your own credentials you received from Joseph!

engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/index')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)

  return render_template("index.html")


@app.route('/artist')
def artist():
  print(request.args)
  # artist_name = session['artist']
  # cursor = g.conn.execute("SELECT * FROM artist WHERE LOWER(name) = LOWER(%s)", artist_name)
  if len(session['artist']) == 0:
    artist_id = session['artist_id']
    cursor = g.conn.execute("SELECT * FROM artist WHERE artist_id = %s", artist_id)
  else:  
    artist_name = session['artist']
    cursor = g.conn.execute("SELECT * FROM artist WHERE LOWER(name) = LOWER(%s)", artist_name)
  names = []
  ids = []

  ##GET ARTIST NAME FOR ARTIST PAGE
  for result in cursor:
    names.append(result['name'])
    ids.append(result['artist_id'])
  cursor.close()

  if len(ids) == 0:
    print("artist not found")
    msg = Markup("<span style=\"background-color: #FFCCCC\">Could not find artist \'{}\'</span>".format(artist_name))
    flash(msg)
    return redirect('/index')
  
  ##LIST OF ALBUMS ON ARTIST PAGE ( HYPERLINKS )
  artist_id = ids[0]
  cursor = g.conn.execute("SELECT * FROM album WHERE artist_id = %s order by release_date desc", artist_id)
  album_names = []
  album_ids = []
  years = []
  for result in cursor:
    album_names.append(result['title'])
    album_ids.append(result['album_id'])
    years.append(result['release_date'].year)
  cursor.close()

  context = dict(data_names = names, data_album_names = album_names, data_album_ids = album_ids, years = years)
  return render_template("artist.html", **context)


@app.route('/artist_id/<artist_id>', methods=['GET'])
def artist_name(artist_id):
  session['artist'] = ""
  session['artist_id'] = artist_id
  return redirect(url_for('.artist', artist = artist_id))

@app.route('/user')
def user():
  print(request.args)
  if len(session['user']) == 0:
    user_id = session['user_id']
    cursor = g.conn.execute("SELECT * FROM users WHERE user_id = %s", user_id)
  else:  
    user_name = session['user']
    cursor = g.conn.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(%s)", user_name)
  
  names = []
  ids = []
  emails = []

  ##GET USER NAME FOR USER PAGE
  for result in cursor:
    names.append(result['username'])
    ids.append(result['user_id'])
    emails.append(result['email'])
  cursor.close()

  if len(ids) == 0:
    print("user not found")
    msg = Markup("<span style=\"background-color: #FFCCCC\">Could not find user \'{}\'</span>".format(user_name))
    flash(msg)
    return redirect('/index')
  
  ##COMMENTS COUNT FOR USER PAGE
  user_id = ids[0]
  cursor = g.conn.execute("SELECT * FROM comment WHERE user_id = %s", user_id)
  comment_num=0
  for result in cursor:
    comment_num+=1
  cursor.close()

  context = dict(emails=emails,username=names,comment_num=comment_num,user_ids=ids)
  return render_template("user.html", **context)

## Executes when an user hyperlink is clicked
@app.route('/user_id/<user_id>', methods=['GET'])
def user_name(user_id):
  session['user'] = ""
  session['user_id'] = user_id
  return redirect(url_for('.user', user = user_id))

@app.route('/album')
def album():
  print(request.args)
  if len(session['album']) == 0:
    album_id = session['album_id']
    cursor = g.conn.execute("SELECT * FROM album WHERE album_id = %s", album_id)
  else:  
    album_name = session['album']
    cursor = g.conn.execute("SELECT * FROM album WHERE LOWER(title) = LOWER(%s)", album_name)
  
  titles = []
  ids = []
  dates = []
  ##GET ALBUM INFO FOR ALBUM PAGE
  for result in cursor:
    titles.append(result['title'])
    ids.append(result['album_id'])
    dates.append(result['release_date'])
  
  if len(ids) == 0:
    print("album not found")
    msg = Markup("<span style=\"background-color: #FFCCCC\">Could not find album \'{}\'</span>".format(album_name))
    flash(msg)
    return redirect('/index')
  elif len(ids) > 1:
    return redirect(url_for('.search_list_album', search_list_album = session['album']))
  album_id = ids[0]

  year = dates[0].year

  ##LIST OF SONGS ON ALBUM PAGE ( HYPERLINKS )
  cursor = g.conn.execute("SELECT * FROM song WHERE album_id = %s order by track_num", album_id)
  artist_ids = []
  song_names = []
  song_ids = []
  for result in cursor:
    song_names.append(result['title'])
    song_ids.append(result['song_id'])
    artist_ids.append(result['artist_id'])

  ##GET ARTIST NAME FOR ALBUM PAGE
  cursor = g.conn.execute("SELECT * FROM artist WHERE artist_id = %s", artist_ids[0])
  artist_names = []
  for result in cursor:
    artist_names.append(result['name'])
  
  ##GET COMMENT TEXT FOR ALBUM PAGE
  cursor = g.conn.execute("SELECT text, comment_id, user_id FROM comment WHERE album_id=%s and comment_id NOT IN (SELECT comment_id FROM moderator_comment) order by comment_id desc",album_id)
  comments = []
  comment_ids = []
  user_ids = []
  for result in cursor:
    comments.append(result['text'])
    comment_ids.append(result['comment_id'])
    user_ids.append(result['user_id'])

  ##GET USER NAMES FOR ALBUM PAGE ( EACH USERNAME IS A HYPERLINK ABOVE A COMMENT )
  user_names = []
  for i in range(len(user_ids)):
    cursor = g.conn.execute("SELECT * FROM users WHERE user_id = %s", user_ids[i])
    for result in cursor:
      user_names.append(result['username'])
    cursor.close()

  context = dict(artist_id = artist_ids[0], data_titles = titles, data_song_names = song_names, data_song_ids = song_ids, data_artist_names = artist_names, 
                data_release_year = year, data_comments = comments, data_user_ids = user_ids, data_user_names = user_names, comment_ids = comment_ids,
                client_id = session['client_id'], mod_id = session['moderator'])
  return render_template("album.html", **context)
  
## Executes when an album hyperlink is clicked
@app.route('/album_id/<album_id>', methods=['GET'])
def album_name(album_id):
  session['album'] = ""
  session['album_id'] = album_id
  return redirect(url_for('.album', album = album_id))

@app.route('/song')
def song():
  print(request.args)
  if len(session['song']) == 0:
    song_id = session['song_id']
    cursor = g.conn.execute("SELECT * FROM song WHERE song_id = %s", song_id)
  else:  
    song_name = session['song']
    cursor = g.conn.execute("SELECT * FROM song WHERE LOWER(title) = LOWER(%s)", song_name)
  
  ##GET SONG INFO FOR SONG PAGE
  titles = []
  ids = []
  # album_ids = []
  # artist_ids = []
  durations = []
  features = []
  for result in cursor:
    titles.append(result['title'])
    ids.append(result['song_id'])
    ids.append(result['album_id'])
    ids.append(result['artist_id'])
    ms = int(result['duration_ms'])
    seconds = (ms // 1000) % 60
    mins = (ms // 60000) % 60
    durations.append("{} min, {} sec".format(mins, seconds))
    features.append(result['artist_features'])


  if len(ids) == 0:
    print("song not found")
    msg = Markup("<span style=\"background-color: #FFCCCC\">Could not find song \'{}\'</span>".format(song_name))
    flash(msg)
    return redirect('/index')
  elif len(durations) > 1:
    return redirect(url_for('.search_list_song', search_list_song = session['song']))
  song_id = ids[0]
  album_id = ids[1]
  artist_id = ids[2]
  feature_names = []

  ##GET ARTIST FEATURES FOR SONG PAGE
  try:
    for i in range(len(features[0])):
      cursor = g.conn.execute("SELECT * FROM artist WHERE artist_id = %s", features[0][i])
      for result in cursor:
        feature_names.append(result['name'])
      cursor.close()
  except:
    features[0] = ""

  ##GET ALBUM NAME FOR SONG PAGE
  cursor = g.conn.execute("SELECT * FROM album WHERE album_id = %s", album_id)
  album_names = []
  for result in cursor:
    album_names.append(result['title'])

  ##GET ARTIST NAME FOR SONG PAGE
  cursor = g.conn.execute("SELECT * FROM artist WHERE artist_id = %s", artist_id)
  artist_names = []
  for result in cursor:
    artist_names.append(result['name'])
  cursor.close()

  ##GET COMMENTS FOR SONG PAGE
  cursor = g.conn.execute("SELECT text, comment_id, user_id FROM comment WHERE song_id=%s and comment_id NOT IN (SELECT comment_id FROM moderator_comment) order by comment_id desc",song_id)
  comments = []
  comment_ids = []
  user_ids = []
  for result in cursor:
    comments.append(result['text'])
    comment_ids.append(result['comment_id'])
    user_ids.append(result['user_id'])
  cursor.close()
  ##GET USER NAMES FOR SONG PAGE
  user_names = []
  for i in range(len(user_ids)):
    cursor = g.conn.execute("SELECT * FROM users WHERE user_id = %s", user_ids[i])
    for result in cursor:
      user_names.append(result['username'])
    cursor.close()
  
  rating = []
  cursor = g.conn.execute("SELECT AVG(rating) as rating from user_rates_song WHERE song_id =%s", song_id)
  for result in cursor:
    rating.append(result['rating'])

  context = dict(album_id = album_id,artist_id = artist_id,data_titles = titles, data_ids = ids, data_album_names = album_names, data_artist_names = artist_names, 
                  durations=durations,comments=comments,user_ids=user_ids,user_names=user_names, features=features, feature_names=feature_names, comment_ids = comment_ids, 
                  client_id = session['client_id'], mod_id = session['moderator'], rating = rating)
  return render_template("song.html", **context)

## Executes when a song hyperlink is clicked
@app.route('/song_id/<song_id>', methods=['GET'])
def song_name(song_id):
  session['song'] = ""
  session['song_id'] = song_id
  return redirect(url_for('.song', song = song_id))

## Multiple results song
@app.route('/search_list_song')
def search_list_song():
  print(request.args)
  cursor = g.conn.execute("SELECT * FROM song WHERE LOWER(title) = LOWER(%s)", session['song'])
  song_names = []
  artist_ids = []
  album_ids = []
  song_ids = []

  ##GET ARTIST NAME FOR MULTIPLE SEARCH PAGE
  for result in cursor:
    song_names.append(result['title'])
    artist_ids.append(result['artist_id'])
    album_ids.append(result['album_id'])
    song_ids.append(result['song_id'])
  cursor.close()

  artist_names = []
  for i in range(len(artist_ids)):
    cursor = g.conn.execute("SELECT * FROM artist WHERE artist_id = %s", artist_ids[i])
    for result in cursor:
      artist_names.append(result['name'])
    cursor.close()
  
  ## GET ALBUM NAME FOR EACH RESULT IN PAGE
  album_names = []
  years = []
  for i in range(len(album_ids)):
    cursor = g.conn.execute("SELECT * FROM album WHERE album_id = %s", album_ids[i])
    for result in cursor:
      album_names.append(result['title'])
      years.append(result['release_date'].year)
    cursor.close()

  context = dict(artist_names=artist_names,title=song_names,ids=song_ids,album_names=album_names, years=years)
  return render_template("search_list_song.html", **context)

## Multiple results album
@app.route('/search_list_album')
def search_list_album():
  print(request.args)
  cursor = g.conn.execute("SELECT * FROM album WHERE LOWER(title) = LOWER(%s)", session['album'])
  album_names = []
  artist_ids = []
  album_ids = []
  years = []
  ##GET ARTIST NAME FOR MULTIPLE SEARCH PAGE
  for result in cursor:
    album_names.append(result['title'])
    artist_ids.append(result['artist_id'])
    album_ids.append(result['album_id'])
    years.append(result['release_date'].year)
  cursor.close()

  artist_names = []
  for i in range(len(artist_ids)):
    cursor = g.conn.execute("SELECT * FROM artist WHERE artist_id = %s", artist_ids[i])
    for result in cursor:
      artist_names.append(result['name'])
    cursor.close()
  context = dict(artist_names=artist_names,title=album_names,ids=album_ids,years=years)
  return render_template("search_list_album.html", **context)

### Search functionality on index page
@app.route('/search', methods=['POST'])
def search():
  session['album_id'] = 0
  session['song_id'] = 0
  session['artist_id'] = 0
  session['user_id'] = 0
  searched_name = request.form['name']
  search_type = request.form['type']
  if search_type == "artist":
    session['artist'] = searched_name
    return redirect(url_for('.artist', artist = searched_name))
  elif search_type == "album":
    session['album'] = searched_name
    return redirect(url_for('.album', album = searched_name))
  elif search_type == "song":
    session['song'] = searched_name
    return redirect(url_for('.song', song = searched_name))
    # return redirect(url_for('.search_list', search_list = searched_name))
  elif search_type == "user":
    session['user'] = searched_name
    return redirect(url_for('.user', user = searched_name))

@app.route('/logins', methods=['POST'])
def logins():
  session['moderator'] = 0
  session['client_id']= 0
  uname = request.form['uname']
  password = request.form['psw']
  pword = []
  uid = []
  cursor = g.conn.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(%s)",uname)
  for result in cursor:
    pword.append(result['password'])
    uid.append(result['user_id'])
  cursor.close()
  if len(pword)!=0:
    if password == pword[0]:
      session['client_id']=uid[0]
      cursor = g.conn.execute("SELECT * FROM moderator WHERE user_id = %s",session['client_id'])
      mod_id = []
      for result in cursor:
        mod_id.append(result['user_id'])
      cursor.close()
      if len(mod_id) > 0:
        session['moderator'] = 1
      else:
        session['moderator'] = 0
      print("Successful login")
      return redirect(url_for('.index', client_id = session['client_id']))
    else:
      print("Wrong password")
      msg = Markup("<span style=\"background-color: #FFCCCC\">Wrong password, try again.</span>")
      flash(msg)
      return redirect('/')
  else:
    print("User not found")
    msg = Markup("<span style=\"background-color: #FFCCCC\">Could not find user \'{}\'</span>".format(uname))
    flash(msg)
    return redirect('/')


 

@app.route('/album_comment', methods=['POST'])
def album_comment():
  text = request.form['text']
  album_id = session['album_id']
#  try: 
#    user_id = session['user_id']
#  except:
#    msg = Markup("<span style=\"background-color: #FFCCCC\">Please sign in</span>")
#    flash(msg)
#    return redirect(url_for('.album', album = session['album_id']))
  ##SET COMMENT ID
  cursor = g.conn.execute("SELECT MAX(comment_id) as comment_id FROM comment")
  for result in cursor:
    comment_id = result['comment_id']
  g.conn.execute('INSERT INTO comment(text, comment_id, user_id, album_id, song_id) VALUES (%s, %s, %s, %s, null)', text, comment_id + 1, session['client_id'], album_id)
  return redirect(url_for('.album', album = session['album_id']))

@app.route('/song_comment', methods=['POST'])
def song_comment():
  text = request.form['text']
  song_id = session['song_id']

  cursor = g.conn.execute("SELECT MAX(comment_id) as comment_id FROM comment")
  for result in cursor:
    comment_id = result['comment_id']
  g.conn.execute('INSERT INTO comment(text, comment_id, user_id, album_id, song_id) VALUES (%s, %s, %s, null, %s)', text, comment_id + 1, session['client_id'], song_id)
  return redirect(url_for('.song', song = session['song_id']))

##DELETE COMMENTS BY ADDING INTO MODERATOR_COMMENT TABLE
@app.route('/delete/<comment_id>', methods=['GET'])
def delete(comment_id):
  mod_id = session['moderator']
  if mod_id > 0:
    g.conn.execute('INSERT INTO moderator_comment(user_id, comment_id) VALUES (%s, %s)', mod_id, comment_id)
  else:
    g.conn.execute('INSERT INTO moderator_comment(user_id, comment_id) VALUES (%s, %s)', 1, comment_id) ##when a user deletes their own comment, moderator 1 is used
  if int(session['song_id']) > 0:
    song_id = session['song_id']
    return redirect(url_for('.song', song = song_id))
  else:
    album_id = session['album_id']
    return redirect(url_for('.album', album = album_id))


@app.route('/')
def login():
    # abort(401)
    # this_is_never_executed()
    return render_template("login.html")


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.secret_key = 'secret_key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
