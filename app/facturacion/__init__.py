from flask import Blueprint

bp_factura = Blueprint('factura', __name__)

from app.facturacion import routes