from app.extensions import db
from datetime import datetime

class Cita(db.Model):
    __tablename__ = 'citas'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'))
    medico_id = db.Column(db.Integer, db.ForeignKey('medicos.id'))
    sala_id = db.Column(db.Integer, db.ForeignKey('salas.id'))
    fecha_hora = db.Column(db.DateTime, nullable=False)
    motivo = db.Column(db.Text)
    estado = db.Column(db.String(20), default='pendiente')
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    observaciones = db.Column(db.Text)
    
    #  Relaciones 
    paciente = db.relationship('Paciente', back_populates='citas')
    medico = db.relationship('Medico', back_populates='citas')
    sala = db.relationship('Sala', back_populates='citas')
    factura = db.relationship('Factura', back_populates='cita', uselist=False)
    historial = db.relationship('HistorialClinico', back_populates='cita', uselist=False) 