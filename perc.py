# all the imports
from datetime import datetime
from flask import Flask, render_template, session, redirect, url_for, flash, \
    request
from flask_script import Manager, Shell
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField, DateField
from wtforms.validators import DataRequired
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, SmallInteger, \
    String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_login import LoginManager, UserMixin, login_user, logout_user, \
    login_required

app = Flask(__name__)  # create the application instance
app.config.from_pyfile('config.py')  # load the config from config.py

manager = Manager(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
lm = LoginManager(app)
lm.login_view = 'login'


class Annotation(db.Model):
    __tablename__ = 'annotations'

    annotation_guid = db.Column(db.String(32), primary_key=True)
    reading_guid = db.Column(db.ForeignKey('readings.reading_guid'), nullable=False)
    annotation = db.Column(db.Text)

    reading = db.relationship('Reading', primaryjoin='Annotation.reading_guid == Reading.reading_guid',
                              backref='annotations')


class Asset(db.Model):
    __tablename__ = 'assets'
    __table_args__ = (
        db.CheckConstraint("(model)::text <> ''::text"),
        db.CheckConstraint("(serial)::text <> ''::text"),
        db.UniqueConstraint('model', 'serial')
    )

    asset_guid = db.Column(db.String(32), primary_key=True)
    asset_type = db.Column(db.SmallInteger, nullable=False)
    model = db.Column(db.String(32), nullable=False)
    serial = db.Column(db.String(32), nullable=False)
    active = db.Column(db.Boolean)
    deleted = db.Column(db.Boolean)
    asset_password = db.Column(db.String(20))
    notes = db.Column(db.Text)


class LicenseInUse(db.Model):
    __tablename__ = 'license_in_use'

    license_in_use_guid = db.Column(db.String(32), primary_key=True)
    computer_name = db.Column(db.Text, nullable=False)
    user_guid = db.Column(db.ForeignKey('users.user_guid'), nullable=False)
    license_guid = db.Column(db.ForeignKey('licenses.license_guid'), nullable=False)
    time_stamp = db.Column(db.DateTime, nullable=False)

    license = db.relationship('License', primaryjoin='LicenseInUse.license_guid == License.license_guid',
                              backref='license_in_uses')
    user = db.relationship('User', primaryjoin='LicenseInUse.user_guid == User.user_guid', backref='license_in_uses')


class License(db.Model):
    __tablename__ = 'licenses'

    license_guid = db.Column(db.String(32), primary_key=True)
    license_type = db.Column(db.SmallInteger, nullable=False)
    license_serial = db.Column(db.String(20))
    version = db.Column(db.String(20))
    date_applied = db.Column(db.DateTime, nullable=False)
    logins_remaining = db.Column(db.Integer)
    license_id = db.Column(db.Text, nullable=False)
    deleted = db.Column(db.Boolean)


class Location(db.Model):
    __tablename__ = 'locations'
    __table_args__ = (
        db.CheckConstraint("(location_name)::text <> ''::text"),
    )

    location_guid = db.Column(db.String(32), primary_key=True)
    location_name = db.Column(db.String(20), nullable=False, unique=True)
    active = db.Column(db.Boolean)
    deleted = db.Column(db.Boolean)
    notes = db.Column(db.Text)

    def __repr__(self):
        return '<Location {0!s}>'.format(self.location_name)


class LogSession(db.Model):
    __tablename__ = 'log_sessions'

    log_session_guid = db.Column(db.String(32), primary_key=True)
    session_start = db.Column(db.DateTime, nullable=False)
    session_end = db.Column(db.DateTime)
    logging_interval = db.Column(db.Integer, nullable=False)
    logger_guid = db.Column(db.ForeignKey('assets.asset_guid'), nullable=False)
    user_guid = db.Column(db.ForeignKey('users.user_guid'), nullable=False)
    session_type = db.Column(db.SmallInteger, nullable=False)
    computer_name = db.Column(db.Text, nullable=False)

    asset = db.relationship('Asset', primaryjoin='LogSession.logger_guid == Asset.asset_guid', backref='log_sessions')
    user = db.relationship('User', primaryjoin='LogSession.user_guid == User.user_guid', backref='log_sessions')


class Reading(db.Model):
    __tablename__ = 'readings'

    reading_guid = db.Column(db.String(32), primary_key=True)
    reading = db.Column(db.Float(53), nullable=False)
    reading_type = db.Column(db.SmallInteger, nullable=False)
    time_stamp = db.Column(db.DateTime, nullable=False)
    log_session_guid = db.Column(db.ForeignKey('log_sessions.log_session_guid'), nullable=False)
    sensor_guid = db.Column(db.ForeignKey('assets.asset_guid'), nullable=False)
    location_guid = db.Column(db.ForeignKey('locations.location_guid'), nullable=False)
    channel = db.Column(db.SmallInteger, nullable=False)
    max_alarm = db.Column(db.Boolean)
    max_alarm_value = db.Column(db.Float(53))
    min_alarm = db.Column(db.Boolean)
    min_alarm_value = db.Column(db.Float(53))
    compromised = db.Column(db.Boolean)

    location = db.relationship('Location', primaryjoin='Reading.location_guid == Location.location_guid',
                               backref='readings')
    log_session = db.relationship('LogSession', primaryjoin='Reading.log_session_guid == LogSession.log_session_guid',
                                  backref='readings')
    asset = db.relationship('Asset', primaryjoin='Reading.sensor_guid == Asset.asset_guid', backref='readings')


class SensorParameter(db.Model):
    __tablename__ = 'sensor_parameters'

    log_session_guid = db.Column(db.ForeignKey('log_sessions.log_session_guid'), primary_key=True, nullable=False)
    channel = db.Column(db.SmallInteger, primary_key=True, nullable=False)
    parameter_name = db.Column(db.String(128), primary_key=True, nullable=False)
    parameter_value = db.Column(db.String(128), nullable=False)

    log_session = db.relationship('LogSession',
                                  primaryjoin='SensorParameter.log_session_guid == LogSession.log_session_guid',
                                  backref='sensor_parameters')


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        db.CheckConstraint("(login_name)::text <> ''::text"),
    )

    @property
    def id(self):
        """Return an identifier."""
        return self.user_guid

    user_guid = db.Column(db.String(32), primary_key=True)
    login_name = db.Column(db.String(32), nullable=False, unique=True)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    user_password = db.Column(db.String(64))
    user_group = db.Column(db.SmallInteger)
    permissions = db.Column(db.BigInteger)
    active = db.Column(db.Boolean)
    deleted = db.Column(db.Boolean)
    change = db.Column(db.Boolean)
    notes = db.Column(db.Text)


