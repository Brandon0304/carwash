from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from datetime import datetime


class Empleado(UserMixin, db.Model):
    __tablename__ = 'empleados'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    telefono = db.Column(db.String(20))
    turno = db.Column(db.String(20))  # mañana, tarde, noche
    activo = db.Column(db.Boolean, default=True)
    es_admin = db.Column(db.Boolean, default=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

    # Relación con servicios
    servicios = db.relationship('Servicio', backref='empleado', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Empleado {self.nombre} {self.apellido}>'