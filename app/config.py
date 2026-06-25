import os

class Config:
    SECRET_KEY = 'dev-secret-key-12345'
    
    # Ruta a la carpeta instance (relativa)
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '..', 'instance', 'medicare.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False