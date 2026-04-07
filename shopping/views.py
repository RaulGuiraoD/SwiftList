from django.shortcuts import render, redirect, get_object_or_404
from django.db import models 
from django.db.models import Sum, Count, Q
from django.utils import timezone
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

def estadisticas(request):
    # 1. Gasto Total Histórico
    gasto_total = ListaCompra.objects.filter(esta_finalizada=True).aggregate(Sum('total_ticket'))['total_ticket__sum'] or 0

    # 2. Gasto este mes
    mes_actual = timezone.now().month
    gasto_mes = ListaCompra.objects.filter(
        esta_finalizada=True, 
        fecha_creacion__month=mes_actual
    ).aggregate(Sum('total_ticket'))['total_ticket__sum'] or 0

    # 3. Top Productos (Los 5 más frecuentes)
    top_productos = MaestroProducto.objects.filter(frecuencia_uso__gt=0).order_by('-frecuencia_uso')[:5]

    # 4. Gasto por Tienda (Cambiado 'listas' por 'listacompra')
    tiendas_stats = Tienda.objects.annotate(
        total_gastado=Sum('listacompra__total_ticket', filter=Q(listacompra__esta_finalizada=True)),
        num_visitas=Count('listacompra', filter=Q(listacompra__esta_finalizada=True))
    ).filter(num_visitas__gt=0).order_by('-total_gastado')

    context = {
        'gasto_total': gasto_total,
        'gasto_mes': gasto_mes,
        'top_productos': top_productos,
        'tiendas_stats': tiendas_stats,
    }
    return render(request, 'shopping/estadisticas.html', context)


def eliminar_lista(request, lista_id):
    lista = get_object_or_404(ListaCompra, id=lista_id)
    # Solo permitimos borrar si no está finalizada (por seguridad)
    if not lista.esta_finalizada:
        lista.delete()
    return redirect('dashboard')

def gestionar_maestro(request):
    # Ver todos los productos ordenados alfabéticamente
    productos = MaestroProducto.objects.all().order_by('nombre')
    
    # Buscador simple por si tiene muchos
    query = request.GET.get('q')
    if query:
        productos = productos.filter(nombre__icontains=query)
        
    return render(request, 'shopping/gestionar_maestro.html', {'productos': productos})

def eliminar_producto_maestro(request, producto_id):
    producto = get_object_or_404(MaestroProducto, id=producto_id)
    producto.delete()
    return redirect('gestionar_maestro')