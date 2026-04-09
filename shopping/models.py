from django.db import models
from django.contrib.auth.models import User

class Tienda(models.Model):
    # Añadimos unique=True para que la base de datos no acepte repetidos
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tiendas', null=True, blank=True)
    nombre = models.CharField(max_length=100) 
    color_hex = models.CharField(max_length=7, default="#0a8f34")

    class Meta:
        unique_together = ('usuario', 'nombre')

    def __str__(self):
        return self.nombre

    # Forzamos que el nombre siempre se guarde con la primera letra en mayúscula
    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip().capitalize()
        super().save(*args, **kwargs)

class MaestroProducto(models.Model):
    """ El 'cerebro'. Aquí se guarda todo lo que ella ha comprado alguna vez. """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='productos_maestros', null=True, blank=True)
    nombre = models.CharField(max_length=200)
    tienda_habitual = models.ForeignKey(Tienda, on_delete=models.SET_NULL, null=True, blank=True)
    frecuencia_uso = models.PositiveIntegerField(default=0)
    zona = models.CharField(max_length=100, default="General")

    class Meta:
        unique_together = ('usuario', 'nombre')

    def __str__(self):
        return f"{self.nombre} ({self.zona})"

class ListaCompra(models.Model):
    """ Representa una 'sesión' de compra: 'Compra Mercadona Martes' """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listas', null=True, blank=True)
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    esta_finalizada = models.BooleanField(default=False)
    fecha_finalizada = models.DateTimeField(null=True, blank=True)
    total_ticket = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Lista {self.tienda.nombre} - {self.fecha_creacion.strftime('%d/%m/%Y')}"

class ItemLista(models.Model):
    """ Los productos específicos dentro de una lista concreta """
    lista = models.ForeignKey(ListaCompra, related_name='items', on_delete=models.CASCADE)
    producto_maestro = models.ForeignKey(MaestroProducto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1) # Ej: '2 packs', '1kg'
    comprado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.producto_maestro.nombre} en {self.lista}"