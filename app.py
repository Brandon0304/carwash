from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import os
import base64
import json
import time
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Importar modelos después de inicializar db
from models.empleado import Empleado
from models.insumo import Insumo
from models.servicio import Servicio, TipoServicio, InsumoServicio
from models.vehiculo import Vehiculo, Cliente
from models.evaluacion import Evaluacion
from models.cotizacion import Proveedor, Producto, Cotizacion

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return Empleado.query.get(int(user_id))


# Rutas para el dashboard principal
@app.route('/')
@login_required
def index():
    # RF004 - Listado de servicios pendientes
    servicios_pendientes = Servicio.query.filter_by(fecha_salida=None).all()

    # RF009 - Carga de trabajo por empleado
    empleados = Empleado.query.filter_by(activo=True).all()
    carga_trabajo = []

    for empleado in empleados:
        num_servicios = Servicio.query.filter_by(empleado_id=empleado.id, fecha_salida=None).count()
        carga_trabajo.append({
            'empleado': empleado,
            'num_servicios': num_servicios
        })

    # RF008 - Insumos con stock bajo
    insumos_bajos = Insumo.query.filter(Insumo.cantidad <= Insumo.stock_minimo).all()

    return render_template('dashboard.html',
                           servicios_pendientes=servicios_pendientes,
                           carga_trabajo=carga_trabajo,
                           insumos_bajos=insumos_bajos)


