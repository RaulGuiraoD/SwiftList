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

document.addEventListener('DOMContentLoaded', function() {
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
});


let editMode = false;

function toggleEditMode() {
    editMode = !editMode;
    const isEditing = editMode;
    
    document.getElementById('selectionTools').classList.toggle('d-none', !isEditing);
    document.getElementById('floatingDeleteBar').classList.toggle('d-none', !isEditing);
    
    const btn = document.getElementById('btnEditMode');
    btn.innerHTML = isEditing ? 
        '<i class="bi bi-x-lg me-1 text-danger"></i> Cancelar' : 
        '<i class="bi bi-pencil-square me-1 text-primary"></i> Seleccionar productos';

    document.querySelectorAll('.check-container').forEach(el => el.classList.toggle('d-none', !isEditing));
    document.querySelectorAll('.individual-delete').forEach(el => el.classList.toggle('d-none', isEditing));
    
    if (!isEditing) {
        document.getElementById('selectAll').checked = false;
        toggleAll(document.getElementById('selectAll'));
    }
}

function handleItemClick(event, element) {
    if (!editMode) return;
    
    // Evitamos que se dispare si el clic fue directamente en el checkbox
    if (event.target.type !== 'checkbox') {
        const cb = element.querySelector('.producto-checkbox');
        cb.checked = !cb.checked;
        updateCount();
    }
}

function toggleAll(source) {
    const checkboxes = document.querySelectorAll('.producto-checkbox');
    checkboxes.forEach(cb => cb.checked = source.checked);
    updateCount();
}

function updateCount() {
    const checkedCount = document.querySelectorAll('.producto-checkbox:checked').length;
    document.getElementById('countSelected').innerText = checkedCount;
    document.querySelector('#floatingDeleteBar button').disabled = (checkedCount === 0);
    
    // Resaltar visualmente la fila seleccionada
    document.querySelectorAll('.item-maestro').forEach(item => {
        const cb = item.querySelector('.producto-checkbox');
        if (cb.checked) {
            item.style.backgroundColor = 'rgba(13, 110, 253, 0.05)';
        } else {
            item.style.backgroundColor = 'transparent';
        }
    });
}

function showDeleteModal() {
    const checkedCount = document.querySelectorAll('.producto-checkbox:checked').length;
    document.getElementById('modalCount').innerText = checkedCount;
    const modal = new bootstrap.Modal(document.getElementById('modalConfirmMultiple'));
    modal.show();
}

function submitMultipleDelete() {
    document.getElementById('formDeleteMultiple').submit();
}