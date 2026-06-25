from flask import Blueprint

bp_historial = Blueprint('historial', __name__)

from app.historial import routes