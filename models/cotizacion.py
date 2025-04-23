from app import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property


class Proveedor(db.Model):
    __tablename__ = 'proveedores'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    empresa = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

    # Relación con cotizaciones
    cotizaciones = db.relationship('Cotizacion', backref='proveedor', lazy='dynamic')

    def __repr__(self):
        return f'<Proveedor {self.nombre}>'


class Producto(db.Model):
    __tablename__ = 'productos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255))
    unidad = db.Column(db.String(20), nullable=False)
    publicado = db.Column(db.Boolean, default=False)  # Si está disponible para cotizar
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

    # Relación con cotizaciones
    cotizaciones = db.relationship('Cotizacion', backref='producto', lazy='dynamic')

    def __repr__(self):
        return f'<Producto {self.nombre}>'


class Cotizacion(db.Model):
    __tablename__ = 'cotizaciones'

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    comentario = db.Column(db.Text)
    fecha_cotizacion = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Cotizacion de {self.proveedor.nombre} para {self.producto.nombre}: ${self.precio}>'