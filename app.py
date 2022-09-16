#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime, timedelta
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app,db,compare_type=True)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city_id = db.Column(db.Integer, db.ForeignKey('City.id'),nullable=False)
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(900))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String,nullable=True)
    website = db.Column(db.String)

    show = db.relationship('Show',backref='vshow',lazy=False)
    genre = db.relationship('GenreVenue',backref='vgenre',lazy=False)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city_id = db.Column(db.Integer,db.ForeignKey('City.id'),nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(900))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String)
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String,nullable=True)

    show = db.relationship('Show',backref='ashow',lazy=False)
    genre = db.relationship('GenreArtist',backref='agenre',lazy=False)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show (db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer,primary_key=True)
  time = db.Column(db.DateTime(timezone=True),nullable=False)
  artist_id = db.Column(db.Integer,db.ForeignKey('Artist.id'),nullable=False)
  venue_id = db.Column(db.Integer,db.ForeignKey('Venue.id'),nullable=False)

class City(db.Model):
  __tablename__ = 'City'

  id = db.Column(db.Integer,primary_key=True)
  name = db.Column(db.String,nullable=False)
  state = db.Column(db.String(2),nullable=False)

  venue_rel = db.relationship('Venue',backref='cvenues',lazy=False)
  artist_rel = db.relationship('Artist',backref='cartists',lazy=False)

class Genre (db.Model):
  __tablename__ = 'Genre'

  id = db.Column(db.Integer,primary_key=True)
  name = db.Column(db.String,nullable=False)

  g_venue = db.relationship('GenreVenue',backref='cvenue',lazy=False)
  a_venue = db.relationship('GenreArtist',backref='cartist',lazy=False)

class GenreVenue(db.Model):
  __tablename__ = 'GenreVenue'

  id = db.Column(db.Integer,primary_key=True)
  genre_id = db.Column(db.Integer,db.ForeignKey(Genre.id))
  venue_id = db.Column(db.Integer,db.ForeignKey('Venue.id'))

