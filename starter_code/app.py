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
from models import Venue, Artist, Shows, app, db
from flask_migrate import Migrate
from sqlalchemy import literal, func
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#


moment = Moment(app)
app.config.from_object('config')


migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# I moved all the models to models.py file


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
# My methods.
#----------------------------------------------------------------------------#


def compareBetweenYears(showTime):
    # getting today year
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    today = format_datetime(dt_string)
    todayArray = today.replace(',', '').split(' ')
    todaYear = todayArray[3]
    # getting show year
    showTime = format_datetime(showTime)
    showTimeArray = showTime.replace(',', '').split(' ')
    showYear = showTimeArray[3]
    return todaYear < showYear

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
    # I used group by to get list of cities and states
    results = db.session.query(Venue.city, Venue.state).group_by(
        Venue.state, Venue.city)
    # I added every venue to it's corresponding city and state
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
    # I used strip method to remove white spaces
    # then from stackover flow I learned how to filter the results case insensitive
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


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    venue.genres = venue.genres.split(',')

    # After checking the review I impelmented the JOIN statment below:
    shows = db.session.query(Shows).join(
        Venue, Shows.venue_id == venue_id).all()

    past_shows = list()
    upcoming_shows = list()
    for show in shows:
        pastOrfuture = compareBetweenYears(show.start_time)
        showTemp = {
            'artist_id': show.artist_id,
            'artist_name': Artist.query.get(show.artist_id).name,
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
        # taking venue information from the form
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


@ app.route('/venues/<venue_id>/delete')
def delete_venue(venue_id):
    # delete venue and every related shows
    venue = Venue.query.get(venue_id)
    venueShows = venue.shows
    for show in venueShows:
        db.session.delete(show)
    db.session.delete(venue)
    db.session.commit()
    return render_template('pages/home.html')

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


@ app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist = Artist.query.get(artist_id)
    artist.genres = artist.genres.split(',')

    # After checking the review I impelmented the JOIN statment below to get the shows:
    shows = db.session.query(Shows).join(
        Venue, Shows.artist_id == artist_id).all()

    past_shows = list()
    upcoming_shows = list()
    for show in shows:
        pastOrfuture = compareBetweenYears(show.start_time)
        showTemp = {

            'venue_id': show.venue_id,
            'venue_name': Venue.query.get(show.venue_id).name,
            'venue_image_link': Venue.query.get(show.venue_id).image_link,
            'start_time': show.start_time
        }

        if pastOrfuture:
            upcoming_shows.append(showTemp)
        else:
            past_shows.append(showTemp)
    artist.upcoming_shows = upcoming_shows
    artist.past_shows = past_shows
    artist.past_shows_count = len(past_shows)
    artist.upcoming_shows_count = len(upcoming_shows)
    return render_template('pages/show_artist.html', artist=artist)


@ app.route('/artists/<artist_id>/delete')
def delete_artist(artist_id):
    artist = Artist.query.get(artist_id)
    artistShows = artist.shows
    for show in artistShows:
        db.session.delete(show)
    db.session.delete(artist)
    db.session.commit()
    return render_template('pages/home.html')

#  Update
#  ----------------------------------------------------------------


@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    try:
        artist = Artist.query.get(artist_id)
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        genresArray = request.form.getlist('genres')
        genres = ','.join(genresArray)
        artist.genres = genres
        seeking_description = request.form['seeking_description']
        # if the seeking description empty or None the seeking venue false
        if seeking_description == '' or seeking_description == 'None':
            seeking_venue = False
        else:
            seeking_venue = True
        artist.seeking_description = seeking_description
        artist.seeking_venue = seeking_venue
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.website = request.form['website']

        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info)
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@ app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@ app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.phone = request.form['phone']
        genresArray = request.form.getlist('genres')
        genres = ','.join(genresArray)
        venue.genres = genres
        seeking_description = request.form['seeking_description']
        if seeking_description == '' or seeking_description == 'None':
            seeking_venue = False
        else:
            seeking_venue = True
        venue.seeking_description = seeking_description
        venue.seeking_venue = seeking_venue
        venue.image_link = request.form['image_link']
        venue.facebook_link = request.form['facebook_link']
        venue.website = request.form['website']

        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info)
    finally:
        db.session.close()
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


@ app.route('/shows')
def shows():
    data = list()
    showsArr = Shows.query.all()

    for show in showsArr:
        showTemp = {

            'venue_id': show.venue_id,
            'artist_id': show.artist_id,
            'venue_name': Venue.query.get(show.venue_id).name,
            'artist_name': Artist.query.get(show.artist_id).name,
            'artist_image_link': Artist.query.get(show.artist_id).image_link,
            'start_time': show.start_time
        }

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
