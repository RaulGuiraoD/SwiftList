// Función para avisos (Toasts)
function showToast(message, isError = false) {
    const toastElement = document.getElementById('liveToast');
    const toastBody = document.getElementById('toastMessage');

    toastBody.innerText = message;

    if (isError) {
        toastElement.classList.add('bg-danger-custom');
    } else {
        toastElement.classList.remove('bg-danger-custom');
    }

    const toast = new bootstrap.Toast(toastElement, { delay: 2500 });
    toast.show();
}

// Función para añadir desde sugerencias directamente
function addFromSugerencia(nombre) {
    const input = document.getElementById('inputProducto');
    input.value = nombre;
    // Opcional: enviar el formulario automáticamente al hacer clic
    document.getElementById('formAdd').submit();
    showToast("Producto añadido: " + nombre);
}

/*----------------------------------------------------------------------------------------------------------------------------**/

// Variable global para controlar el modo edición
let isEditModeActive = false;

function toggleEditMode() {
    isEditModeActive = !isEditModeActive;

    // Elementos comunes
    const selectionTools = document.getElementById('selectionTools');
    const floatingBar = document.getElementById('floatingDeleteBar');
    const btn = document.getElementById('btnEditMode');

    // Detectamos si estamos en Catálogo o Historial buscando una clase específica
    const isHistorial = document.querySelector('.item-seleccionable') !== null;

    // Toggle visibilidad herramientas
    selectionTools.classList.toggle('d-none', !isEditModeActive);
    floatingBar.classList.toggle('d-none', !isEditModeActive);

    // Cambiar texto del botón según el modo y el lugar
    if (isEditModeActive) {
        btn.innerHTML = '<i class="bi bi-x-lg me-1 text-danger"></i> Cancelar';
    } else {
        const label = isHistorial ? 'listas' : 'productos';
        btn.innerHTML = `<i class="bi bi-pencil-square me-1 text-primary"></i> Seleccionar ${label}`;
    }

    // Mostrar/Ocultar contenedores de checks y botones individuales
    document.querySelectorAll('.check-container').forEach(el => el.classList.toggle('d-none', !isEditModeActive));

    // Ocultar botones individuales (diferentes clases según la página)
    document.querySelectorAll('.individual-delete, .individual-actions').forEach(el => {
        el.classList.toggle('d-none', isEditModeActive);
    });

    // Si cancelamos, desmarcamos todo
    if (!isEditModeActive) {
        const selectAllCheck = document.getElementById('selectAll');
        if (selectAllCheck) {
            selectAllCheck.checked = false;
            toggleAll(selectAllCheck);
        }
    }
}

function handleItemClick(event, element) {
    if (!isEditModeActive) return;

    // Si el clic es en un link o botón de acción real, no hacemos nada
    if (event.target.tagName === 'A' || event.target.tagName === 'BUTTON' || event.target.closest('button')) {
        return;
    }

    // Evitamos duplicar el disparo si se hace clic justo en el checkbox
    if (event.target.type !== 'checkbox') {
        const cb = element.querySelector('.producto-checkbox, .lista-checkbox');
        if (cb) {
            cb.checked = !cb.checked;
            updateCount();
        }
    } else {
        // Si hizo clic en el checkbox directamente
        updateCount();
    }
}

function toggleAll(source) {
    const checkboxes = document.querySelectorAll('.producto-checkbox, .lista-checkbox');
    checkboxes.forEach(cb => cb.checked = source.checked);
    updateCount();
}

function updateCount() {
    const checkboxes = document.querySelectorAll('.producto-checkbox:checked, .lista-checkbox:checked');
    const checkedCount = checkboxes.length;

    const countBadge = document.getElementById('countSelected');
    const deleteBtn = document.querySelector('#floatingDeleteBar button');

    if (countBadge) countBadge.innerText = checkedCount;
    if (deleteBtn) deleteBtn.disabled = (checkedCount === 0);

    // Efectos visuales según el tipo de item
    // Para productos (Catálogo)
    document.querySelectorAll('.item-maestro').forEach(item => {
        const cb = item.querySelector('.producto-checkbox');
        item.style.backgroundColor = cb.checked ? 'rgba(13, 110, 253, 0.05)' : 'transparent';
    });

    // Para listas (Historial)
    document.querySelectorAll('.item-seleccionable').forEach(item => {
        const cb = item.querySelector('.lista-checkbox');
        if (cb) {
            item.style.transform = cb.checked ? 'scale(0.98)' : 'scale(1)';
            item.style.opacity = cb.checked ? '0.8' : '1';
        }
    });
}

