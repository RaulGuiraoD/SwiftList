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