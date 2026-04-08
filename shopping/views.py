from django.shortcuts import render, redirect, get_object_or_404
from django.db import models, IntegrityError
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import Tienda, ListaCompra, MaestroProducto, ItemLista
from django.db.models.functions import TruncMonth

def dashboard(request):
    listas_abiertas = ListaCompra.objects.filter(esta_finalizada=False).order_by('-fecha_creacion')
    tiendas = Tienda.objects.all().order_by('nombre')

    if request.method == 'POST':
        # Caso A: Añadir una tienda nueva
        if 'nombre_tienda' in request.POST:
            nombre = request.POST.get('nombre_tienda', '').strip().capitalize()
            color = request.POST.get('color_tienda', '#007bff')
            
            if nombre:
                # Verificamos si ya existe para no dar error de sistema
                if not Tienda.objects.filter(nombre=nombre).exists():
                    Tienda.objects.create(nombre=nombre, color_hex=color)
                # Si ya existe, simplemente no hacemos nada (o podrías mandar un mensaje)
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

def gestionar_tiendas(request):
    tiendas = Tienda.objects.all().order_by('nombre')
    return render(request, 'shopping/gestionar_tiendas.html', {'tiendas': tiendas})

def eliminar_tienda(request, tienda_id):
    tienda = get_object_or_404(Tienda, id=tienda_id)
    # Al eliminar la tienda, se borrarán sus listas por el models.CASCADE
    tienda.delete()
    return redirect('gestionar_tiendas')

def editar_tienda(request, tienda_id):
    tienda = get_object_or_404(Tienda, id=tienda_id)
    if request.method == 'POST':
        nombre = request.POST.get('nombre').strip().capitalize()
        color = request.POST.get('color_hex')
        
        if nombre:
            try:
                # Comprobamos que no exista OTRA tienda con ese nombre
                # (excluyendo la propia tienda que estamos editando)
                if not Tienda.objects.exclude(id=tienda.id).filter(nombre=nombre).exists():
                    tienda.nombre = nombre
                    tienda.color_hex = color
                    tienda.save()
            except IntegrityError:
                pass
                
    return redirect('gestionar_tiendas') # Siempre vuelve a la lista de gestión


def cambiar_cantidad(request, item_id, operacion):
    item = get_object_or_404(ItemLista, id=item_id)
    if operacion == 'sumar':
        item.cantidad += 1
    elif operacion == 'restar' and item.cantidad > 1:
        item.cantidad -= 1
    item.save()
    return redirect('ver_lista', lista_id=item.lista.id)