# RF001 - Registro de vehículos
@app.route('/vehiculos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_vehiculo():
    if request.method == 'POST':
        # Verificar si el cliente ya existe
        cliente = Cliente.query.filter_by(telefono=request.form['telefono']).first()

        if not cliente:
            cliente = Cliente(
                nombre=request.form['nombre'],
                telefono=request.form['telefono'],
                email=request.form.get('email', '')
            )
            db.session.add(cliente)
            db.session.flush()

        # Crear el vehículo
        vehiculo = Vehiculo(
            placa=request.form['placa'].upper(),
            tipo=request.form['tipo'],
            marca=request.form['marca'],
            modelo=request.form['modelo'],
            color=request.form['color'],
            cliente_id=cliente.id
        )

        db.session.add(vehiculo)
        db.session.commit()

        flash('Vehículo registrado correctamente')
        return redirect(url_for('nuevo_servicio', vehiculo_id=vehiculo.id))

    return render_template('vehiculos/form.html')


# RF002 - Asignación de servicios
@app.route('/servicios/nuevo/<int:vehiculo_id>', methods=['GET', 'POST'])
@login_required
def nuevo_servicio(vehiculo_id):
    vehiculo = Vehiculo.query.get_or_404(vehiculo_id)
    tipos_servicio = TipoServicio.query.filter_by(tipo_vehiculo=vehiculo.tipo).all()

    if request.method == 'POST':
        tipo_servicio_id = request.form['tipo_servicio_id']
        tipo_servicio = TipoServicio.query.get(tipo_servicio_id)

        servicio = Servicio(
            vehiculo_id=vehiculo.id,
            tipo_servicio_id=tipo_servicio_id,
            empleado_id=current_user.id,
            fecha_entrada=datetime.now(),
            precio=tipo_servicio.precio,
            observaciones=request.form.get('observaciones', '')
        )

        db.session.add(servicio)
        db.session.commit()

        flash('Servicio asignado correctamente')
        return redirect(url_for('index'))

    return render_template('vehiculos/servicio_form.html', vehiculo=vehiculo, tipos_servicio=tipos_servicio)


# RF003 - Registro de insumos utilizados
@app.route('/servicios/<int:servicio_id>/insumos', methods=['GET', 'POST'])
@login_required
def insumos_servicio(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)
    insumos = Insumo.query.filter_by(activo=True).all()

    if request.method == 'POST':
        insumo_id = request.form['insumo_id']
        cantidad = float(request.form['cantidad'])

        insumo = Insumo.query.get(insumo_id)

        if insumo.cantidad < cantidad:
            flash('No hay suficiente stock de este insumo')
            return redirect(url_for('insumos_servicio', servicio_id=servicio_id))

        # Registrar insumo usado
        insumo_servicio = InsumoServicio(
            servicio_id=servicio_id,
            insumo_id=insumo_id,
            cantidad=cantidad
        )

        # Actualizar stock
        insumo.cantidad -= cantidad

        db.session.add(insumo_servicio)
        db.session.commit()

        flash('Insumo registrado correctamente')
        return redirect(url_for('insumos_servicio', servicio_id=servicio_id))

    insumos_usados = InsumoServicio.query.filter_by(servicio_id=servicio_id).all()
    return render_template('servicios/insumos.html', servicio=servicio, insumos=insumos, insumos_usados=insumos_usados)


# RF004 - Listado de servicios pendientes
@app.route('/servicios/pendientes')
@login_required
def servicios_pendientes():
    try:
        # Agregar la fecha actual para calcular el tiempo transcurrido
        now = datetime.now()
        servicios = Servicio.query.filter_by(fecha_salida=None).order_by(Servicio.fecha_entrada).all()
        return render_template('servicios/pendientes.html', servicios=servicios, now=now)
    except Exception as e:
        # Imprimir el error para depuración
        print(f"Error en servicios_pendientes: {str(e)}")
        # Puedes devolver una página de error personalizada
        return render_template('error.html', error=str(e)), 500


# RF005 - Historial de servicios
@app.route('/vehiculos/historial', methods=['GET', 'POST'])
@login_required
def historial_vehiculo():
    if request.method == 'POST':
        placa = request.form['placa'].upper()
        vehiculo = Vehiculo.query.filter_by(placa=placa).first()

        if not vehiculo:
            flash('No se encontró un vehículo con esa placa')
            return redirect(url_for('historial_vehiculo'))

        servicios = Servicio.query.filter_by(vehiculo_id=vehiculo.id).order_by(Servicio.fecha_entrada.desc()).all()
        return render_template('vehiculos/historial.html', vehiculo=vehiculo, servicios=servicios)

    return render_template('vehiculos/buscar_historial.html')


# RF006 - Cálculo de tiempo promedio por tipo de lavado
@app.route('/reportes/tiempos')
@login_required
def reporte_tiempos():
    # Obtener servicios completados (con fecha de salida)
    servicios = Servicio.query.filter(Servicio.fecha_salida.isnot(None)).all()

    # Calcular tiempos promedio por tipo de servicio
    tiempos_promedio = {}
    for servicio in servicios:
        tipo_servicio = servicio.tipo_servicio.nombre
        tiempo = (servicio.fecha_salida - servicio.fecha_entrada).total_seconds() / 60  # Tiempo en minutos

        if tipo_servicio in tiempos_promedio:
            tiempos_promedio[tipo_servicio]['total'] += tiempo
            tiempos_promedio[tipo_servicio]['count'] += 1
        else:
            tiempos_promedio[tipo_servicio] = {'total': tiempo, 'count': 1}

    for tipo, datos in tiempos_promedio.items():
        tiempos_promedio[tipo]['promedio'] = datos['total'] / datos['count']

    return render_template('reportes/tiempos.html', tiempos_promedio=tiempos_promedio)


# RF007 - Reporte de ingresos diarios
@app.route('/reportes/ingresos', methods=['GET', 'POST'])
@login_required
def reporte_ingresos():
    if request.method == 'POST':
        fecha_str = request.form['fecha']
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
    else:
        fecha = datetime.now().date()

    # Obtener servicios completados del día
    inicio_dia = datetime.combine(fecha, datetime.min.time())
    fin_dia = datetime.combine(fecha, datetime.max.time())

    servicios = Servicio.query.filter(
        Servicio.fecha_salida.isnot(None),
        Servicio.fecha_salida >= inicio_dia,
        Servicio.fecha_salida <= fin_dia
    ).all()

    # Calcular ingresos
    total_ingresos = sum(servicio.precio for servicio in servicios)

    return render_template('reportes/ingresos.html',
                           fecha=fecha,
                           servicios=servicios,
                           total_ingresos=total_ingresos)


# RF008 - Identificación de insumos con stock bajo
@app.route('/insumos/stock-bajo')
@login_required
def insumos_stock_bajo():
    insumos = Insumo.query.filter(Insumo.cantidad <= Insumo.stock_minimo).all()
    return render_template('insumos/stock_bajo.html', insumos=insumos)


# RF009 - Carga de trabajo por empleado
@app.route('/reportes/carga-trabajo')
@login_required
def carga_trabajo():
    empleados = Empleado.query.filter_by(activo=True).all()
    carga = []

    for empleado in empleados:
        servicios = Servicio.query.filter_by(empleado_id=empleado.id, fecha_salida=None).all()
        carga.append({
            'empleado': empleado,
            'servicios': servicios,
            'total': len(servicios)
        })

    return render_template('reportes/carga_trabajo.html', carga=carga)


# RF010 - Registro de empleados y turnos
@app.route('/empleados')
@login_required
def empleados():
    empleados_lista = Empleado.query.all()
    return render_template('empleados/list.html', empleados=empleados_lista)


@app.route('/empleados/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_empleado():
    if request.method == 'POST':
        empleado = Empleado(
            nombre=request.form['nombre'],
            apellido=request.form['apellido'],
            email=request.form['email'],
            telefono=request.form['telefono'],
            turno=request.form['turno'],
            activo=True,
            es_admin=bool(request.form.get('es_admin', False))
        )

        empleado.set_password(request.form['password'])

        db.session.add(empleado)
        db.session.commit()

        flash('Empleado registrado correctamente')
        return redirect(url_for('empleados'))

    return render_template('empleados/form.html')


# Finalizar servicio (entregar vehículo)
@app.route('/servicios/<int:servicio_id>/finalizar', methods=['POST'])
@login_required
def finalizar_servicio(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)
    servicio.fecha_salida = datetime.now()

    db.session.commit()

    flash('Servicio finalizado correctamente')
    return redirect(url_for('index'))


# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        empleado = Empleado.query.filter_by(email=email).first()

        if empleado is None or not empleado.check_password(password):
            flash('Email o contraseña incorrectos')
            return redirect(url_for('login'))

        login_user(empleado)
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# RQ-UF44 - Evaluación del servicio
@app.route('/evaluacion/<string:token>', methods=['GET', 'POST'])
def evaluacion_servicio(token):
    # Decodificar token para obtener servicio_id
    try:
        servicio_id = decode_token(token)
        servicio = Servicio.query.get_or_404(servicio_id)
    except:
        flash('El enlace de evaluación no es válido o ha expirado', 'danger')
        return redirect(url_for('index'))

    # Verificar que el servicio esté completado
    if not servicio.fecha_salida:
        flash('No se puede evaluar un servicio que no ha sido completado', 'warning')
        return redirect(url_for('index'))

    # Verificar si ya tiene una evaluación
    evaluacion_existente = Evaluacion.query.filter_by(servicio_id=servicio.id).first()
    if evaluacion_existente:
        flash('Este servicio ya ha sido evaluado anteriormente', 'info')
        return render_template('evaluacion/gracias.html')

    if request.method == 'POST':
        evaluacion = Evaluacion(
            servicio_id=servicio.id,
            tiempo_espera=int(request.form['tiempo_espera']),
            amabilidad=int(request.form['amabilidad']),
            calidad=int(request.form['calidad']),
            comentario=request.form.get('comentario', '')
        )

        db.session.add(evaluacion)
        db.session.commit()

        return render_template('evaluacion/gracias.html')

    return render_template('evaluacion/form.html', servicio=servicio)


# Función para generar token para evaluación
def generate_evaluation_token(servicio_id):
    # En una implementación real, usaríamos una librería como itsdangerous
    # Para este ejemplo, usamos un token simple
    data = {
        'servicio_id': servicio_id,
        'exp': int(time.time()) + 7 * 24 * 3600  # 7 días de expiración
    }

    token = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
    return token


# Función para decodificar token de evaluación
def decode_token(token):
    import base64
    import json
    import time

    try:
        data = json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        if data['exp'] < int(time.time()):
            raise ValueError("Token expired")
        return data['servicio_id']
    except:
        raise ValueError("Invalid token")


# Ruta para enviar enlace de evaluación
@app.route('/servicios/<int:servicio_id>/enviar-evaluacion', methods=['POST'])
@login_required
def enviar_evaluacion(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)

    if not servicio.fecha_salida:
        flash('No se puede enviar evaluación para un servicio no completado', 'warning')
        return redirect(url_for('index'))

    # Generar token y construir URL
    token = generate_evaluation_token(servicio.id)
    url = url_for('evaluacion_servicio', token=token, _external=True)

    # En una implementación real, enviaríamos el enlace por email o SMS
    # Para este ejemplo, simplemente mostramos la URL
    flash(f'Enlace de evaluación generado: {url}', 'success')

    return redirect(url_for('historial_vehiculo'))


# RQ-UF45 - Módulo de cotización de productos
@app.route('/proveedores/registro', methods=['GET', 'POST'])
def registro_proveedor():
    if request.method == 'POST':
        # Verificar si el proveedor ya existe
        proveedor = Proveedor.query.filter_by(email=request.form['email']).first()

        if proveedor:
            flash('Ya existe un proveedor con este email', 'warning')
            return redirect(url_for('login_proveedor'))

        # Crear nuevo proveedor
        proveedor = Proveedor(
            nombre=request.form['nombre'],
            email=request.form['email'],
            telefono=request.form['telefono'],
            empresa=request.form.get('empresa', '')
        )

        db.session.add(proveedor)
        db.session.commit()

        flash('Registro completado correctamente. Ahora puede iniciar sesión.', 'success')
        return redirect(url_for('login_proveedor'))

    return render_template('proveedores/registro.html')


@app.route('/proveedores/login', methods=['GET', 'POST'])
def login_proveedor():
    if request.method == 'POST':
        email = request.form['email']
        proveedor = Proveedor.query.filter_by(email=email).first()

        if not proveedor or not proveedor.activo:
            flash('Email no registrado o cuenta inactiva', 'danger')
            return redirect(url_for('login_proveedor'))

        # En una implementación real, verificaríamos la contraseña
        # Para este ejemplo simplificado, solo validamos el email

        # Guardar ID de proveedor en sesión
        session['proveedor_id'] = proveedor.id

        return redirect(url_for('cotizaciones_proveedor'))

    return render_template('proveedores/login.html')


@app.route('/proveedores/cotizaciones')
def cotizaciones_proveedor():
    # Verificar si hay proveedor en sesión
    if 'proveedor_id' not in session:
        flash('Debe iniciar sesión para acceder', 'warning')
        return redirect(url_for('login_proveedor'))

    proveedor_id = session['proveedor_id']
    proveedor = Proveedor.query.get_or_404(proveedor_id)

    # Obtener productos publicados para cotizar
    productos = Producto.query.filter_by(publicado=True, activo=True).all()

    # Obtener cotizaciones previas del proveedor
    cotizaciones = Cotizacion.query.filter_by(proveedor_id=proveedor_id).all()

    return render_template('proveedores/cotizaciones.html',
                           proveedor=proveedor,
                           productos=productos,
                           cotizaciones=cotizaciones)


@app.route('/proveedores/cotizar/<int:producto_id>', methods=['POST'])
def cotizar_producto(producto_id):
    # Verificar si hay proveedor en sesión
    if 'proveedor_id' not in session:
        flash('Debe iniciar sesión para acceder', 'warning')
        return redirect(url_for('login_proveedor'))

    proveedor_id = session['proveedor_id']
    producto = Producto.query.get_or_404(producto_id)

    if not producto.publicado or not producto.activo:
        flash('Este producto no está disponible para cotizar', 'warning')
        return redirect(url_for('cotizaciones_proveedor'))

    # Verificar si ya existe una cotización previa
    cotizacion_existente = Cotizacion.query.filter_by(
        producto_id=producto_id,
        proveedor_id=proveedor_id
    ).first()

    if cotizacion_existente:
        # Actualizar cotización existente
        cotizacion_existente.precio = float(request.form['precio'])
        cotizacion_existente.comentario = request.form.get('comentario', '')
        cotizacion_existente.fecha_cotizacion = datetime.now()

        db.session.commit()
        flash('Cotización actualizada correctamente', 'success')
    else:
        # Crear nueva cotización
        cotizacion = Cotizacion(
            producto_id=producto_id,
            proveedor_id=proveedor_id,
            precio=float(request.form['precio']),
            comentario=request.form.get('comentario', '')
        )

        db.session.add(cotizacion)
        db.session.commit()
        flash('Cotización registrada correctamente', 'success')

    return redirect(url_for('cotizaciones_proveedor'))


@app.route('/proveedores/logout')
def logout_proveedor():
    session.pop('proveedor_id', None)
    flash('Ha cerrado sesión correctamente', 'success')
    return redirect(url_for('login_proveedor'))


# Rutas para administrador (gestión de productos)
@app.route('/admin/productos')
@login_required
def admin_productos():
    if not current_user.es_admin:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('index'))

    productos = Producto.query.all()
    return render_template('admin/productos.html', productos=productos)


@app.route('/admin/productos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_producto():
    if not current_user.es_admin:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        producto = Producto(
            nombre=request.form['nombre'],
            descripcion=request.form.get('descripcion', ''),
            unidad=request.form['unidad'],
            publicado=bool(request.form.get('publicado', False))
        )

        db.session.add(producto)
        db.session.commit()

        flash('Producto agregado correctamente', 'success')
        return redirect(url_for('admin_productos'))

    return render_template('admin/producto_form.html')


@app.route('/admin/productos/<int:producto_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_producto(producto_id):
    if not current_user.es_admin:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('index'))

    producto = Producto.query.get_or_404(producto_id)

    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form.get('descripcion', '')
        producto.unidad = request.form['unidad']
        producto.publicado = bool(request.form.get('publicado', False))

        db.session.commit()

        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('admin_productos'))

    return render_template('admin/producto_form.html', producto=producto)


@app.route('/admin/cotizaciones')
@login_required
def admin_cotizaciones():
    if not current_user.es_admin:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('index'))

    # Agrupar cotizaciones por producto para comparar precios
    productos = Producto.query.filter_by(activo=True).all()
    cotizaciones_por_producto = {}

    for producto in productos:
        cotizaciones = Cotizacion.query.filter_by(producto_id=producto.id).order_by(Cotizacion.precio).all()
        if cotizaciones:
            cotizaciones_por_producto[producto] = cotizaciones

    return render_template('admin/cotizaciones.html',
                           cotizaciones_por_producto=cotizaciones_por_producto)


