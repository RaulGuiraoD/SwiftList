from django.shortcuts import render, redirect, get_object_or_404
from .models import Tienda, ListaCompra, MaestroProducto, ItemLista

def dashboard(request):
    listas_abiertas = ListaCompra.objects.filter(esta_finalizada=False).order_by('-fecha_creacion')
    tiendas = Tienda.objects.all()

    if request.method == 'POST':
        # Caso A: Añadir una tienda nueva
        if 'nombre_tienda' in request.POST:
            nombre = request.POST.get('nombre_tienda')
            color = request.POST.get('color_tienda', '#007bff')
            if nombre:
                Tienda.objects.create(nombre=nombre, color_hex=color)
            return redirect('dashboard')

        # Caso B: Crear una nueva lista de la compra
        tienda_id = request.POST.get('tienda_id')
        if tienda_id:
            tienda = get_object_or_404(Tienda, id=tienda_id)
            nueva_lista = ListaCompra.objects.create(tienda=tienda)
            return redirect('ver_lista', lista_id=nueva_lista.id)

    return render(request, 'shopping/dashboard.html', {
        'listas_abiertas': listas_abiertas,
        'tiendas': tiendas,
    })

def ver_lista(request, lista_id):
    lista = get_object_or_404(ListaCompra, id=lista_id)
    
    if request.method == 'POST':
        nombre_prod = request.POST.get('nombre').strip().capitalize()
        cantidad = request.POST.get('cantidad', '1')

        if nombre_prod:
            # 1. Buscar o crear en el Maestro (aquí es donde la app "aprende")
            producto_maestro, created = MaestroProducto.objects.get_or_create(
                nombre=nombre_prod,
                defaults={'tienda_habitual': lista.tienda}
            )
            
            # 2. Añadirlo a la lista actual
            ItemLista.objects.create(
                lista=lista,
                producto_maestro=producto_maestro,
                cantidad=cantidad
            )
        return redirect('ver_lista', lista_id=lista.id)

    # Obtenemos los items de esta lista
    items = lista.items.all().order_by('comprado', '-id')
    
    # Obtenemos todos los nombres del maestro para el autocompletado
    sugerencias = MaestroProducto.objects.all()

    return render(request, 'shopping/lista_detalle.html', {
        'lista': lista,
        'items': items,
        'sugerencias': sugerencias
    })

def completar_item(request, item_id):
    item = get_object_or_404(ItemLista, id=item_id)
    item.comprado = not item.comprado
    item.save()
    return redirect('ver_lista', lista_id=item.lista.id)

def eliminar_item(request, item_id):
    item = get_object_or_404(ItemLista, id=item_id)
    lista_id = item.lista.id
    item.delete()
    return redirect('ver_lista', lista_id=lista_id)

def finalizar_compra(request, lista_id):
    lista = get_object_or_404(ListaCompra, id=lista_id)
    
    if request.method == 'POST':
        total_raw = request.POST.get('total_ticket', '').strip()
        
        # Si el campo viene vacío, ponemos 0.00
        if not total_raw:
            lista.total_ticket = 0
        else:
            try:
                # Convertimos a float/decimal para asegurar que es un número
                lista.total_ticket = float(total_raw.replace(',', '.'))
            except ValueError:
                # Si mete texto raro por error, lo reseteamos a 0
                lista.total_ticket = 0
            
        lista.esta_finalizada = True
        lista.save()
        
        # Aumentar frecuencia de los productos comprados
        for item in lista.items.filter(comprado=True):
            producto = item.producto_maestro
            producto.frecuencia_uso += 1
            producto.save()
            
        return redirect('dashboard')
    
    return redirect('ver_lista', lista_id=lista.id)

def listas_archivadas(request):
    # Solo las que están finalizadas, de la más reciente a la más antigua
    listas = ListaCompra.objects.filter(esta_finalizada=True).order_by('-fecha_creacion')
    return render(request, 'shopping/listas_archivadas.html', {'listas': listas})

def reabrir_lista(request, lista_id):
    lista = get_object_or_404(ListaCompra, id=lista_id)
    lista.esta_finalizada = False
    # Al reabrir, reseteamos el total del ticket por si quiere cambiarlo luego
    lista.total_ticket = 0
    lista.save()
    return redirect('ver_lista', lista_id=lista.id)