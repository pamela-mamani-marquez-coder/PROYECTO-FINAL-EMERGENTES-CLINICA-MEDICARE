from app.extensions import db
from datetime import datetime

class Paciente(db.Model):
    __tablename__ = 'pacientes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True)
    ci = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date)
    genero = db.Column(db.String(10))
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    email = db.Column(db.String(120))
    seguro_medico = db.Column(db.String(100))
    alergias = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones 
    usuario = db.relationship('Usuario', back_populates='paciente', uselist=False)
    citas = db.relationship('Cita', back_populates='paciente')
    historial = db.relationship('HistorialClinico', back_populates='paciente')
    
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    def __repr__(self):
        return f'<Paciente {self.nombre_completo()}>'