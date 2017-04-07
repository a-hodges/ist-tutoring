#!/usr/bin/env python3

import os
import datetime
import argparse
import csv
import io

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from flask_sqlalchemy import SQLAlchemy, _QueryProperty
from flask_oauthlib.client import OAuth

import model as m
# Default ordering for admin types
m.Semesters.order_by = m.Semesters.start_date
m.Professors.order_by = m.Professors.last_first
m.Courses.order_by = m.Courses.number
m.Sections.order_by = m.Sections.number
m.ProblemTypes.order_by = m.ProblemTypes.description
m.Messages.order_by = m.Messages.end_date.desc()

# Create App
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Attach Database
db = SQLAlchemy(app)
db.Model = m.Base
# Ugly code to make Base.query work
m.Base.query_class = db.Query
m.Base.query = _QueryProperty(db)
# Configure Google OAuth
oauth = OAuth()
google = oauth.remote_app(
    'google',
    app_key='GOOGLE',
    request_token_params={'scope': 'email'},
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)


def create_app(args):
    r"""
    Sets up app for use
    Adds database configuration and the secret key
    """
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    # setup Database
    app.config['SQLALCHEMY_DATABASE_URI'] = '{}:///{}'.format(
        args.type, args.database)
    db.create_all()

    # setup config values
    with app.app_context():
        config = {
            'SECRET_KEY': os.urandom(24),
            'PERMANENT_SESSION_LIFETIME': '30',
            'GOOGLE_CONSUMER_KEY': os.urandom(24),
            'GOOGLE_CONSUMER_SECRET': os.urandom(24),
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


def date(string):
    r"""
    Convert a date formated string to a date object
    """
    if string == '':
        return None
    else:
        return datetime.datetime.strptime(string, '%Y-%m-%d').date()


def get_int(string):
    r"""
    Convert a string to int, returning none for invalid strings
    """
    ret = None
    if string is not None:
        try:
            ret = int(string)
        except ValueError:
            pass
    return ret


@app.context_processor
def context():
    r"""
    Makes extra variables available to the template engine
    """
    return dict(
        m=m,
        str=str,
        int=get_int,
        date=date,
        len=len,
    )


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
    return error(e, "You don't have access to this page."), 403


@app.errorhandler(404)
def four_oh_four(e):
    r"""
    404 (page not found) error page
    """
    return error(e, "We couldn't find the page you were looking for."), 404


@app.errorhandler(500)
def five_hundred(e):
    r"""
    500 (internal server) error page
    """
    if isinstance(e, NoResultFound):
        message = 'Could not find the requested item in the database.'
    elif isinstance(e, MultipleResultsFound):
        message = 'Found too many results for the requested resource.'
    elif isinstance(e, IntegrityError):
        message = 'Invalid data entered. Go back and fill out all fields.'
    else:
        message = 'Whoops, looks like something went wrong!'
    return error('500: '+type(e).__name__, message), 500


def get_user():
    r"""
    Gets the user data from the current session
    Returns the Tutor object of the current user
    """
    id = session.get('username')
    user = None
    if id:
        if app.config['DEBUG']:
            user = m.Tutors(email=id, is_active=True, is_superuser=True)
        else:
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


# ----#-   Pages
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

    today = datetime.date.today()

    sections = m.Sections.query.\
        join(m.Courses).filter(m.Courses.on_display.is_(True)).\
        join(m.Semesters).filter(
            (m.Semesters.start_date <= today) &
            (m.Semesters.end_date >= today)
        ).\
        join(m.Tickets).filter(
            m.Tickets.status.in_((None, m.Status.Open, m.Status.Claimed))
        ).\
        all()

    courses = m.Courses.query.\
        order_by(m.Courses.order_by).\
        filter(m.Courses.on_display.is_(True)).\
        options(subqueryload(m.Courses.tutors)).\
        all()

    tickets = m.Tickets.query.filter(
        m.Tickets.status.in_((None, m.Status.Open))
    ).options(
        joinedload(m.Tickets.section),
    ).order_by(m.Tickets.time_created).all()

    messages = m.Messages.query.filter(
        (
            (m.Messages.start_date < today) |
            (m.Messages.start_date.is_(None))
        ) &
        (
            (m.Messages.end_date > today) |
            (m.Messages.end_date.is_(None))
        )
    )

    for course in courses:
        course.current_sections = []
        for section in sections:
            if course == section.course:
                course.current_sections.append(section)
        course.current_tickets = sum(
            len(section.tickets) for section in course.current_sections)
        course.current_tutors = []
        for tutor in course.tutors:
            if tutor.is_working:
                course.current_tutors.append(tutor)

    html = render_template(
        'status.html',
        user=user,
        messages=messages,
        courses=courses,
        tickets=tickets,
    )
    return html


def get_open_courses():
    r"""
    Gets a list of courses and sections for the current semester
    """
    today = datetime.date.today()
    return m.Courses.query.join(m.Sections).join(m.Semesters).\
        order_by(m.Courses.number).\
        order_by(m.Sections.number).\
        filter(m.Semesters.start_date <= today).\
        filter(m.Semesters.end_date >= today).\
        all()


@app.route('/open_ticket/')
def open_ticket():
    r"""
    The student page for opening a ticket
    """
    user = get_user()

    courses = get_open_courses()
    problems = m.ProblemTypes.query.order_by(m.ProblemTypes.description).all()

    html = render_template(
        'edit_open_ticket.html',
        user=user,
        courses=courses,
        problems=problems,
    )
    return html


@app.route('/open_ticket/', methods=['POST'])
def save_open_ticket():
    r"""
    Creates a new ticket and stores it in the database
    """
    ticket_form = {
        'student_email': str,
        'student_fname': str,
        'student_lname': str,
        'section_id': get_int,
        'assignment': str,
        'question': str,
        'problem_type_id': get_int,
    }

    form = {}
    for key, value in ticket_form.items():
        form[key] = value(request.form.get(key))

    form['status'] = m.Status.Open
    form['time_created'] = datetime.datetime.now()

    ticket = m.Tickets(**form)
    db.session.add(ticket)
    db.session.commit()

    html = redirect(url_for('index'))
    flash('&#10004; Ticket successfully opened')
    return html


@app.route('/tickets/')
def view_tickets():
    r"""
    View/Claim/Close tickets
    """
    user = get_user()
    if not user:
        return redirect(url_for('login', next=url_for('view_tickets')))

    today = datetime.date.today()
    tickets = m.Tickets.query.order_by(m.Tickets.time_created).\
        join(m.Sections).\
        join(m.Semesters).\
        join(m.Courses).\
        filter(
            (m.Tickets.time_created > today) |
            (m.Tickets.time_closed > today) |
            (m.Tickets.status.in_((None, m.Status.Open, m.Status.Claimed)))
        ).\
        all()

    open = []
    claimed = []
    closed = []
    for ticket in tickets:
        if ticket.status in (None, m.Status.Open):
            open.append(ticket)
        elif ticket.status == m.Status.Claimed:
            claimed.append(ticket)
        elif ticket.status == m.Status.Closed:
            closed.append(ticket)
        else:
            raise ValueError('Invalid ticket status: {}'.format(ticket.status))

    html = render_template(
        'list_tickets.html',
        user=user,
        open=open,
        claimed=claimed,
        closed=closed,
    )
    return html


@app.route('/tickets/close/<id>')
def close_ticket(id):
    r"""
    The tutor page for claiming and closing tickets
    """
    user = get_user()
    if not user:
        return abort(403)

    ticket = m.Tickets.query.filter_by(id=id).one()
    courses = get_open_courses()
    problems = m.ProblemTypes.query.order_by(m.ProblemTypes.description).all()
    tutors = m.Tutors.query.order_by(m.Tutors.last_first).all()

    html = render_template(
        'edit_close_ticket.html',
        user=user,
        ticket=ticket,
        courses=courses,
        problems=problems,
        tutors=tutors,
    )
    return html


@app.route('/tickets/close/', methods=['POST'])
def save_close_ticket():
    r"""
    Saves changes to a ticket into the database
    """
    user = get_user()
    if not user:
        return abort(403)

    close_ticket_form = {
        'assignment': str,
        'question': str,
        'was_successful': bool,
        'tutor_id': str,
        'assistant_tutor_id': str,
        'section_id': get_int,
        'problem_type_id': get_int,
    }

    form = {}
    for key, value in close_ticket_form.items():
        form[key] = value(request.form.get(key))

    if request.form.get('submit') == 'claim':
        form['status'] = m.Status.Claimed
    elif request.form.get('submit') == 'close':
        form['status'] = m.Status.Closed
        form['time_closed'] = datetime.datetime.now()
    else:
        raise ValueError('Invalid submit type: {}'.format(form.get('submit')))

    id = get_int(request.form.get('id'))
    ticket = m.Tickets.query.filter_by(id=id).one()

    for key, value in form.items():
        if getattr(ticket, key) != value:
            setattr(ticket, key, value)
    db.session.commit()

    html = redirect(url_for('view_tickets'))
    return html


@app.route('/tickets/reopen/<id>')
def reopen_ticket(id):
    r"""
    Moves a ticket from closed to claimed
    """
    user = get_user()
    if not user:
        return abort(403)

    ticket = m.Tickets.query.filter_by(id=id).one()
    ticket.status = m.Status.Claimed
    db.session.commit()

    return redirect(url_for('view_tickets'))


# ----#-   Administration tools
def filter_report(args):
    r"""
    Filters reports by query arguments
    """
    tickets = m.Tickets.query.\
        order_by(m.Tickets.time_created.desc()).\
        join(m.Sections)

    if args.get('min_date', ''):
        min_date = date(args['min_date'])
        tickets = tickets.filter(m.Tickets.time_created >= min_date)
    if args.get('max_date', ''):
        max_date = date(args['max_date'])
        tickets = tickets.filter(m.Tickets.time_created <= max_date)

    if args.get('semester', ''):
        semester = get_int(args['semester'])
        tickets = tickets.filter(m.Sections.semester_id == semester)

    if args.get('course', ''):
        course = get_int(args['course'])
        tickets = tickets.filter(m.Sections.course_id == course)

    return tickets


@app.route('/reports/')
def reports():
    r"""
    The report page for the administrator
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    tickets = filter_report(request.args).all()
    semesters = m.Semesters.query.order_by(m.Semesters.order_by).all()
    courses = m.Courses.query.order_by(m.Courses.order_by).all()

    html = render_template(
        'report.html',
        user=user,
        tickets=tickets,
        semesters=semesters,
        courses=courses,
    )
    return html


@app.route('/report/file/')
def report_download():
    r"""
    Downloads a report as a CSV
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    tickets = filter_report(request.args).\
        join(m.ProblemTypes).\
        join(m.Courses).\
        join(m.Semesters).\
        join(m.Professors).\
        all()
    
    headers = [
        'URL',
        'Student Email',
        'Student First Name',
        'Student Last Name',
        'Assignment',
        'Question',
        'Problem Type',
        'Status',
        'Time Created',
        'Time Closed',
        'Was Successful',
        'Primary Tutor',
        'Assistant Tutor',
        'Semester',
        'Course Number',
        'Section Number',
        'Professor',
    ]
    report = [headers]
    for ticket in tickets:
        elem = [
            os.path.join('', url_for('ticket_details', id=ticket.id)),
            ticket.student_email,
            ticket.student_fname,
            ticket.student_lname,
            ticket.assignment,
            ticket.question,
            ticket.problem_type.description,
            ticket.status,
            ticket.time_created,
            ticket.time_closed,
            ticket.was_successful,
            ticket.tutor_id,
            ticket.assistant_tutor_id,
            ticket.section.semester.title,
            ticket.section.course.number,
            ticket.section.number,
            ticket.section.professor.last_first,
        ]
        report.append(elem)

    html = io.StringIO()
    writer = csv.writer(html)
    for line in report:
        writer.writerow(line)
    return html.getvalue()


@app.route('/reports/ticket/<int:id>')
def ticket_details(id):
    r"""
    Allows the administrator to view the details of a specific ticket
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    ticket = m.Tickets.query.filter_by(id=id).one()

    html = render_template(
        'ticket_details.html',
        user=user,
        ticket=ticket,
    )
    return html


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
        user=user,
    )
    return html


@app.route('/admin/semesters/', defaults={'type': m.Semesters})
@app.route('/admin/professors/', defaults={'type': m.Professors})
@app.route('/admin/courses/', defaults={'type': m.Courses})
@app.route('/admin/sections/', defaults={'type': m.Sections})
@app.route('/admin/problems/', defaults={'type': m.ProblemTypes})
@app.route('/admin/messages/', defaults={'type': m.Messages})
def list_admin(type):
    r"""
    Displays and allows editing of the available admin objects
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    title = {
        m.Semesters: 'Semesters',
        m.Professors: 'Professors',
        m.Courses: 'Courses',
        m.Sections: 'Course Sections',
        m.ProblemTypes: 'Problem Types',
        m.Messages: 'Messages',
    }.get(type)

    items = type.query.order_by(type.order_by)
    if type == m.Sections:
        items = items.join(m.Semesters).all()
        items = sorted(items, key=lambda a: a.course.number)
        items = sorted(
            items, key=lambda a: a.semester.start_date, reverse=True)
    else:
        items = items.all()

    html = render_template(
        'list_admin.html',
        user=user,
        title=title,
        type=type,
        items=items,
    )
    return html


@app.route('/admin/semesters/new', defaults={'type': m.Semesters})
@app.route('/admin/professors/new', defaults={'type': m.Professors})
@app.route('/admin/courses/new', defaults={'type': m.Courses})
@app.route('/admin/sections/new', defaults={'type': m.Sections})
@app.route('/admin/problems/new', defaults={'type': m.ProblemTypes})
@app.route('/admin/messages/new', defaults={'type': m.Messages})
@app.route('/admin/semesters/<int:id>', defaults={'type': m.Semesters})
@app.route('/admin/professors/<int:id>', defaults={'type': m.Professors})
@app.route('/admin/courses/<int:id>', defaults={'type': m.Courses})
@app.route('/admin/sections/<int:id>', defaults={'type': m.Sections})
@app.route('/admin/problems/<int:id>', defaults={'type': m.ProblemTypes})
@app.route('/admin/problems/<int:id>', defaults={'type': m.Messages})
def edit_admin(type, id=None):
    r"""
    Allows editing and creation of admin objects
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    if id is None:
        obj = None
    else:
        obj = type.query.filter_by(id=id).one()

    html = render_template(
        'edit_%s.html' % type.__tablename__,
        user=user,
        type=type,
        obj=obj,
    )
    return html


semester_form = {
    'year': get_int,
    'season': lambda a: m.Seasons(int(a)),
    'start_date': date,
    'end_date': date,
}
professor_form = {
    'fname': str,
    'lname': str,
}
course_form = {
    'number': str,
    'name': str,
    'on_display': bool,
}
section_form = {
    'number': str,
    'time': str,
    'course_id': get_int,
    'semester_id': get_int,
    'professor_id': get_int,
}
problem_form = {
    'description': str,
}
message_form = {
    'message': str,
    'start_date': date,
    'end_date': date,
}


@app.route(
    '/admin/semesters/', methods=['POST'], defaults={'type': m.Semesters})
@app.route(
    '/admin/professors/', methods=['POST'], defaults={'type': m.Professors})
@app.route(
    '/admin/courses/', methods=['POST'], defaults={'type': m.Courses})
@app.route(
    '/admin/sections/', methods=['POST'], defaults={'type': m.Sections})
@app.route(
    '/admin/problems/', methods=['POST'], defaults={'type': m.ProblemTypes})
@app.route(
    '/admin/messages/', methods=['POST'], defaults={'type': m.Messages})
def save_edit_admin(type):
    r"""
    Handles changes to administrative objects
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    if request.form.get('action') == 'delete':
        obj = type.query.filter_by(id=request.form.get('id')).one()
        db.session.delete(obj)
    else:
        form = {
            m.Semesters: semester_form,
            m.Professors: professor_form,
            m.Courses: course_form,
            m.Sections: section_form,
            m.ProblemTypes: problem_form,
            m.Messages: message_form,
        }.get(type).copy()
        for key, value in form.items():
            form[key] = value(request.form.get(key))

        id = request.form.get('id')
        if id:
            obj = type.query.filter_by(id=id).one()
            for key, value in form.items():
                if getattr(obj, key) != value:
                    setattr(obj, key, value)
        else:
            obj = type(**form)
            db.session.add(obj)
    db.session.commit()

    html = redirect(url_for('list_admin', type=type))
    return html


@app.route('/admin/tutors/')
def list_tutors():
    r"""
    Displays and allows editing of the tutors
    """
    user = get_user()
    if not user or not user.is_superuser:
        return abort(403)

    html = render_template(
        'list_tutors.html',
        user=user,
        items=m.Tutors.query.order_by(m.Tutors.last_first).all(),
    )
    return html


@app.route('/admin/tutors/new')
@app.route('/admin/tutors/<email>')
def edit_tutors(email=None):
    r"""
    Allows editing and creation of tutor objects
    """
    user = get_user()
    if not user or not (user.is_superuser or user.email == email):
        return abort(403)

    if email is None:
        tutor = None
    else:
        tutor = m.Tutors.query.filter_by(email=email).one()

    html = render_template(
        'edit_tutors.html',
        user=user,
        type=m.Tutors,
        obj=tutor,
        courses=m.Courses.query.order_by(m.Courses.number).all(),
    )
    return html


@app.route('/admin/tutors/', methods=['POST'])
def save_edit_tutors():
    r"""
    Handles changes to tutor objects
    """
    user = get_user()
    email = request.form.get('email')
    if not user or not (user.is_superuser or user.email == email):
        return abort(403)

    if request.form.get('action') == 'delete':
        obj = type.query.filter_by(email=email).one()
        db.session.delete(obj)
    else:
        form = {
            'fname': str,
            'lname': str,
            'is_working': bool,
        }
        if user.is_superuser:
            form.update({
                'is_active': bool,
                'is_superuser': bool,
            })
        for key, value in form.items():
            form[key] = value(request.form.get(key))

        if not request.form.get('new'):
            obj = m.Tutors.query.filter_by(email=email).one()
            for key, value in form.items():
                if getattr(obj, key) != value:
                    setattr(obj, key, value)
        else:
            obj = m.Tutors(email=email, **form)
            db.session.add(obj)

        for course in m.Courses.query.all():
            if request.form.get(course.number):
                if course not in obj.courses:
                    obj.courses.append(course)
            else:
                if course in obj.courses:
                    obj.courses.remove(course)

    db.session.commit()

    if user.is_superuser:
        html = redirect(url_for('list_tutors'))
    else:
        html = redirect(url_for('index'))
    return html


# ----#-   Login/Logout
@google.tokengetter
def get_google_token(token=None):
    r"""
    Returns a user's token from OAuth
    """
    return session.get('google_token')


@app.route('/login/')
def login():
    r"""
    Redirects the user to the Google/UNO Single Sign On page

    Logs the user in as 'test@unomaha.edu' in debug mode
    """
    session.clear()
    next = request.args.get('next') or request.referrer or None
    if app.config['DEBUG']:
        session['username'] = 'test@unomaha.edu'
        session['google_token'] = (None, None)
        html = redirect(next or url_for('index'))
    else:
        html = google.authorize(
            callback=url_for('oauth_authorized', next=next))
    return html


@app.route('/oauth-authorized')
def oauth_authorized():
    r"""
    Logs the user in using the OAuth API
    """
    next_url = request.args.get('next') or url_for('index')

    resp = google.authorized_response()
    if resp is None:
        return redirect(next_url)

    email = google.get('userinfo')
    email = resp.get('email')

    if m.Tutors.query.filter_by(email=email).count():
        session['google_token'] = (resp['access_token'], '')
        session['username'] = email  # ???

    return redirect(next_url)


@app.route('/logout/')
def logout():
    r"""
    Logs the user out and returns them to the homepage
    """
    session.clear()
    html = redirect(url_for('index'))
    return html
# ----#-   End App


def main():
    port = 80  # default port
    parser = argparse.ArgumentParser(
        description='Tutoring Portal Server',
        epilog='The server runs locally on port %d if PORT is not specified.'
        % port)
    parser.add_argument(
        '-p, --port', dest='port', type=int,
        help='The port where the server will run')
    parser.add_argument(
        '-d, --database', dest='database', default=':memory:',
        help='The database to be accessed')
    parser.add_argument(
        '-t, --type', dest='type', default='sqlite',
        help='The type of database engine to be used')
    parser.add_argument(
        '--debug', dest='debug', action='store_true',
        help='run the server in debug mode')
    parser.add_argument(
        '--reload', dest='reload', action='store_true',
        help='reload on source update without restarting server (also debug)')
    args = parser.parse_args()
    if args.reload:
        args.debug = True

    if args.port is None:  # Private System
        args.port = port
        host = '127.0.0.1'
    else:  # Public System
        host = '0.0.0.0'

    create_app(args)

    app.run(
        host=host,
        port=args.port,
        debug=args.debug,
        use_reloader=args.reload,
    )

if __name__ == '__main__':
    main()
