from flask import Blueprint

main = Blueprint('main', __name__)

from perc.main import views, errors
