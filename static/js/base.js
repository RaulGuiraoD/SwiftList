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