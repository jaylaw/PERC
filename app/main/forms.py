from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField, DateField
from wtforms.validators import DataRequired
from .. import db
from ..models import Location


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

    def pop_loc(self):
        locations = db.session.query(Location).all()
        loc_choices = [loc.location_name for loc in locations]
        loc_names = list(enumerate(loc_choices))
        self.location.choices = loc_names
