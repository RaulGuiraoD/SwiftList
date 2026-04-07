from django.db import models

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    completado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        ordering = ['completado', '-fecha_creacion']