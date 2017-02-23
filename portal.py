#!/usr/bin/env python3

import os
import datetime
import argparse
import logging

from flask import (
    Flask,
    render_template,
    url_for,
    redirect,
    send_from_directory,
    session,
    abort,
    json,
)
from sqlalchemy.orm.exc import NoResultFound
from flask_sqlalchemy import SQLAlchemy, _QueryProperty

import model as m

# Create App
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Attach Database
db = SQLAlchemy(app)
db.Model = m.Base
# Ugly code to make Base.query work
m.Base.query_class = db.Query
m.Base.query = _QueryProperty(db)


def create_app(args):
    r"""
    Sets up app for use
    Adds logging, database configuration, and the secret key
    """
    global app, db
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True
    
    # setup Logging
    log = logging.getLogger('FlaskApp')
    log.setLevel(logging.ERROR)
    app.logger.addHandler(log)
    
    # setup Database
    app.config['SQLALCHEMY_DATABASE_URI'] = '{}:///{}'.format(
        args.type, args.database)
    db.create_all()
    
    # setup config values
    with app.app_context():
        config = {
            'SECRET_KEY': os.urandom(24),
            'PERMANENT_SESSION_LIFETIME': '30',
        }
        # get Config values from database
        for name in config:
            try:
                key = m.Config.query.filter_by(name=name).one()
                config[name] = key.value
            except NoResultFound:
                key = m.Config(name=name, value=config[name])
                db.session.add(key)
                db.session.commit()
        
        config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
            minutes=int(config['PERMANENT_SESSION_LIFETIME']))
        app.config.update(config)


def error(e, message):
    r"""
    Basic error template for all error pages
    """
    user = get_user()
    html = render_template(
        'error.html',
        title=str(e),
        message=message,
        user=user,
    )
    return html


@app.errorhandler(403)
def four_oh_three(e):
    r"""
    403 (forbidden) error page
    """
    return error(
        e,
        "You don't have access to this page."
    ), 403


@app.errorhandler(404)
def four_oh_four(e):
    r"""
    404 (page not found) error page
    """
    return error(
        e,
        "We couldn't find the page you were looking for."
    ), 404


@app.errorhandler(500)
def five_hundred(e):
    r"""
    500 (internal server) error page
    Will have to be changed for production version
    """
    return error(
        '500: '+str(e),
        "Whoops, looks like something went wrong!",
    ), 500


def get_user():
    r"""
    Gets the user data from the current session
    Returns the Tutor object of the current user
    """
    id = session.get('username')
    user = None
    if id:
        try:
            user = m.Tutors.query.filter_by(email=id).one()
        except NoResultFound:
            session.clear()
        
        if user and not user.is_active:
            session.clear()
            user = None
    return user


@app.route('/favicon.ico')
def favicon():
    r"""
    The favorites icon for the site
    """
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon',
    )


@app.route('/index.html')
@app.route('/')
def index():
    r"""
    The home page, from which tutors can login and students can open tickets
    """
    user = get_user()
    html = render_template(
        'index.html',
        home=True,
        user=user,
    )
    return html


@app.route('/status.html')
def status():
    r"""
    A status page for the CSLC
    
    For students displays:
        Annoucements
        Course Availability
    
    For tutors, also displays:
        Open Tickets
    """
    user = get_user()
    html = render_template(
        'status.html',
        user=user,
    )
    return html


@app.route('/open_ticket/index.html')
@app.route('/open_ticket/')
def open_ticket():
    r"""
    The student page for opening a ticket
    """
    user = get_user()
    html = render_template(
        'open_ticket.html',
        user=user,
    )
    return redirect(url_for('index'))


@app.route('/close_ticket/<ticket>')
def close_ticket(ticket):
    r"""
    The tutor page for claiming and closing tickets
    """
    user = get_user()
    if not user:
        return abort(403)
    
    html = render_template(
        'close_ticket.html',
        user=user,
    )
    return redirect(url_for('index'))


@app.route('/login/index.html')
@app.route('/login/')
def login():
    r"""
    Redirects the user to the UNO Single Sign On page
    """
    session.clear()
    session['username'] = 'test@unomaha.edu'
    html = redirect('https://auth.unomaha.edu/idp/Authn/UserPassword')
    html = redirect(url_for('index'))
    return html


@app.route('/logout/index.html')
@app.route('/logout/')
def logout():
    r"""
    Logs the user out and returns them to the homepage
    """
    session.clear()
    html = redirect(url_for('index'))
    return html


@app.route('/admin/index.html')
@app.route('/admin/')
def admin():
    r"""
    The admin configutration page
    Can add professors, semesters, courses, sections, tutors, and more
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)
    
    html = render_template(
        'admin.html',
    )
    return html


# ----#-   JSON
@app.route('/tickets.json')
def json_status():
    r"""
    Query needs checking
    """
    user = get_user()
    if not user:
        return abort(403)
    
    data = m.Tickets.query.filter(
        m.Tickets.status.in_((None, m.Status.Open))
    ).all()
    data = list(map(lambda a: a.dict(), data))
    return json.jsonify(d=data)


@app.route('/availability.json')
def json_availability():
    r"""
    Query needs checking
    Output needs checking
    """
    today = datetime.date.today()
    data = m.Courses.query.\
        join(m.can_tutor_table).join(m.Tutors).\
        join(m.Sections).join(m.Tickets).join(m.Semesters).\
        filter(m.Courses.on_display == True).\
        filter(m.Tickets.in_((None, m.Status.Open, m.Status.Claimed))).\
        filter(m.Semesters.start_date <= today).\
        filter(m.Semesters.end_date >= today).\
        all()
    lst = []
    for course in data:
        tickets = sum(len(section.tickets) for section in course.sections)
        tutors = len(course.tutors)
        lst.append({'course': course, 'tickets': tickets, 'tutors': tutors})
    return json.jsonify(d=data)


def main():
    port = 80  # default port
    parser = argparse.ArgumentParser(
        description='Tutoring Portal Server',
        epilog='The server runs locally on port %d if PORT is not specified.'
        % port)
    parser.add_argument(
        '--debug', dest='debug', action='store_true',
        help='run the server in debug mode')
    parser.add_argument(
        '-p, --port', dest='port', type=int,
        help='The port where the server will run')
    parser.add_argument(
        '-d, --database', dest='database', default=':memory:',
        help='The database to be accessed')
    parser.add_argument(
        '-t, --type', dest='type', default='sqlite',
        help='The type of database engine to be used')
    args = parser.parse_args()

    if args.port is None:  # Private System
        args.port = port
        host = '127.0.0.1'
    else:  # Public System
        host = '0.0.0.0'
        
    create_app(args)

    app.run(host=host, port=args.port, debug=args.debug, use_reloader=False)

if __name__ == '__main__':
    main()