function showDeleteModal() {
    const checkboxes = document.querySelectorAll('.producto-checkbox:checked, .lista-checkbox:checked');
    const checkedCount = checkboxes.length;

    const modalCountLabel = document.getElementById('modalCount');
    if (modalCountLabel) modalCountLabel.innerText = checkedCount;

    const modalElement = document.getElementById('modalConfirmMultiple');
    if (modalElement) {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    }
}

function submitMultipleDelete() {
    const form = document.getElementById('formDeleteMultiple');
    if (form) form.submit();
}

document.addEventListener('DOMContentLoaded', function () {
    let intervalId = null;
    let timeoutId = null;

    function startUpdating(button) {
        // Ejecutamos la primera vez inmediatamente
        ejecutarCambio(button);

        // Esperamos 500ms para confirmar que el usuario está "manteniendo"
        timeoutId = setTimeout(() => {
            // Si sigue manteniendo, empezamos a actualizar cada 150ms
            intervalId = setInterval(() => {
                ejecutarCambio(button);
            }, 150);
        }, 500);
    }

    function stopUpdating() {
        clearTimeout(timeoutId);
        clearInterval(intervalId);
    }

    function ejecutarCambio(button) {
        const url = button.getAttribute('data-url');
        const itemId = button.getAttribute('data-item-id');
        const spanCantidad = document.getElementById(`cantidad-${itemId}`);

        fetch(url, {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(response => response.json())
            .then(data => {
                if (data.nueva_cantidad !== undefined) {
                    spanCantidad.innerText = data.nueva_cantidad;
                    // Feedback visual sutil
                    spanCantidad.classList.add('scale-up');
                    setTimeout(() => spanCantidad.classList.remove('scale-up'), 100);
                }
            })
            .catch(error => console.error('Error:', error));
    }

    // Eventos para todos los botones de cantidad
    document.querySelectorAll('.btn-cantidad').forEach(button => {
        // Evitamos el click normal para que no se duplique con nuestra lógica
        button.addEventListener('click', (e) => e.preventDefault());

        // INICIO: Ratón y Táctil
        button.addEventListener('mousedown', () => startUpdating(button));
        button.addEventListener('touchstart', (e) => {
            e.preventDefault(); // Evita el menú contextual en móvil
            startUpdating(button);
        });

        // FIN: Ratón y Táctil (cualquier forma de soltar)
        button.addEventListener('mouseup', stopUpdating);
        button.addEventListener('mouseleave', stopUpdating);
        button.addEventListener('touchend', stopUpdating);
        button.addEventListener('touchcancel', stopUpdating);
    });

    const messageContainer = document.getElementById('messages-container');

    if (messageContainer) {
        // Espera 2 segundos (2000ms) antes de empezar a desaparecer
        setTimeout(function () {
            messageContainer.style.transition = "opacity 0.8s ease";
            messageContainer.style.opacity = "0";

            // Eliminar del DOM después de que termine la animación
            setTimeout(function () {
                messageContainer.remove();
            }, 800);
        }, 2000);
    }

    const avatarInputs = document.querySelectorAll('.avatar-input');
    const currentAvatarDisplay = document.getElementById('current-avatar');

    avatarInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.checked) {
                // Actualiza el círculo grande arriba
                if (currentAvatarDisplay) {
                    currentAvatarDisplay.innerText = this.value;
                }

                // Cambia el estilo visual del botón seleccionado
                document.querySelectorAll('.avatar-selector-btn').forEach(btn => {
                    btn.classList.remove('active-avatar');
                });
                this.parentElement.classList.add('active-avatar');
            }
        });
    });

   /* ANIMACION BARRA ESTADISTICAS */
    const bar = document.getElementById('budget-bar');
    
    if (bar) {
        // 1. Capturamos el porcentaje y limpiamos posibles comas de Django
        let pct = bar.getAttribute('data-percentage').replace(',', '.');
        
        // 2. Forzamos estado inicial (0%)
        bar.style.setProperty('width', '0%', 'important');

        // 3. Pequeño delay de cortesía para que el usuario vea la animación al entrar
        setTimeout(() => {
            bar.style.setProperty('width', pct + '%', 'important');
        }, 300);
    }

});
