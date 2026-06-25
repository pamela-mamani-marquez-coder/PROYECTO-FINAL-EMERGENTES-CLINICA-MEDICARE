from flask import Blueprint

bp_recepcionista = Blueprint('recepcionista', __name__)

from app.recepcionista import routes