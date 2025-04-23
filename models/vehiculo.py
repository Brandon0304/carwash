from app import db
from datetime import datetime


class Cliente(db.Model):
    __tablename__ = 'clientes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120))
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

    # Relación con vehículos
    vehiculos = db.relationship('Vehiculo', backref='cliente', lazy='dynamic')

    def __repr__(self):
        return f'<Cliente {self.nombre} - Tel: {self.telefono}>'


class Vehiculo(db.Model):
    __tablename__ = 'vehiculos'

    id = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(20), unique=True, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # auto, camioneta, motocicleta, etc.
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    color = db.Column(db.String(30))
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

    # Relación con servicios
    servicios = db.relationship('Servicio', backref='vehiculo', lazy='dynamic')

    def __repr__(self):
        return f'<Vehiculo {self.placa} - {self.marca} {self.modelo}>'