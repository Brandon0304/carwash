from app import db
from datetime import datetime


class Evaluacion(db.Model):
    __tablename__ = 'evaluaciones'

    id = db.Column(db.Integer, primary_key=True)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicios.id'), nullable=False)
    tiempo_espera = db.Column(db.Integer, nullable=False)  # Calificación de 1 a 5
    amabilidad = db.Column(db.Integer, nullable=False)  # Calificación de 1 a 5
    calidad = db.Column(db.Integer, nullable=False)  # Calificación de 1 a 5
    comentario = db.Column(db.Text)
    fecha_evaluacion = db.Column(db.DateTime, default=datetime.now)

    # Relación con el servicio
    servicio = db.relationship('Servicio', backref='evaluacion', uselist=False)

    def __repr__(self):
        return f'<Evaluacion para servicio #{self.servicio_id}>'

    @property
    def promedio(self):
        """Calcula la calificación promedio"""
        return (self.tiempo_espera + self.amabilidad + self.calidad) / 3