from datetime import datetime
from flask import render_template, session, redirect, url_for, request, flash
from flask_login import login_required, login_user, logout_user
from . import main
from .forms import NameForm, LoginForm, CriteriaForm
from .. import db
from ..models import User


@main.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@main.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500


@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(login_name=form.name.data).first()
        if user is None:
            flash('Not Authorized.')
        else:
            session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('main.index'))
    return render_template('index.html', form=form,
                           name=session.get('name'),
                           current_time=datetime.utcnow())


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(login_name=form.username.data).first()
        if user is None or form.password.data != 'LogWare':
            flash('Not Authorized.')
            return redirect(url_for('main.login', **request.args))
        login_user(user, form.remember_me.data)
        return redirect(request.args.get('next') or url_for('main.index'))
    return render_template('login.html', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@main.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    form = CriteriaForm()
    form.pop_loc()
    if request.method == 'POST' and form.validate():
        return redirect(url_for('results', symbol=request.form['symbol'],
                                trend1=request.form['trend1'],
                                trend2=request.form['trend2']))
    return render_template('report.html', form=form)