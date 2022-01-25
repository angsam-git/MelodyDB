import os
import hashlib
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for, flash, Markup

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

DATABASEURI = "postgresql://postgres:melody@localhost:5432/MelodyDB"

engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print("error connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass

@app.route('/index')
def index():
  print(request.args)

  if session.get('selected_user') != True:
    return redirect('/')
  context = dict(user_name = session['user_name'], client_id = session['client_id'])
  return render_template("index.html", **context)


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
    msg = Markup("<span style=\"background-color: #FF9595\">Could not find artist \'{}\'</span>".format(artist_name))
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

  context = dict(data_names = names, data_album_names = album_names, data_album_ids = album_ids, years = years, client_id = session['client_id'],user_name = session['user_name'])
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
    msg = Markup("<span style=\"background-color: #FF9595\">Could not find user \'{}\'</span>".format(user_name))
    flash(msg)
    return redirect('/index')
  
  ##COMMENTS COUNT FOR USER PAGE
  user_id = ids[0]
  cursor = g.conn.execute("SELECT * FROM comment WHERE user_id = %s", user_id)
  comment_num=0
  for result in cursor:
    comment_num+=1
  cursor.close()

  context = dict(emails=emails,username=names,comment_num=comment_num,user_ids=ids, client_id = session['client_id'],user_name = session['user_name'])
  return render_template("user.html", **context)

## Executes when an user hyperlink is clicked
@app.route('/user_id/<user_id>', methods=['GET'])
def user_name(user_id):
  session['user'] = ""
  session['user_id'] = user_id
  return redirect(url_for('.user', user = user_id))

def round_half(x):
    return round(x * 2) / 2

@app.route('/album')
def album():
  session['song_id'] = 0
  ##if user not logged in set as guest
  if 'client_id' not in session:
    session['client_id'] = 0
    session['moderator'] = 0

  print(request.args)
  if len(session['album']) == 0:
    album_id = session['album_id']
    cursor = g.conn.execute("SELECT * FROM album WHERE album_id = %s", album_id)
  else:  
    album_name = session['album']
    cursor = g.conn.execute("SELECT * FROM album WHERE LOWER(title) = LOWER(%s)", album_name)
  
  print("HERE: %s", session['client_id'])

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
    msg = Markup("<span style=\"background-color: #FF9595\">Could not find album \'{}\'</span>".format(album_name))
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
  song_durations = []
  song_durations_formatted = []
  song_ratings = []
  for result in cursor:
    song_names.append(result['title'])
    song_ids.append(result['song_id'])
    artist_ids.append(result['artist_id'])
    rating = []
    cursor_two = g.conn.execute("SELECT AVG(rating)::numeric(3,2) as rating from user_rates_song WHERE song_id =%s", result['song_id'])
    for result_two in cursor_two:
      rating.append(result_two['rating'])
    if rating[0] is None:
      song_ratings.append(2.5)
    else:
      song_ratings.append(round_half(float(rating[0])))
    ms = int(result['duration_ms'])
    seconds = (ms // 1000) % 60
    mins = (ms // 60000) % 60
    song_durations.append(ms)
    song_durations_formatted.append("{} min, {} sec".format(mins, seconds))
  

  album_len = len(song_ids)
  album_duration_ms = sum(song_durations)
  seconds = (album_duration_ms // 1000) % 60
  mins = (album_duration_ms // 60000) % 60
  hrs = (album_duration_ms // 3600000)
  album_duration = []
  if hrs > 0:
    album_duration.append("{} hr, {} min".format(hrs, mins))
  else:
    album_duration.append("{} min, {} sec".format(mins, seconds))

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

  context = dict(artist_id = artist_ids[0], data_titles = titles, data_song_names = song_names, data_song_ids = song_ids, data_artist_names = artist_names, data_album_len = album_len, data_album_duration = album_duration[0],
                data_release_year = year, data_comments = comments, data_user_ids = user_ids, data_user_names = user_names, comment_ids = comment_ids, data_song_durations = song_durations_formatted, data_song_ratings = song_ratings,
                client_id = session['client_id'], mod_id = session['moderator'],user_name = session['user_name'])
  return render_template("album.html", **context)

## Executes when an album hyperlink is clicked
@app.route('/album_id/<album_id>', methods=['GET'])
def album_name(album_id):
  session['album'] = ""
  session['album_id'] = album_id
  return redirect(url_for('.album', album = album_id))

@app.route('/song')
def song():

  ##if user not logged in set as guest
  if 'client_id' not in session:
    session['client_id'] = 0
    session['moderator'] = 0

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
    msg = Markup("<span style=\"background-color: #FF9595\">Could not find song \'{}\'</span>".format(song_name))
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
  cursor = g.conn.execute("SELECT AVG(rating)::numeric(3,2) as rating from user_rates_song WHERE song_id =%s", song_id)
  for result in cursor:
    if result['rating'] is not None:
      rating.append(round_half(float(result['rating'])))
    else:
      rating.append(round_half(2.5))
  

  context = dict(album_id = album_id,artist_id = artist_id,data_titles = titles, data_ids = ids, data_album_names = album_names, data_artist_names = artist_names, 
                  durations=durations,comments=comments,user_ids=user_ids,user_names=user_names, features=features, feature_names=feature_names, comment_ids = comment_ids, 
                  client_id = session['client_id'], mod_id = session['moderator'], rating = rating,user_name = session['user_name'])
  return render_template("song.html", **context)

## Executes when a song hyperlink is clicked
@app.route('/song_id/<song_id>', methods=['GET'])
def song_name(song_id):
  session['song'] = ""
  session['song_id'] = song_id
  return redirect(url_for('.song', song = song_id))

## Executes when a user rates a song
@app.route('/user_rate/<rating>', methods=['GET'])
def user_rates(rating):
  print(session['client_id'])
  if session['client_id'] == 0:
    msg = Markup("<span style=\"background-color: #FF9595\">Please login to add ratings</span>")
    flash(msg)
    return redirect('/')
  try:
    cursor = g.conn.execute("INSERT INTO user_rates_song(song_id, rating, user_id) VALUES(%s, %s, %s)", session['song_id'], rating, session['client_id'])
  except:
    cursor = g.conn.execute("UPDATE user_rates_song SET rating = %s WHERE song_id = %s and user_id = %s", rating, session['song_id'], session['client_id'])
  return redirect(url_for('.song', song = session['song_id']))

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

  context = dict(artist_names=artist_names,title=song_names,ids=song_ids,album_names=album_names, years=years, client_id = session['client_id'],user_name = session['user_name'])
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
  context = dict(artist_names=artist_names,title=album_names,ids=album_ids,years=years, client_id = session['client_id'],user_name = session['user_name'])
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
  if len(searched_name) == 0:
    msg = Markup("<span style=\"background-color: #FF9595\">Please fill the search field</span>")
    flash(msg)
    return redirect('/index')
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
  session['client_id'] = 0

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
    hashed_pw = hashpw(password, (int(uid[0]) * 2) + 3)
    print(hashed_pw)
    print(pword[0])
    if hashed_pw == pword[0]:
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
      session['user_name'] = uname
      session['selected_user'] = True
      return redirect(url_for('.index', client_id = session['client_id']))
    else:
      print("Wrong password")
      msg = Markup("<span style=\"background-color: #FF9595\">Wrong password. Please try again.</span>")
      flash(msg)
      return redirect('/')
  else:
    print("User not found")
    msg = Markup("<span style=\"background-color: #FF9595\">Could not find user \'{}\'</span>".format(uname))
    flash(msg)
    return redirect('/')

@app.route('/guest_login')
def guest_login():
  session['selected_user'] = True
  session['user_name'] = 'Guest'
  return redirect(url_for('.index', client_id = 0))

@app.route('/registration')
def registration():
  return render_template("register.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
  uname = request.form['uname']
  email = request.form['email']
  password = request.form['psw']
  password_confirm = request.form['psw_confirm']
  uid = []

  # Check to make sure registration entries are valid
  total_num = sum(c.isdigit() for c in password)
  if total_num < 2:
    msg = Markup("<span style=\"background-color: #FF9595\">Password must contain at least two numbers.</span>")
    flash(msg)
    return redirect('/registration')

  if password != password_confirm:
    msg = Markup("<span style=\"background-color: #FF9595\">Confirm password must match password.</span>")
    flash(msg)
    return redirect('/registration')

  cursor = g.conn.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(%s)",uname)
  for result in cursor:
    uid.append(result['user_id'])

  if len(uid) > 0:
    msg = Markup("<span style=\"background-color: #FF9595\">Username already in use. Please try a different username.</span>")
    flash(msg)
    return redirect('/registration')

  cursor = g.conn.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(%s)",email)
  for result in cursor:
    uid.append(result['user_id'])

  if len(uid) > 0:
    msg = Markup("<span style=\"background-color: #FF9595\">Email already in use. Please try a different email.</span>")
    flash(msg)
    return redirect('/registration')

  #Register account
  cursor = g.conn.execute("SELECT MAX(user_id) AS max_id FROM users")
  for result in cursor:
    uid.append(result['max_id'])

  hashed_pw = hashpw(password, ((int(uid[0]) + 1) * 2) + 3)
  cursor = g.conn.execute("INSERT INTO users(user_id, username, email, password) VALUES(%s, %s, %s, %s)", int(uid[0]) + 1, uname, email, hashed_pw)

  session['client_id']= int(uid[0]) + 1
  session['user_name'] = uname
  session['selected_user'] = True
  return redirect(url_for('.index', client_id = session['client_id']))

#HASH PASSWORD n TIMES
def hashpw(pw, n):
  password = pw
  while n > 0:
    password = hashlib.md5(password.encode()).hexdigest()
    n = n-1
  return password

##EXECUTES WHEN COMMENT IS ADDED TO AN ALBUM PAGE
@app.route('/album_comment', methods=['POST'])
def album_comment():

  ##Redirect to login page if user not logged in
  if session['client_id'] == 0:
    return redirect('/')

  text = request.form['text']
  album_id = session['album_id']

  if len(text) == 0:
    return redirect(url_for('.album', album = session['album_id']))
  cursor = g.conn.execute("SELECT MAX(comment_id) as comment_id FROM comment")
  for result in cursor:
    comment_id = result['comment_id']
  g.conn.execute('INSERT INTO comment(text, comment_id, user_id, album_id, song_id) VALUES (%s, %s, %s, %s, null)', text, comment_id + 1, session['client_id'], album_id)
  return redirect(url_for('.album', album = session['album_id']))

##EXECUTES WHEN COMMENT IS ADDED TO A SONG PAGE
@app.route('/song_comment', methods=['POST'])
def song_comment():

  ##Redirect to login page if user not logged in
  if session['client_id'] == 0:
    return redirect('/')

  text = request.form['text']
  song_id = session['song_id']

  if len(text) == 0:
    return redirect(url_for('.song', song = session['song_id']))
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
    print(album_id)
    return redirect(url_for('.album', album_id = album_id))


@app.route('/')
def login():
    if 'client_id' not in session:
      session['client_id'] = 0
    elif session['client_id'] != 0:
      return redirect('/index')
    return render_template("login.html")

@app.route('/logout')
def logout():
  session['selected_user'] = False
  session['client_id'] = 0
  return redirect('/')


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.secret_key = 'secret_key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