# Ruta para ver reporte de evaluaciones de servicio
@app.route('/admin/evaluaciones')
@login_required
def admin_evaluaciones():
    if not current_user.es_admin:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('index'))

    evaluaciones = Evaluacion.query.order_by(Evaluacion.fecha_evaluacion.desc()).all()

    # Calcular promedios generales
    if evaluaciones:
        promedio_tiempo = sum(e.tiempo_espera for e in evaluaciones) / len(evaluaciones)
        promedio_amabilidad = sum(e.amabilidad for e in evaluaciones) / len(evaluaciones)
        promedio_calidad = sum(e.calidad for e in evaluaciones) / len(evaluaciones)
        promedio_general = sum(e.promedio for e in evaluaciones) / len(evaluaciones)
    else:
        promedio_tiempo = promedio_amabilidad = promedio_calidad = promedio_general = 0

    return render_template('admin/evaluaciones.html',
                           evaluaciones=evaluaciones,
                           promedio_tiempo=promedio_tiempo,
                           promedio_amabilidad=promedio_amabilidad,
                           promedio_calidad=promedio_calidad,
                           promedio_general=promedio_general)


# Inicializar la base de datos con datos de prueba
@app.cli.command('init-db')
def init_db_command():
    # Crear tablas si no existen
    db.create_all()

    # Crear tipos de servicio si no existen
    if TipoServicio.query.count() == 0:
        tipos_servicio = [
            TipoServicio(nombre='Lavado Básico - Auto', descripcion='Lavado exterior', precio=15.00, tiempo_estimado=20,
                         tipo_vehiculo='auto'),
            TipoServicio(nombre='Lavado Completo - Auto', descripcion='Lavado exterior e interior', precio=25.00,
                         tiempo_estimado=40, tipo_vehiculo='auto'),
            TipoServicio(nombre='Lavado Premium - Auto', descripcion='Lavado exterior, interior y encerado',
                         precio=35.00,
                         tiempo_estimado=60, tipo_vehiculo='auto'),
            TipoServicio(nombre='Lavado Básico - Camioneta', descripcion='Lavado exterior', precio=20.00,
                         tiempo_estimado=30, tipo_vehiculo='camioneta'),
            TipoServicio(nombre='Lavado Completo - Camioneta', descripcion='Lavado exterior e interior', precio=30.00,
                         tiempo_estimado=50, tipo_vehiculo='camioneta'),
            TipoServicio(nombre='Lavado Premium - Camioneta', descripcion='Lavado exterior, interior y encerado',
                         precio=45.00, tiempo_estimado=70, tipo_vehiculo='camioneta'),
        ]

        for tipo in tipos_servicio:
            db.session.add(tipo)

    # Crear insumos si no existen
    if Insumo.query.count() == 0:
        insumos = [
            Insumo(nombre='Shampoo para autos', descripcion='Shampoo especial para lavado de autos', unidad='litro',
                   cantidad=20, stock_minimo=5),
            Insumo(nombre='Cera para autos', descripcion='Cera para encerado', unidad='bote', cantidad=10,
                   stock_minimo=3),
            Insumo(nombre='Limpiador de interiores', descripcion='Limpiador para interiores', unidad='litro',
                   cantidad=15,
                   stock_minimo=4),
            Insumo(nombre='Aromatizante', descripcion='Aromatizante para interiores', unidad='unidad', cantidad=30,
                   stock_minimo=10),
        ]

        for insumo in insumos:
            db.session.add(insumo)

    # Crear productos para cotización si no existen
    if Producto.query.count() == 0:
        productos = [
            Producto(nombre='Shampoo para autos', descripcion='Shampoo especial para lavado de autos', unidad='litro',
                     publicado=True),
            Producto(nombre='Cera para autos', descripcion='Cera para encerado', unidad='bote', publicado=True),
            Producto(nombre='Limpiador de interiores', descripcion='Limpiador para interiores', unidad='litro',
                     publicado=True),
            Producto(nombre='Aromatizante', descripcion='Aromatizante para interiores', unidad='unidad',
                     publicado=True),
            Producto(nombre='Toallas de microfibra', descripcion='Paquete de 5 toallas', unidad='paquete',
                     publicado=True),
            Producto(nombre='Aspiradora portátil', descripcion='Para limpieza de interiores', unidad='unidad',
                     publicado=False),
        ]

        for producto in productos:
            db.session.add(producto)

    # Crear empleado admin si no existe
    if Empleado.query.filter_by(email='admin@carwash.com').count() == 0:
        admin = Empleado(
            nombre='Admin',
            apellido='Sistema',
            email='admin@carwash.com',
            telefono='123456789',
            turno='mañana',
            activo=True,
            es_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)

    db.session.commit()
    print('Base de datos inicializada correctamente')


# Agregar menús para las nuevas funcionalidades en el layout
@app.context_processor
def inject_menu_data():
    return {
        'show_admin_menu': current_user.is_authenticated and getattr(current_user, 'es_admin', False)
    }


if __name__ == '__main__':
    app.run(debug=True)