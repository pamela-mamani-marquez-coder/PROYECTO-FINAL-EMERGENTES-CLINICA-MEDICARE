from flask import Blueprint

bp_admin = Blueprint('admin', __name__)

from app.admin import routes