class GenreArtist (db.Model):
  __tablename__ = 'GenreArtist'
  id = db.Column(db.Integer,primary_key=True)
  genre_id = db.Column(db.Integer,db.ForeignKey(Genre.id))
  artist_id = db.Column(db.Integer,db.ForeignKey(Artist.id))


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = value if not isinstance(value,str) else dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  data = []
  for c in City.query.all():
    venues = []
    for v in Venue.query.filter_by(city_id=c.id):
      s = Show.query.filter_by(venue_id=v.id).filter(Show.time>=datetime.today()).all()
      venues.append({
        'id':v.id,
        'name':v.name,
        'num_upcoming_shows':0 if s is None else len(s)
      })
    data.append({
      'city':c.name,
      'state':c.state,
      'venues':venues
    })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  term = request.form.get('search_term','')
  venues = Venue.query.filter(func.lower(Venue.name).contains(term.lower())).all()
  data = []
  for v in venues:
    c = Show.query.filter_by(venue_id=v.id).filter(Show.time>=datetime.today())
    data.append({
      'id':v.id,
      'name':v.name,
      'num_upcoming_shows':0 if c is None else len(c)
    })
  response = {
    'count':len(venues),
    'data':data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  venue = Venue.query.filter_by(id=venue_id).first()
  genres = Genre.query.join(GenreVenue).filter(GenreVenue.venue_id==venue.id).all()
  shows_coming = Show.query.filter_by(venue_id=venue.id).filter(Show.time>=datetime.today()).all()
  past_shows = Show.query.filter_by(venue_id=venue.id).filter(Show.time<datetime.today()).all()
  vg = []
  sc = []
  ps = []
  for g in genres:
    vg.append(g.name)
  for s in shows_coming:
    artist = Artist.query.filter_by(id=s.artist_id).first()
    sc.append({
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": s.time
    })

  for s in past_shows:
    artist = Artist.query.filter_by(id=s.artist_id).first()
    ps.append({
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": s.time
    })
  city = City.query.filter_by(id=venue.city_id).first()

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": vg,
    "address": venue.address,
    "city": city.name,
    "state": city.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "upcoming_shows":sc,
    "past_shows":ps,
    "past_shows_count":len(ps),
    "upcoming_shows_count":len(sc)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  # on successful db insert, flash success
  try:
    #City first
    city = City.query.filter_by(name=request.form['city'],state=request.form['state']).first()
    if city is None:
      city = City(name=request.form['city'],state=request.form['state'])
      db.session.add(city)
      db.session.commit()
    #Next genres
    genres = []
    for genre in request.form.getlist('genres'):
      g = Genre.query.filter_by(name=genre).first()
      if g is None:
        g = Genre(name=genre)
        db.session.add(g)
        db.session.commit()
      genres.append(g)
    venue = Venue(
      name=request.form['name'],
      city_id=city.id,
      address=request.form['address'],
      phone=request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form.get('facebook_link',False),
      seeking_talent = False if 'seeking_talent' not in request.form.keys() else True,
      seeking_description = request.form.get('seeking_description',False),
      website = request.form.get('website_link',False)
    )
    db.session.add(venue)
    for g in genres:
      gv = GenreVenue(
        venue_id = venue.id,
        genre_id = g.id
      )
      db.session.add(gv)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  except :
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    print(sys.exc_info())
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  v = Venue.query.filter_by(id=venue_id).first()
  try:
    gv = GenreVenue.query.filter_by(venue_id=venue_id).all()
    for g in gv:
      db.session.delete(g)
    sv = Show.query.filter_by(venue_id=venue_id).all()
    for s in sv:
      db.session.delete(s)
    db.session.delete(v)
    db.session.commit()
    flash ("Delete operation successful.")
  except:
    flash("Delete operation failed.")
    print(sys.exc_info())

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = []
  artists = Artist.query.all()
  for a in artists:
    data.append({
      'id':a.id,
      'name':a.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  term = request.form.get('search_term','')
  artists = Artist.query.filter(func.lower(Artist.name).contains(term.lower())).all()
  data = []
  for a in artists:
    c = Show.query.filter_by(artist_id=a.id).filter(Show.time>=datetime.today()).all()
    data.append({
     'id':a.id,
      'name':a.name,
      'num_upcoming_shows':0 if c is None else len(c)
    })
  response={
    "count":len(artists),
    'data':data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  artist = Artist.query.filter_by(id=artist_id).first()
  genres = Genre.query.join(GenreArtist).filter(GenreArtist.artist_id==artist.id).all()
  shows_coming = Show.query.filter_by(artist_id=artist.id).filter(Show.time>=datetime.today()).all()
  past_shows = Show.query.filter_by(artist_id=artist.id).filter(Show.time<datetime.today()).all()
  vg = []
  sc = []
  ps = []
  for g in genres:
    vg.append(g.name)
  for s in shows_coming:
    venue = Venue.query.filter_by(id=s.venue_id).first()
    sc.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": s.time
    })

  for s in past_shows:
    venue = Venue.query.filter_by(id=s.venue_id).first()
    ps.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": s.time
    })
  city = City.query.filter_by(id=artist.city_id).first()

  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": vg,
    "city": city.name,
    "state": city.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "upcoming_shows":sc,
    "past_shows":ps,
    "past_shows_count":len(ps),
    "upcoming_shows_count":len(sc)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  a = Artist.query.filter_by(id=artist_id).first()
  c = City.query.filter_by(id=a.city_id).first()
  genre = GenreArtist.query.filter_by(artist_id=a.id).all()
  g = []
  for gv in genre:
    g.append(Genre.query.filter_by(id=gv.genre_id).first().name)
  artist = {
    'id':a.id,
    'name':a.name,
    'genres':g,
    'city':c.name,
    'state':c.state,
    'phone':a.phone,
    'website':a.website,
    'facebook_link':a.facebook_link,
    'seeking_venue':a.seeking_venue,
    'seeking_description':a.seeking_description,
    'image_link':a.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  form.name.data = artist['name']
  form.genres.data = artist['genres']
  form.city.data = artist['city']
  form.state.data = artist['state']
  form.phone.data = artist['phone']
  form.website_link.data = artist['website']
  form.facebook_link.data = artist['facebook_link']
  form.seeking_venue.data = artist['seeking_venue']
  form.seeking_description.data = artist['seeking_description']
  form.image_link.data = artist['image_link']

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = request.form
  artist = Artist.query.filter_by(id=artist_id).first()
  try:
    genreA = form.getlist('genres')
    genreB = []
    #did the city change?
    c = City.query.filter_by(name=form.get('city'),state=form.get('state')).first()
    if c is None:
      c = City(name=form.get('city'),state=form.get('state'))
      db.session.add(c)
      db.session.commit()

    for g in GenreArtist.query.filter_by(artist_id=artist.id).all():
      genreB.append(Genre.query.filter_by(id=g.genre_id).first().name)


    #if a genre is in the before but not after, it is to be removed
    #if a genre is in the after but not before it needs to be added
    for g in genreA:
      if g not in genreB:
        genre = Genre.query.filter_by(name=g).first()
        if genre is None:
          genre = Genre(name=g)
          db.session.add(genre)
          db.session.commit()
          genre = Genre.query.filter_by(name=g).first()
        gr = GenreArtist(genre_id=genre.id,artist_id=artist.id)
        db.session.add(gr)
    for g in genreB:
      if g not in genreA:
        toberemoved = GenreArtist.query.filter_by(artist_id=artist.id,genre_id=Genre.query.filter_by(name=g).first().id).first()
        db.session.delete(toberemoved)

    artist.name = form.get('name')
    artist.city_id = c.id
    artist.phone = form.get('phone')
    artist.image_link = form.get('image_link')
    artist.facebook_link = form.get('facebook_link')
    artist.website = form.get('website_link')
    artist.seeking_venue = False if form.get('seeking_venue') is None else True
    artist.seeking_description = form.get('seeking_description')

    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully edited!')
  except:
    db.session.rollback()
    flash('error occured editing Artist ' + request.form['name'] )
    print(sys.exc_info())
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  v = Venue.query.filter_by(id=venue_id).first()
  c = City.query.filter_by(id=v.city_id).first()
  genre = GenreVenue.query.filter_by(venue_id=v.id).all()
  g = []
  for gv in genre:
    g.append(Genre.query.filter_by(id=gv.genre_id).first().name)
  venue = {
    'id':v.id,
    'name':v.name,
    'genres':g,
    'city':c.name,
    'state':c.state,
    'phone':v.phone,
    'website':v.website,
    'facebook_link':v.facebook_link,
    'seeking_talent':v.seeking_talent,
    'seeking_description':v.seeking_description,
    'image_link':v.image_link
  }
  # TODO: populate form with fields from venue with ID <venue_id>
  form.name.data = venue['name']
  form.genres.data = venue['genres']
  form.city.data = venue['city']
  form.state.data = venue['state']
  form.phone.data = venue['phone']
  form.website_link.data = venue['website']
  form.facebook_link.data = venue['facebook_link']
  form.seeking_talent.data = venue['seeking_talent']
  form.seeking_description.data = venue['seeking_description']
  form.image_link.data = venue['image_link']

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes

  form = request.form
  venue = Venue.query.filter_by(id=venue_id).first()
  try:
    genreA = form.getlist('genres')
    genreB = []
    #did the city change?
    c = City.query.filter_by(name=form.get('city'),state=form.get('state')).first()
    if c is None:
      c = City(name=form.get('city'),state=form.get('state'))
      db.session.add(c)
      db.session.commit()

    for g in GenreVenue.query.filter_by(venue_id=venue.id).all():
      genreB.append(Genre.query.filter_by(id=g.genre_id).first().name)


    #if a genre is in the before but not after, it is to be removed
    #if a genre is in the after but not before it needs to be added
    for g in genreA:
      if g not in genreB:
        genre = Genre.query.filter_by(name=g).first()
        if genre is None:
          genre = Genre(name=g)
          db.session.add(genre)
          db.session.commit()
          genre = Genre.query.filter_by(name=g).first()
        gr = GenreVenue(genre_id=genre.id,venue_id=venue.id)
        db.session.add(gr)
    for g in genreB:
      if g not in genreA:
        toberemoved = GenreVenue.query.filter_by(venue_id=venue.id,genre_id=Genre.query.filter_by(name=g).first().id).first()
        db.session.delete(toberemoved)

    venue.name = form.get('name')
    venue.city_id = c.id
    venue.phone = form.get('phone')
    venue.image_link = form.get('image_link')
    venue.facebook_link = form.get('facebook_link')
    venue.website = form.get('website_link')
    venue.seeking_talent = False if form.get('seeking_talent') is None else True
    venue.seeking_description = form.get('seeking_description')

    db.session.commit()
    flash('venue ' + request.form['name'] + ' was successfully edited!')
  except:
    db.session.rollback()
    flash('error occured editing venue ' + request.form['name'] )
    print(sys.exc_info())

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Artist record in the db, instead
  try:
    #City first
    city = City.query.filter_by(name=request.form['city'],state=request.form['state']).first()
    if city is None:
      city = City(name=request.form['city'],state=request.form['state'])
      db.session.add(city)
      db.session.commit()
    #Next genres
    genres = []
    for genre in request.form.getlist('genres'):
      g = Genre.query.filter_by(name=genre).first()
      if g is None:
        g = Genre(name=genre)
        db.session.add(g)
        db.session.commit()
      genres.append(g)
    artist = Artist(
      name=request.form['name'],
      city_id=city.id,
      phone=request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form.get('facebook_link',False),
      seeking_venue = False if 'seeking_venue' not in request.form.keys() else True,
      seeking_description = None if 'seeking_description' not in request.form.keys() else request.form.get('seeking_description'),
      website = request.form.get('website_link',False)
    )
    db.session.add(artist)
    db.session.commit()
    for g in genres:
      gv = GenreArtist(
        artist_id = artist.id,
        genre_id = g.id
      )
      db.session.add(gv)
    db.session.commit()
  # TODO: modify data to be the data object returned from db insertion

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  except:
    flash('An error occurred. Artist ' + request.form['name']  + ' could not be listed.')
    print(sys.exc_info())
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data=[]
  shows = Show.query.all()
  for s in shows:
    a = Artist.query.filter_by(id=s.artist_id).first()
    data.append({
      'venue_id':s.venue_id,
      'venue_name':Venue.query.filter_by(id=s.venue_id).first().name,
      'artist_id':s.artist_id,
      'artist_name':a.name,
      'artist_image_link':a.image_link,
      'start_time':s.time
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    form = request.form
    s = Show(artist_id=form.get('artist_id'),venue_id=form.get('venue_id'),time=form.get('start_time'))
    db.session.add(s)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  except:
    flash('An error occurred. Show could not be listed.')
    print(sys.exc_info())
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