# En tu ver_lista actual, asegúrate de que el POST maneje enteros
def ver_lista(request, lista_id):
    lista = get_object_or_404(ListaCompra, id=lista_id)
    
    if request.method == 'POST':
        nombre_prod = request.POST.get('nombre').strip().capitalize()
        cantidad = request.POST.get('cantidad', 1)

        if nombre_prod:
            # 1. Intentamos buscarlo. Si no existe, lo creamos.
            producto_maestro, created = MaestroProducto.objects.get_or_create(
                nombre=nombre_prod,
                defaults={'tienda_habitual': lista.tienda}
            )

            # 2. Si es NUEVO (created es True), le asignamos la zona automáticamente
            if created or producto_maestro.zona == "General":
                nueva_zona = categorizar_mercadona(nombre_prod)
                # Solo guardamos si el cerebro ha encontrado algo mejor que "General"
                if nueva_zona != "General":
                    producto_maestro.zona = nueva_zona
                    producto_maestro.save()
            
            # 3. Añadir a la lista
            ItemLista.objects.create(
                lista=lista,
                producto_maestro=producto_maestro,
                cantidad=int(cantidad)
            )
        return redirect('ver_lista', lista_id=lista.id)
    
    # ... resto de la lógica de la vista (mantenla igual) ...
    items = lista.items.all().order_by(
        'comprado', 
        'producto_maestro__zona', 
        'producto_maestro__nombre'
    )
    return render(request, 'shopping/lista_detalle.html', {
        'lista': lista,
        'items': items,
        'sugerencias': MaestroProducto.objects.filter(frecuencia_uso__gt=0)[:10]
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
        lista.fecha_finalizada = timezone.now()
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
    ahora = timezone.now()
    
    # 1. Gasto Mes Actual (Filtrando por mes Y año)
    gasto_mes = ListaCompra.objects.filter(
        esta_finalizada=True, 
        fecha_finalizada__month=ahora.month,
        fecha_finalizada__year=ahora.year
    ).aggregate(Sum('total_ticket'))['total_ticket__sum'] or 0

    # 2. HISTORIAL MENSUAL (Agrupado)
    # Esto genera una lista de diccionarios con el gasto de cada mes
    historial_meses = (
        ListaCompra.objects.filter(esta_finalizada=True)
        .annotate(mes=TruncMonth('fecha_finalizada'))
        .values('mes')
        .annotate(total=Sum('total_ticket'))
        .order_by('-mes')
    )

    # 3. Top Productos y Tiendas (Mantén tu lógica que está muy bien)
    top_productos = MaestroProducto.objects.filter(frecuencia_uso__gt=0).order_by('-frecuencia_uso')[:5]
    tiendas_stats = Tienda.objects.annotate(
        total_gastado=Sum('listacompra__total_ticket', filter=Q(listacompra__esta_finalizada=True)),
        num_visitas=Count('listacompra', filter=Q(listacompra__esta_finalizada=True))
    ).filter(num_visitas__gt=0).order_by('-total_gastado')

    context = {
        'gasto_mes': gasto_mes,
        'historial_meses': historial_meses,
        'top_productos': top_productos,
        'tiendas_stats': tiendas_stats,
        'mes_nombre': ahora.strftime('%B') # Para mostrar "Abril" en el título
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

def categorizar_mercadona(nombre):
    nombre = nombre.lower()
    
    # Usamos "raíces" de palabras para captar plurales y diminutivos
    categorias = {
        'Frutería y Verdura': [
            'patat', 'ceboll', 'ajo', 'lechug', 'tomat', 'platan', 'manzan', 'per', 
            'frut', 'verdur', 'boniat', 'aguacat', 'limon', 'naranj', 'fres', 
            'pimiento', 'calabaci', 'zanahori', 'seta', 'champi', 'uvas', 'piña'
        ],
        'Carnicería/Charcutería': [
            'poll', 'terner', 'cerd', 'pav', 'jamon', 'lomo', 'embuti', 'chori', 
            'salchich', 'morta', 'filet', 'hamburg', 'alit', 'carn', 'serra', 
            'cocid', 'bacon', 'fuet', 'pancet', 'ques' # El queso suele estar cerca
        ],
        'Lácteos y Frío': [
            'lech', 'yogur', 'cuajad', 'mantequill', 'kefir', 'batid', 'nat', 
            'hummu', 'guacamol', 'gelatin', 'postr', 'bifidu', 'mozzarel', 'flan'
        ],
        'Congelados': [
            'hielo', 'pizz', 'helad', 'nugget', 'croquet', 'varit', 'congelad', 'sorbet'
        ],
        'Panadería y Dulces': [
            'pan', 'barr', 'hogaz', 'mold', 'croiss', 'napolitan', 'gallet', 
            'bizcoch', 'magdalen', 'donut', 'tortit', 'pico', 'regaña', 'chocolat'
        ],
        'Despensa y Latas': [
            'arroz', 'past', 'macarr', 'espague', 'fideo', 'harin', 'aceit', 
            'vinagr', 'sal', 'azucar', 'legumbr', 'lentej', 'garbanz', 'alubi', 
            'cald', 'especi', 'bot', 'conserv', 'atun', 'frit', 'maiz', 'miel'
        ],
        'Bebidas y Bodega': [
            'agu', 'refresc', 'col', 'fant', 'cervez', 'vin', 'zum', 'energet', 
            'isoton', 'tint', 'sidr', 'caser', 'tónica'
        ],
        'Limpieza e Higiene': [
            'detergent', 'suaviz', 'lavavajill', 'lejia', 'fregasuel', 'limpia', 
            'estropaj', 'bayet', 'papel', 'higieni', 'cocin', 'servillet', 
            'champú', 'gel', 'desodor', 'dient', 'cepill', 'maquinill', 'pañal', 
            'compres', 'toallit', 'jabon', 'suavi'
        ],
        'Mascotas': [
            'perr', 'gat', 'pienso', 'mascot', 'aren', 'latit'
        ],
    }

    # Comprobamos si la RAÍZ está dentro del NOMBRE
    for zona, raices in categorias.items():
        if any(raiz in nombre for raiz in raices):
            return zona
            
    return "General"