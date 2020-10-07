#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from datetime import date
from datetime import datetime
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import literal, func
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Shows', backref='venue', lazy=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Shows', backref='artist', lazy=True)


# TODO: implement any missing fields, as a database migration using Flask-Migrate


class Shows(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    start_time = db.Column(db.String(120))


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


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
    data = list()

    results = db.session.query(Venue.city, Venue.state).group_by(
        Venue.state, Venue.city)

    for cityAndState in results.all():
        venues = Venue.query.filter_by(
            city=cityAndState.city, state=cityAndState.state).all()
        venuesArr = list()
        for venue in venues:
            venueTemp = {
                'id': venue.id,
                'name': venue.name
            }
            venuesArr.append(venueTemp)
        dataTemp = {
            'city': cityAndState.city,
            'state': cityAndState.state,
            'venues': venuesArr
        }
        data.append(dataTemp)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    term = request.form.get('search_term', '').strip()
    results = Venue.query.filter(func.lower(Venue.name).contains(term.lower()))
    data = list()
    if len(results.all()) > 0:
        print(results.all()[0].name, flush=True)
        for venue in results.all():
            venueTemp = {
                'id': venue.id,
                'name': venue.name
            }
            data.append(venueTemp)

    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@ app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    venue.genres = venue.genres.split(',')
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    today = format_datetime(dt_string)
    todayArray = today.replace(',', '').split(' ')
    todaYear = todayArray[3]

    past_shows = list()
    upcoming_shows = list()
    for show in venue.shows:
        showTime = format_datetime(show.start_time)
        showTimeArray = showTime.replace(',', '').split(' ')
        showYear = showTimeArray[3]
        pastOrfuture = todaYear < showYear
        showTemp = {
            'artist.id': show.artist_id,
            'artist.name': Artist.query.get(show.artist_id).name,
            'artist_image_link': Artist.query.get(show.artist_id).image_link,
            'start_time': show.start_time
        }

        if pastOrfuture:
            upcoming_shows.append(showTemp)
        else:
            past_shows.append(showTemp)

    venue.upcoming_shows = upcoming_shows
    venue.past_shows = past_shows
    venue.past_shows_count = len(past_shows)
    venue.upcoming_shows_count = len(upcoming_shows)
    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------


@ app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@ app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        genresArray = request.form.getlist('genres')
        image_link = request.form['image_link']
        facebook_link = request.form['facebook_link']
        genres = ','.join(genresArray)

        venue = Venue(
            name=name,
            city=city,
            state=state,
            address=address,
            phone=phone,
            genres=genres,
            image_link=image_link,
            facebook_link=facebook_link
        )

        # on successful db insert, flash success
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        flash('An error occurred. Venue ' +
              venue.name + ' could not be listed.')
        db.session.rollback()
        print(sys.exc_info)
    finally:
        db.session.close()
    return render_template('pages/home.html')


@ app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@ app.route('/artists')
def artists():
    data = list()
    artists = Artist.query.all()
    for artist in artists:
        artistTemp = {
            'id': artist.id,
            'name': artist.name
        }
        data.append(artistTemp)

    return render_template('pages/artists.html', artists=data)


@ app.route('/artists/search', methods=['POST'])
def search_artists():

    term = request.form.get('search_term', '').strip()
    results = Artist.query.filter(
        func.lower(Artist.name).contains(term.lower()))
    data = list()
    if len(results.all()) > 0:
        print(results.all()[0].name, flush=True)
        for artist in results.all():
            artistTemp = {
                'id': artist.id,
                'name': artist.name
            }
            data.append(artistTemp)
    print(data, flush=True)
    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


class ArtistShow:
    def __init__(self, venue_id, venue_name,  venue_image_link, start_time):
        self.venue_id = venue_id
        self.venue_name = venue_name
        self.venue_image_link = venue_image_link
        self.start_time = start_time


@ app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist = Artist.query.get(artist_id)
    artist.genres = artist.genres.split(',')
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    today = format_datetime(dt_string)
    todayArray = today.replace(',', '').split(' ')
    todaYear = todayArray[3]

    past_shows = list()
    upcoming_shows = list()
    for show in artist.shows:
        showTime = format_datetime(show.start_time)
        showTimeArray = showTime.replace(',', '').split(' ')
        showYear = showTimeArray[3]
        pastOrfuture = todaYear < showYear
        showTemp = ArtistShow(
            show.venue_id,
            Venue.query.get(show.venue_id).name,
            Venue.query.get(show.venue_id).image_link,
            show.start_time
        )
        if pastOrfuture:
            upcoming_shows.append(showTemp)
        else:
            past_shows.append(showTemp)
    artist.upcoming_shows = upcoming_shows
    artist.past_shows = past_shows
    artist.past_shows_count = len(past_shows)
    artist.upcoming_shows_count = len(upcoming_shows)
    return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------


@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = {
        "id": 4,
        "name": "Guns N Petals",
        "genres": ["Rock n Roll"],
        "city": "San Francisco",
        "state": "CA",
        "phone": "326-123-5000",
        "website": "https://www.gunsnpetalsband.com",
        "facebook_link": "https://www.facebook.com/GunsNPetals",
        "seeking_venue": True,
        "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
        "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    return redirect(url_for('show_artist', artist_id=artist_id))


@ app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = {
        "id": 1,
        "name": "The Musical Hop",
        "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
        "address": "1015 Folsom Street",
        "city": "San Francisco",
        "state": "CA",
        "phone": "123-123-1234",
        "website": "https://www.themusicalhop.com",
        "facebook_link": "https://www.facebook.com/TheMusicalHop",
        "seeking_talent": True,
        "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
        "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@ app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@ app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@ app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        genresArray = request.form.getlist('genres')
        seeking_description = request.form['seeking_description']
        if seeking_description == '':
            seeking_venue = False
        else:
            seeking_venue = True
        image_link = request.form['image_link']
        website = request.form['website']
        facebook_link = request.form['facebook_link']
        genres = ','.join(genresArray)

        artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            genres=genres,
            website=website,
            image_link=image_link,
            facebook_link=facebook_link,
            seeking_venue=seeking_venue,
            seeking_description=seeking_description
        )

        # on successful db insert, flash success
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        flash('An error occurred. Artist ' +
              venue.name + ' could not be listed.')
        db.session.rollback()
        print(sys.exc_info)
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------
class Show:
    def __init__(self, venue_id, artist_id, venue_name, artist_name, artist_image_link, start_time):
        self.venue_id = venue_id
        self.artist_id = artist_id
        self.venue_name = venue_name
        self.artist_name = artist_name
        self.artist_image_link = artist_image_link
        self.start_time = start_time


@ app.route('/shows')
def shows():
    data = list()
    showsArr = Shows.query.all()

    for show in showsArr:
        showTemp = Show(
            show.venue_id,
            show.artist_id,
            Venue.query.get(show.venue_id).name,
            Artist.query.get(show.artist_id).name,
            Artist.query.get(show.artist_id).image_link,
            show.start_time
        )
        data.append(showTemp)

    return render_template('pages/shows.html', shows=data)


@ app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@ app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        start_time = request.form['start_time']

        show = Shows(
            artist_id=artist_id,
            venue_id=venue_id,
            start_time=start_time
        )
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        flash('An error occurred. Show could not be listed.')
        db.session.rollback()
        print(sys.exc_info)
    finally:
        db.session.close()
    return render_template('pages/home.html')


@ app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@ app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
