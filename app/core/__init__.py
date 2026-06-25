from flask import Blueprint

bp_core = Blueprint('core', __name__)

from app.core import routes