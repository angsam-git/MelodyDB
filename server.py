
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
from flask import Flask, request, render_template, g, redirect, Response, session, url_for

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

@app.route('/')
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

  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

  context = dict(data = names)

  return render_template("index.html", **context)


@app.route('/artist')
def artist():
  print(request.args)
  artist_name = session['artist']
  cursor = g.conn.execute("SELECT * FROM artist WHERE LOWER(name) = LOWER(%s)", artist_name)
  names = []
  ids = []
  for result in cursor:
    names.append(result['name'])
    ids.append(result['artist_id'])
  cursor.close()

  if len(ids) == 0:
    print("could not find") ##TO DO : HANDLE CASE WHEN SEARCH NOT IN TABLE
    return redirect('/')
  
  artist_id = ids[0]
  cursor = g.conn.execute("SELECT * FROM album WHERE artist_id = %s order by release_date desc", artist_id)
  album_names = []
  album_ids = []
  for result in cursor:
    album_names.append(result['title'])
    album_ids.append(result['album_id'])

  cursor.close()

  context = dict(data_names = names, data_album_names = album_names, data_album_ids = album_ids)
  return render_template("artist.html", **context)

@app.route('/album')
def album():
  print(request.args)
  cursor = None
  if len(session['album']) == 0:
    album_id = session['album_id']
    cursor = g.conn.execute("SELECT * FROM album WHERE album_id = %s", album_id)
  else:  
    album_name = session['album']
    cursor = g.conn.execute("SELECT * FROM album WHERE LOWER(title) = LOWER(%s)", album_name)
  
  titles = []
  ids = []
  dates = []
  for result in cursor:
    titles.append(result['title'])
    ids.append(result['album_id'])
    dates.append(result['release_date'])
  
  if len(ids) == 0:
    print("could not find") ##TO DO : HANDLE CASE WHEN SEARCH NOT IN TABLE
    return redirect('/')
  album_id = ids[0]

  year = dates[0].year

  cursor = g.conn.execute("SELECT * FROM song WHERE album_id = %s order by track_num", album_id)
  artist_ids = []
  song_names = []
  song_ids = []
  
  for result in cursor:
    song_names.append(result['title'])
    song_ids.append(result['song_id'])
    artist_ids.append(result['artist_id'])

  cursor = g.conn.execute("SELECT * FROM artist WHERE artist_id = %s", artist_ids[0])
  artist_names = []
  for result in cursor:
    artist_names.append(result['name'])
  cursor.close()

  context = dict(data_titles = titles, data_song_names = song_names, data_song_ids = song_ids, data_artist_names = artist_names, data_release_year = year)
  return render_template("album.html", **context)
  
@app.route('/album_id/<album_id>', methods=['GET'])
def album_name(album_id):
  session['album'] = ""
  session['album_id'] = album_id
  return redirect(url_for('.album', album = album_id))

@app.route('/song')
def song():
  print(request.args)
  cursor = None
  if len(session['song']) == 0:
    song_id = session['song_id']
    cursor = g.conn.execute("SELECT * FROM song WHERE song_id = %s", song_id)
  else:  
    song_name = session['song']
    cursor = g.conn.execute("SELECT * FROM song WHERE LOWER(title) = LOWER(%s)", song_name)
  
  titles = []
  ids = []
  album_ids = []
  artist_ids = []
  for result in cursor:
    titles.append(result['title'])
    ids.append(result['song_id'])
    ids.append(result['album_id'])
    ids.append(result['artist_id'])

  if len(ids) == 0:
    print("could not find") ##TO DO : HANDLE CASE WHEN SEARCH NOT IN TABLE
    return redirect('/')
  song_id = ids[0]
  album_id = ids[1]
  artist_id = ids[2]

  cursor = g.conn.execute("SELECT * FROM album WHERE album_id = %s", album_id)
  album_names = []
  for result in cursor:
    album_names.append(result['title'])

  cursor = g.conn.execute("SELECT * FROM artist WHERE artist_id = %s", artist_id)
  artist_names = []
  for result in cursor:
    artist_names.append(result['name'])
  cursor.close()

  context = dict(data_titles = titles, data_ids = ids, data_album_names = album_names, data_artist_names = artist_names)
  return render_template("song.html", **context)

@app.route('/song_id/<song_id>', methods=['GET'])
def song_name(song_id):
  session['song'] = ""
  session['song_id'] = song_id
  return redirect(url_for('.song', song = song_id))


### Search functionality on index page
@app.route('/search', methods=['POST'])
def search():
  session['album_id'] = 0
  session['song_id'] = 0
  session['artist_id'] = 0
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



@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


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
