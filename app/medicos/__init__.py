from flask import Blueprint

bp_medico = Blueprint('medico', __name__)

from app.medicos import routes