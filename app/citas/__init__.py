from flask import Blueprint

bp_cita = Blueprint('cita', __name__)

from app.citas import routes