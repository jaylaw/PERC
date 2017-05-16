from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, SelectField, DateField, DecimalField
from wtforms.validators import DataRequired
from perc import db
from perc.models import Location


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Save Credentials')
    submit = SubmitField('Submit')


class ReportForm(FlaskForm):
    location = SelectField(label='Location', coerce=int)
    '''
    criteria = SelectField('Specifications',
                           choices=[('Pass a dictionary with Main lab parameters!!', 'Main Lab'),
                                    ('Pass a dictionary with Cold Room parameters!!', 'Cold Room'),
                                    ('Allow user to input custom environment parameters!!', 'Custom')])
    '''
    start_date = DateField('<b>Start Date</b> e.g. 2017-03-26',
                           validators=[DataRequired()])
    end_date = DateField('<b>End Date</b> e.g. 2017-03-28',
                         validators=[DataRequired()])
    temperature = DecimalField('Temperature', validators=[DataRequired()], default=73.00)
    temp_tol = DecimalField('Temperature', validators=[DataRequired()], default=6.00)
    humidity = DecimalField('Temperature', validators=[DataRequired()], default=50.00)
    humid_tol = DecimalField('Temperature', validators=[DataRequired()], default=20.00)
    submit = SubmitField()

    def pop_loc(self):
        locations = db.session.query(Location).all()
        loc_choices = [loc.location_name for loc in locations]
        loc_names = list(enumerate(loc_choices))
        self.location.choices = loc_names
