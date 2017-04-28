from perc import db, lm
from flask_login import UserMixin


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


@lm.user_loader
def load_user(id):
    return User.query.get(id)