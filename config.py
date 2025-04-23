import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Configuración de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-clave-secreta-muy-dificil-de-adivinar'

    # Configuración de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'carwash.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración para sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Carpeta para subir archivos
    UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')