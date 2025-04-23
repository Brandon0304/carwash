// Cerrar automáticamente las alertas después de 5 segundos
document.addEventListener('DOMContentLoaded', function() {
    // Obtener todas las alertas con botón de cierre
    var alertList = document.querySelectorAll('.alert.alert-dismissible');

    // Configurar temporizador para cada alerta
    alertList.forEach(function(alert) {
        setTimeout(function() {
            var closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });

    // Activar todos los tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Formatear inputs de placa para convertir a mayúsculas
    var placaInputs = document.querySelectorAll('input[name="placa"]');
    placaInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            this.value = this.value.toUpperCase();
        });
    });
});

// Función para confirmar acciones importantes
function confirmarAccion(mensaje) {
    return window.confirm(mensaje);
}

// Función para formatear moneda
function formatoMoneda(valor) {
    return '$' + parseFloat(valor).toFixed(2);
}

// Función para calcular tiempo transcurrido
function tiempoTranscurrido(fechaInicio, fechaFin) {
    if (!fechaFin) {
        fechaFin = new Date();
    }

    var diferencia = Math.floor((fechaFin - fechaInicio) / 1000 / 60); // Diferencia en minutos

    if (diferencia < 60) {
        return diferencia + ' minutos';
    } else {
        var horas = Math.floor(diferencia / 60);
        var minutos = diferencia % 60;
        return horas + ' horas ' + minutos + ' minutos';
    }
}

// Función para mostrar modal de confirmación personalizado
function mostrarConfirmacion(titulo, mensaje, callbackSi, callbackNo) {
    var modalHTML = `
        <div class="modal fade" id="confirmModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${titulo}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>${mensaje}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="btnNo">No</button>
                        <button type="button" class="btn btn-primary" id="btnSi">Sí</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Crear el modal y añadirlo al DOM
    var modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHTML;
    document.body.appendChild(modalContainer);

    // Crear instancia del modal
    var modal = new bootstrap.Modal(document.getElementById('confirmModal'));

    // Configurar eventos de botones
    document.getElementById('btnSi').addEventListener('click', function() {
        modal.hide();
        if (callbackSi) callbackSi();
        setTimeout(function() {
            modalContainer.remove();
        }, 500);
    });

    document.getElementById('btnNo').addEventListener('click', function() {
        modal.hide();
        if (callbackNo) callbackNo();
        setTimeout(function() {
            modalContainer.remove();
        }, 500);
    });

    // Mostrar el modal
    modal.show();
}