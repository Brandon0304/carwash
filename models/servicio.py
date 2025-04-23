from app import db
from datetime import datetime


class TipoServicio(db.Model):
    __tablename__ = 'tipos_servicio'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255))
    precio = db.Column(db.Float, nullable=False)
    tiempo_estimado = db.Column(db.Integer)  # Tiempo estimado en minutos
    tipo_vehiculo = db.Column(db.String(20), nullable=False)  # auto, camioneta, etc.
    activo = db.Column(db.Boolean, default=True)

    # Relación con servicios
    servicios = db.relationship('Servicio', backref='tipo_servicio', lazy='dynamic')

    def __repr__(self):
        return f'<TipoServicio {self.nombre} - {self.precio}>'


class Servicio(db.Model):
    __tablename__ = 'servicios'

    id = db.Column(db.Integer, primary_key=True)
    vehiculo_id = db.Column(db.Integer, db.ForeignKey('vehiculos.id'), nullable=False)
    tipo_servicio_id = db.Column(db.Integer, db.ForeignKey('tipos_servicio.id'), nullable=False)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False)
    fecha_entrada = db.Column(db.DateTime, default=datetime.now, nullable=False)
    fecha_salida = db.Column(db.DateTime)
    precio = db.Column(db.Float, nullable=False)
    observaciones = db.Column(db.Text)

    # Relación con insumos utilizados
    insumos = db.relationship('InsumoServicio', backref='servicio', lazy='dynamic')

    def __repr__(self):
        return f'<Servicio {self.id} - Vehículo: {self.vehiculo.placa}>'

    @property
    def completado(self):
        return self.fecha_salida is not None

    @property
    def duracion(self):
        if self.fecha_salida:
            return (self.fecha_salida - self.fecha_entrada).total_seconds() / 60  # Duración en minutos
        return None


class InsumoServicio(db.Model):
    __tablename__ = 'insumos_servicio'

    id = db.Column(db.Integer, primary_key=True)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False)
    insumo_id = db.Column(db.Integer, db.ForeignKey('insumos.id'), nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

    # Relación con el insumo
    insumo = db.relationship('Insumo')

    def __repr__(self):
        return f'<InsumoServicio - Servicio: {self.servicio_id}, Insumo: {self.insumo.nombre}, Cantidad: {self.cantidad}>'