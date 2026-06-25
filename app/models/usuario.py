from app.extensions import db, bcrypt
from flask_login import UserMixin
from datetime import datetime

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default='paciente')
    nombres = db.Column(db.String(100))
    apellidos = db.Column(db.String(100))
    ci = db.Column(db.String(20))
    telefono = db.Column(db.String(20))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones 
    paciente = db.relationship('Paciente', back_populates='usuario', uselist=False)
    medico = db.relationship('Medico', back_populates='usuario', uselist=False)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.rol == 'admin'
    
    def is_medico(self):
        return self.rol == 'medico'
    
    def is_recepcionista(self):
        return self.rol == 'recepcionista'
    
    def is_paciente(self):
        return self.rol == 'paciente'
    
    def __repr__(self):
        return f'<Usuario {self.username} ({self.rol})>'