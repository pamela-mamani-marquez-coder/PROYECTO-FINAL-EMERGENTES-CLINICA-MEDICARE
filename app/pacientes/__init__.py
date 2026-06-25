from flask import Blueprint

bp_paciente = Blueprint('paciente', __name__)

from app.pacientes import routes