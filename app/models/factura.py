from app.extensions import db
from datetime import datetime

class Factura(db.Model):
    __tablename__ = 'facturas'
    
    id = db.Column(db.Integer, primary_key=True)
    cita_id = db.Column(db.Integer, db.ForeignKey('citas.id'))
    numero_factura = db.Column(db.String(20), unique=True)
    monto_total = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(50))
    estado_pago = db.Column(db.String(20), default='pendiente')
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_pago = db.Column(db.DateTime)
    
    #  Relación
    cita = db.relationship('Cita', back_populates='factura')