from django.shortcuts import render, redirect
from .models import Producto

def lista_compra(request):
    if request.method == 'POST':
        nombre_producto = request.POST.get('nombre')
        if nombre_producto:
            Producto.objects.create(nombre=nombre_producto)
        return redirect('lista_compra')
    
    productos = Producto.objects.all()
    return render(request, 'shopping/lista.html', {'prodcutos': productos})
