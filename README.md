# 🛒 SwiftList - Tu Compra, Más Fácil que Nunca

**SwiftList** es una aplicación web *mobile-first* diseñada para transformar la experiencia de ir al supermercado. A diferencia de las notas convencionales, SwiftList aprende de tus hábitos, organiza tu ruta por el establecimiento y gestiona tus gastos de forma visual y orgánica.

![Status](https://img.shields.io/badge/Status-Finalizado-success)
![Python](https://img.shields.io/badge/Python-3.10+-2d5a27)
![Django](https://img.shields.io/badge/Framework-Django%205.0-163114)
![Design](https://img.shields.io/badge/Design-Mobile--First-fdfcf9)

---

## 🌟 ¿Qué hace especial a SwiftList?

SwiftList no es solo una lista de tareas; es un asistente de compra que evoluciona contigo.

### 🧠 Inteligencia y Rapidez
- **Catálogo Maestro Automático:** La aplicación recuerda cada producto que ingresas. Con el tiempo, genera patrones de sugerencias para que crear tu lista sea cuestión de segundos.
- **Acceso a Frecuentes:** Un panel inteligente que se actualiza solo con los productos que más compras habitualmente.
- **Predicción de Categorías:** Asigna automáticamente zonas del supermercado a tus productos para que nunca tengas que volver atrás en un pasillo.

### 📝 Experiencia en Tienda
- **Orden por Secciones:** Una vez en el súper, puedes filtrar y ordenar tu lista por zonas (Carnicería, Lácteos, Limpieza, etc.), optimizando tu recorrido.
- **Modo Tachar Inteligente:** Al marcar un producto como "en el carrito", este se desplaza visualmente al final de la lista, manteniendo el foco en lo que aún te falta.
- **Flexibilidad Total:** Permite cambiar el supermercado de destino sobre la marcha dentro de una lista activa, adaptando la experiencia si decides cambiar de planes.

### 📊 Control y Analítica
- **Historial & Re-apertura:** Revisa compras pasadas para comparar precios o reabre una lista antigua para repetirla íntegramente con un solo clic.
- **Estadísticas de Gasto:** Al finalizar, puedes registrar el importe del ticket para generar estadísticas mensuales de consumo y ahorro.
- **Gestión Masiva:** Incluye herramientas de selección múltiple para limpiar el historial o el catálogo de forma rápida y eficiente.

---

## 🎨 Identidad Visual
La aplicación utiliza una paleta de colores orgánica y cálida, diseñada para reducir el estrés de la compra diaria:
- **Verde Primario (`#2d5a27`):** Representa frescura y naturaleza.
- **Fondo Cálido (`#fcfbf6`):** Evita la fatiga visual en comparación con el blanco puro.
- **Interfaz Intuitiva:** Botones redondeados y gestos pensados para el uso con una sola mano.

---

## 🛠️ Stack Tecnológico
- **Backend:** Python & Django (ORM, Gestión de Usuarios, Lógica de Negocio).
- **Frontend:** JavaScript (ES6+), HTML5, CSS3 (Custom Properties).
- **CSS Framework:** Bootstrap 5 (Personalizado para estética orgánica).
- **Iconografía:** Bootstrap Icons.

---

## 🚀 Instalación Local

Si quieres probar SwiftList en tu propio entorno:

1. **Clonar el repositorio:**

   git clone [https://github.com/RaulGuiraoD/SwiftList.git](https://github.com/RaulGuiraoD/SwiftList.git)

2. **Instalar dependencias:**

    pip install -r requirements.txt

3. **Configurar la base de datos**

    python manage.py migrate

4. **Iniciar el servidor**

    python manage.py runserver

Accede a http://127.0.0.1:8000 desde tu navegador (o usa el modo responsive del inspector para verlo en formato móvil).