class Version(db.Model):
    __tablename__ = 'versions'

    db_version = db.Column(db.String(20), primary_key=True)
    client_version = db.Column(db.String(20))


class NameForm(FlaskForm):
    name = StringField('Username: ', validators=[DataRequired()])
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Save Credentials')
    submit = SubmitField('Submit')


class CriteriaForm(FlaskForm):
    location = SelectField(label='Location', coerce=int)
    start_date = DateField('<b>Start Date</b> e.g. 2017-03-26',
                           validators=[DataRequired()])
    end_date = DateField('<b>End Date</b> e.g. 2017-03-28',
                         validators=[DataRequired()])
    submit = SubmitField()


def pop_loc(form):
    locations = db.session.query(Location).all()
    loc_choices = [loc.location_name for loc in locations]
    loc_names = list(enumerate(loc_choices))
    form.location.choices = loc_names


def make_shell_context():
    return dict(app=app, db=db, Location=Location, Reading=Reading)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@lm.user_loader
def load_user(id):
    return User.query.get(id)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(login_name=form.name.data).first()
        if user is None:
            flash('Not Authorized.')
        else:
            session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('index.html', form=form,
                           name=session.get('name'),
                           current_time=datetime.utcnow())


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(login_name=form.username.data).first()
        if user is None or form.password.data != 'LogWare':
            flash('Not Authorized.')
            return redirect(url_for('login', **request.args))
        login_user(user, form.remember_me.data)
        return redirect(request.args.get('next') or url_for('index'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    form = CriteriaForm()
    pop_loc(form)
    if request.method == 'POST' and form.validate():
        return redirect(url_for('results', symbol=request.form['symbol'],
                                trend1=request.form['trend1'],
                                trend2=request.form['trend2']))
    return render_template('report.html', form=form)


if __name__ == '__main__':
    manager.run()
