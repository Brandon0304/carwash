from app import db
from datetime import datetime


class Insumo(db.Model):
    __tablename__ = 'insumos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255))
    unidad = db.Column(db.String(20), nullable=False)  # litro, ml, unidad, etc.
    cantidad = db.Column(db.Float, default=0)
    stock_minimo = db.Column(db.Float, default=0)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)
    ultima_actualizacion = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<Insumo {self.nombre} - Stock: {self.cantidad} {self.unidad}>'

    @property
    def stock_bajo(self):
        return self.cantidad <= self.stock_minimo