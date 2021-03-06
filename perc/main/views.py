from datetime import datetime
from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, login_user, logout_user
from perc.main import main
from perc.main.forms import LoginForm, ReportForm
from perc.models import User
from process import Report


@main.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@main.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


@main.route('/')
def index():
    return render_template('index.html', current_time=datetime.utcnow())


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(login_name=form.username.data).first()
        if user is None or form.password.data != 'LogWare':
            flash('Not Authorized.')
            return redirect(url_for('main.login', **request.args))
        login_user(user, form.remember_me.data)
        return redirect(request.args.get('next') or url_for('main.dashboard'))
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@main.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    form = ReportForm()
    form.pop_loc()
    if request.method == 'POST' and form.validate():
        s = Report(request.form['location'],
                   request.form['temperature'],
                   request.form['humidity'],
                   request.form['temp_tol'],
                   request.form['humid_tol'],
                   request.form['start_date'],
                   request.form['end_date'])

        return render_template('summary_report.html',
                               loc_name=s.get_location_name(),
                               start_date=s.start_date,
                               end_date=s.end_date,
                               temperature=s.temperature,
                               temp_tol=s.temperature_tolerance,
                               humidity=s.humidity,
                               humid_tol=s.humidity_tolerance,
                               report_data=s.generate_summary(),
                               current_time=datetime.utcnow())

    return render_template('report.html', form=form)
