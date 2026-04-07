from django.db import models

class Tienda(models.Model):
    # Añadimos unique=True para que la base de datos no acepte repetidos
    nombre = models.CharField(max_length=100, unique=True) 
    color_hex = models.CharField(max_length=7, default="#0a8f34")

    def __str__(self):
        return self.nombre

    # Forzamos que el nombre siempre se guarde con la primera letra en mayúscula
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().capitalize()
        super().save(*args, **kwargs)

class MaestroProducto(models.Model):
    """ El 'cerebro'. Aquí se guarda todo lo que ella ha comprado alguna vez. """
    nombre = models.CharField(max_length=200, unique=True)
    tienda_habitual = models.ForeignKey(Tienda, on_delete=models.SET_NULL, null=True, blank=True)
    frecuencia_uso = models.PositiveIntegerField(default=0)
    zona = models.CharField(max_length=100, default="General", help_text="Ej: Frutería, Carnicería, Limpieza")

    def __str__(self):
        return f"{self.nombre} ({self.zona})"

class ListaCompra(models.Model):
    """ Representa una 'sesión' de compra: 'Compra Mercadona Martes' """
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    esta_finalizada = models.BooleanField(default=False)
    total_ticket = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Lista {self.tienda.nombre} - {self.fecha_creacion.strftime('%d/%m/%Y')}"

class ItemLista(models.Model):
    """ Los productos específicos dentro de una lista concreta """
    lista = models.ForeignKey(ListaCompra, related_name='items', on_delete=models.CASCADE)
    producto_maestro = models.ForeignKey(MaestroProducto, on_delete=models.CASCADE)
    cantidad = models.CharField(max_length=50, default="1") # Ej: '2 packs', '1kg'
    comprado = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.producto_maestro.nombre} en {self.lista}"