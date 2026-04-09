from django.shortcuts import render, redirect, get_object_or_404
from django.db import IntegrityError
from django.db.models import Sum, Count, Q
from django.utils import timezone
from .models import Tienda, ListaCompra, MaestroProducto, ItemLista, PerfilUsuario
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario) 
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registro.html', {'form': form})

@login_required
def perfil(request):
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        perfil.nombre_completo = request.POST.get('nombre')
        perfil.apellidos = request.POST.get('apellidos')
        perfil.sexo = request.POST.get('sexo')

        nuevo_presupuesto = request.POST.get('presupuesto')
        if nuevo_presupuesto:
            perfil.presupuesto_mensual = nuevo_presupuesto.replace(',', '.')
            
        perfil.avatar_icon = request.POST.get('avatar_icon', perfil.avatar_icon)
        perfil.save()
        
        messages.success(request, "Perfil actualizado")
        return redirect('dashboard')

    return render(request, 'shopping/perfil.html', {'perfil': perfil})

@login_required
def dashboard(request):
    listas_abiertas = ListaCompra.objects.filter(usuario=request.user, esta_finalizada=False).order_by('-fecha_creacion')
    tiendas = Tienda.objects.filter(usuario=request.user).order_by('nombre')

    if request.method == 'POST':
        # Caso A: Añadir una tienda nueva
        if 'nombre_tienda' in request.POST:
            nombre = request.POST.get('nombre_tienda', '').strip().capitalize()
            color = request.POST.get('color_tienda', '#007bff')
            
            if nombre:
                # CREAR con el usuario actual
                Tienda.objects.get_or_create(usuario=request.user, nombre=nombre, defaults={'color_hex': color})
            return redirect('dashboard')

        # Caso B: Crear una nueva lista de la compra
        tienda_id = request.POST.get('tienda_id')
        if tienda_id:
            tienda = get_object_or_404(Tienda, id=tienda_id, usuario=request.user)
            nueva_lista = ListaCompra.objects.create(usuario=request.user, tienda=tienda)
            return redirect('ver_lista', lista_id=nueva_lista.id)

    return render(request, 'shopping/dashboard.html', {
        'listas_abiertas': listas_abiertas,
        'tiendas': tiendas,
    })

@login_required
def gestionar_tiendas(request):
    tiendas = Tienda.objects.filter(usuario=request.user).order_by('nombre')
    return render(request, 'shopping/gestionar_tiendas.html', {'tiendas': tiendas})

@login_required
def eliminar_tienda(request, tienda_id):
    tienda = get_object_or_404(Tienda, id=tienda_id, usuario=request.user)
    # Al eliminar la tienda, se borrarán sus listas por el models.CASCADE
    tienda.delete()
    return redirect('gestionar_tiendas')

@login_required
def cambiar_tienda_lista(request, lista_id):
    if request.method == 'POST':
        nueva_tienda_id = request.POST.get('nueva_tienda')
        
        # Obtenemos la lista y la nueva tienda, o lanzamos un error 404 si no existen
        lista = get_object_or_404(ListaCompra, id=lista_id, usuario=request.user)
        nueva_tienda = get_object_or_404(Tienda, id=nueva_tienda_id, usuario=request.user)
        
        # Cambiamos la tienda y guardamos
        lista.tienda = nueva_tienda
        lista.save()
        
    # Redirigimos de vuelta a la misma lista, que ahora mostrará la nueva tienda
    return redirect('ver_lista', lista_id=lista.id)

@login_required
def editar_tienda(request, tienda_id):
    tienda = get_object_or_404(Tienda, id=tienda_id, usuario=request.user)
    if request.method == 'POST':
        nombre = request.POST.get('nombre').strip().capitalize()
        color = request.POST.get('color_hex')
        
        if nombre:
            try:
                # Comprobamos que no exista OTRA tienda con ese nombre
                # (excluyendo la propia tienda que estamos editando)
                if not Tienda.objects.filter(usuario=request.user, nombre=nombre).exclude(id=tienda.id).exists():
                    tienda.nombre = nombre
                    tienda.color_hex = color
                    tienda.save()
            except IntegrityError:
                pass
                
    return redirect('gestionar_tiendas') # Siempre vuelve a la lista de gestión

@login_required
def cambiar_cantidad(request, item_id, operacion):
    item = get_object_or_404(ItemLista, id=item_id, lista__usuario=request.user)
    
    if operacion == 'sumar':
        item.cantidad += 1
    elif operacion == 'restar' and item.cantidad > 1:
        item.cantidad -= 1
    
    item.save()

    # Si la petición es AJAX, respondemos con el nuevo dato
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'nueva_cantidad': item.cantidad})
    
    # Si no es AJAX (por si acaso), redirigimos como antes
    return redirect('ver_lista', lista_id=item.lista.id)

# En tu ver_lista actual, asegúrate de que el POST maneje enteros
@login_required
def ver_lista(request, lista_id):
    lista = get_object_or_404(ListaCompra, id=lista_id, usuario=request.user)
    tiendas_disponibles = Tienda.objects.filter(usuario=request.user)
    
    if request.method == 'POST':
        nombre_prod = request.POST.get('nombre').strip().capitalize()
        # Capturamos la cantidad, si no viene en el POST por defecto es 1
        cantidad_input = int(request.POST.get('cantidad', 1))

        if nombre_prod:
            # 1. Buscamos o creamos el producto en el Maestro
            producto_maestro, created = MaestroProducto.objects.get_or_create(
                usuario=request.user,
                nombre=nombre_prod,
                defaults={'tienda_habitual': lista.tienda}
            )

            # 2. Categorización automática 
            if created or producto_maestro.zona == "General":
                nueva_zona = categorizar_mercadona(nombre_prod)
                if nueva_zona != "General":
                    producto_maestro.zona = nueva_zona
                    producto_maestro.save()
            
            # 3. LÓGICA ANTI-DUPLICADOS:
            # Buscamos si el producto ya está en esta lista
            item_existente = ItemLista.objects.filter(lista=lista, producto_maestro=producto_maestro).first()

            if item_existente:
                item_existente.cantidad += cantidad_input
                item_existente.save()
            else:
                ItemLista.objects.create(
                    lista=lista,
                    producto_maestro=producto_maestro,
                    cantidad=cantidad_input
                )

        return redirect('ver_lista', lista_id=lista.id)
    
    # --- Lógica de filtrado y orden ---
    orden = request.GET.get('orden', 'recientes')
    if orden == 'secciones':
        # Orden por zonas (el que teníamos antes)
        criterio = ['comprado', 'producto_maestro__zona', 'producto_maestro__nombre']
    elif orden == 'cantidad':
        criterio = ['comprado', '-cantidad', 'producto_maestro__nombre']
    elif orden == 'antiguos':
        criterio = ['comprado', 'creado_en']
    else: # 'recientes'
        criterio = ['comprado', '-creado_en']

    items = lista.items.all().order_by(*criterio)
    
    return render(request, 'shopping/lista_detalle.html', {
        'lista': lista,
        'tiendas_disponibles': tiendas_disponibles,
        'items': items,
        'sugerencias': MaestroProducto.objects.filter(usuario=request.user).order_by('-frecuencia_uso')[:12],
        'orden_actual': orden 
    })

@login_required
def completar_item(request, item_id):
    item = get_object_or_404(ItemLista, id=item_id, lista__usuario=request.user)
    item.comprado = not item.comprado
    item.save()
    
    # Leemos el orden de la URL actual
    orden = request.GET.get('orden', 'recientes')
    
    # Redirigimos manteniendo ese orden
    response = redirect('ver_lista', lista_id=item.lista.id)
    response['Location'] += f'?orden={orden}'
    return response

@login_required
def eliminar_item(request, item_id):
    item = get_object_or_404(ItemLista, id=item_id, lista__usuario=request.user)
    lista_id = item.lista.id
    item.delete()
    
    orden = request.GET.get('orden', 'recientes')
    
    response = redirect('ver_lista', lista_id=lista_id)
    response['Location'] += f'?orden={orden}'
    return response

@login_required
def finalizar_compra(request, lista_id):
    lista = get_object_or_404(ListaCompra, id=lista_id, usuario=request.user)
    
    if request.method == 'POST':
        estaba_finalizada_antes = lista.esta_finalizada
        
        total_raw = request.POST.get('total_ticket', '').strip()
        
        if not total_raw:
            lista.total_ticket = 0
        else:
            try:
                lista.total_ticket = float(total_raw.replace(',', '.'))
            except ValueError:
                lista.total_ticket = 0

        lista.items.all().update(comprado=True)
        lista.esta_finalizada = True
        
        # --- LÓGICA DE FECHA INAMOVIBLE ---
        if not lista.fecha_finalizada:
            lista.fecha_finalizada = timezone.now()
        
        lista.save()
        
        # --- FRECUENCIA ---
        if not estaba_finalizada_antes:
            for item in lista.items.filter(comprado=True):
                producto = item.producto_maestro
                producto.frecuencia_uso += 1
                producto.save()
            
        return redirect('dashboard')
    
    return redirect('ver_lista', lista_id=lista.id)

@login_required
def listas_archivadas(request):
    # Solo las que están finalizadas, de la más reciente a la más antigua
    listas = ListaCompra.objects.filter(usuario=request.user, esta_finalizada=True).order_by('-fecha_finalizada')
    return render(request, 'shopping/listas_archivadas.html', {'listas': listas})

@login_required
def reabrir_lista(request, lista_id):
    lista = get_object_or_404(ListaCompra, id=lista_id, usuario=request.user)
    
    # Solo descontamos si la lista realmente estaba cerrada
    if lista.esta_finalizada:
        # IMPORTANTE: Descontamos la frecuencia de los productos antes de abrirla
        for item in lista.items.filter(comprado=True):
            producto = item.producto_maestro
            if producto.frecuencia_uso > 0:
                producto.frecuencia_uso -= 1
                producto.save()
    
    # Ahora sí, la marcamos como abierta
    lista.esta_finalizada = False
    lista.total_ticket = 0
    # No tocamos lista.fecha_finalizada para que se mantenga la original al volver a cerrar
    lista.save()
    
    return redirect('ver_lista', lista_id=lista.id)

@login_required
def estadisticas(request):
    ahora = timezone.now()
    perfil = request.user.perfilusuario
    
    listas_usuario = ListaCompra.objects.filter(usuario=request.user, esta_finalizada=True)

    # 1. Gasto Mes Actual (Filtrando por mes Y año)
    gasto_mes = listas_usuario.filter(
        fecha_finalizada__month=ahora.month,
        fecha_finalizada__year=ahora.year
    ).aggregate(Sum('total_ticket'))['total_ticket__sum'] or 0

    # --- NUEVA LÓGICA DE PRESUPUESTO ---
    presupuesto = perfil.presupuesto_mensual or 0
    porcentaje_consumido = 0
    restante = 0
    excedente = 0

    if presupuesto > 0:
        gasto_float = float(gasto_mes)
        ppto_float = float(presupuesto)
        porcentaje_consumido = (gasto_float / ppto_float) * 100
        
        if gasto_float > ppto_float:
            excedente = gasto_float - ppto_float  # Lo que se ha pasado
            restante = 0
        else:
            restante = ppto_float - gasto_float   # Lo que le queda
            excedente = 0
    # ----------------------------------

    # 2. HISTORIAL MENSUAL (Filtrado por usuario)
    historial_meses = (
        listas_usuario
        .annotate(mes=TruncMonth('fecha_finalizada'))
        .values('mes')
        .annotate(total=Sum('total_ticket'))
        .order_by('-mes')
    )

    # 3. Top Productos (Solo los del usuario)
    top_productos = MaestroProducto.objects.filter(
        usuario=request.user, 
        frecuencia_uso__gt=0
    ).order_by('-frecuencia_uso')[:5]

    # 4. Tiendas Stats (Filtrado complejo)
    # Aquí filtramos las listas que se suman para que solo cuenten las del usuario
    tiendas_stats = Tienda.objects.filter(usuario=request.user).annotate(
        total_gastado=Sum('listacompra__total_ticket', filter=Q(listacompra__esta_finalizada=True)),
        num_visitas=Count('listacompra', filter=Q(listacompra__esta_finalizada=True))
    ).filter(num_visitas__gt=0).order_by('-total_gastado')

    context = {
        'gasto_mes': gasto_mes,
        'presupuesto': presupuesto,
        'porcentaje': min(porcentaje_consumido, 100), # Para que la barra no se salga del 100%
        'restante': restante,
        'excedente': excedente,
        'historial_meses': historial_meses,
        'top_productos': top_productos,
        'tiendas_stats': tiendas_stats,
        'mes_nombre': ahora.strftime('%B'),
        'perfil': perfil,
    }
    return render(request, 'shopping/estadisticas.html', context)

@login_required
def eliminar_lista(request, lista_id):
    lista = get_object_or_404(ListaCompra, id=lista_id, usuario=request.user)
    # Solo permitimos borrar si no está finalizada (por seguridad)
    if not lista.esta_finalizada:
        lista.delete()
    return redirect('dashboard')

@login_required
def eliminar_multiple_listas(request):
    if request.method == 'POST':
        ids_a_borrar = request.POST.getlist('listas_ids')
        if ids_a_borrar:
            # Esto borrará las listas y, si tienes Cascade en el modelo, sus productos
            ListaCompra.objects.filter(id__in=ids_a_borrar, usuario=request.user).delete()
    return redirect('listas_archivadas') 

@login_required
def gestionar_maestro(request):
    # Ver todos los productos ordenados alfabéticamente
    productos = MaestroProducto.objects.filter(usuario=request.user).order_by('nombre')
    
    # Buscador simple por si tiene muchos
    query = request.GET.get('q')
    if query:
        productos = productos.filter(nombre__icontains=query)
        
    return render(request, 'shopping/gestionar_maestro.html', {'productos': productos})

@login_required
def eliminar_producto_maestro(request, producto_id):
    producto = get_object_or_404(MaestroProducto, id=producto_id, usuario=request.user)
    producto.delete()
    return redirect('gestionar_maestro')

@login_required
def eliminar_multiple_maestros(request):
    if request.method == 'POST':
        ids_a_borrar = request.POST.getlist('productos_ids')
        if ids_a_borrar:
            MaestroProducto.objects.filter(id__in=ids_a_borrar, usuario=request.user).delete()
    return redirect('gestionar_maestro')

def categorizar_mercadona(nombre_prod):
    nombre = nombre_prod.lower()
    
    categorias = {
        'Congelados': [
            'congelad', 'conge', 'hielo', 'helad', 'sorbet', 'nugget', 
            'varit', 'croquet', 'lasaña', 'canelon', 'salteado', 'guisante',
            'verdur congelad', 'arroz congelado', 'pizz', 'corneto', 'magnum'
        ],
        'Salsas': [
            'mayones', 'ketchup', 'mostaz', 'brava', 'soja', 'gajo', 'alioli',
            'salsa', 'tabasco', 'teriyaki', 'pesto', 'boloñesa', 'carbonara',
            'vinagreta', 'barbacoa', 'bbq', 'roquefort', 'miel y mostaza'
        ],
        'Aperitivos': [
            'patat bolsa', 'patatas bolsa', 'papas', 'snack', 'fruto seco', 'almendr', 
            'avellan', 'nueces', 'pistacho', 'pipas', 'palomit', 'nachos', 
            'tortillita', 'cortez', 'cacahuete', 'anacard', 'picos', 'regaña', 'altramuz'
        ],
        'Pescadería': [
            'merluz', 'bacala', 'gamba', 'langostin', 'mejillon', 'pulpo', 
            'sepia', 'calamar', 'dorad', 'lubin', 'emperador', 'almej', 'gula', 'salmon',
            'rodaballo', 'dorada', 'lubina'
        ],
        'Despensa y Latas': [
            'atun', 'lata', 'conserva', 'bote', 'frasco', 'arroz', 'cuscus',
            'vasito', 'tarrina', 'pasta', 'macarr', 'espague', 'fideo', 'harin', 
            'aceit', 'vinagr', 'sal', 'azucar', 'legumbr', 'lentej', 'garbanz', 
            'alubi', 'cald', 'especi', 'frit', 'maiz', 'miel', 'tomate frito',
            'levadura', 'pan rallado', 'colorante'
        ],
        'Lácteos y Frío': [
            'yogur', 'cuajad', 'mantequill', 'kefir', 'leche', 'batid', 'nat', 
            'hummu', 'guacamol', 'gelatin', 'postr', 'mozzarel', 'flan',
            'masa', 'hojaldre', 'quebrada', 'base pizza', 'bebible', 'natillas',
            'salmorejo', 'gazpacho', 'margarina', 'petit'
        ],
        'Frutería y Verdura': [
            'patat', 'ceboll', 'ajo', 'lechug', 'tomat', 'platan', 'manzan', 'per', 
            'frut', 'verdur', 'aguacat', 'limon', 'naranj', 'fres', 'uvas',
            'pimiento', 'calabaci', 'zanahori', 'seta', 'champi', 'piña', 'kiwi', 
            'boniat', 'bonia', 'bata', 'batata', 'brocoli', 'berenjena', 'pepino'
        ],
        'Carnicería': [
            'poll', 'terner', 'cerd', 'lomo', 'filet', 'hamburg', 'alit', 'carn', 
            'pechug', 'torrez', 'picada', 'pavo fresco', 'cordero', 'conejo'
        ],
        'Charcutería/Quesos': [
            'embuti', 'chori', 'salchich', 'morta', 'pav', 'jamon', 'bacon', 
            'fuet', 'pancet', 'ques', 'pate', 'sobrasad', 'brie', 'parmesano',
            'cheddar', 'gouda', 'havarti', 'chopped'
        ],
        'Panadería y Dulces': [
            'pan', 'barr', 'hogaz', 'mold', 'croiss', 'napolitan', 'gallet', 
            'bizcoch', 'magdalen', 'donut', 'tortit', 'chocolat', 'bombon', 
            'caramel', 'gominol', 'tarta', 'pastel', 'sobao', 'palmera', 'cereales'
        ],
        'Bebidas y Bodega': [
            'agu', 'refresc', 'col', 'fant', 'cervez', 'vin', 'zum', 'energet', 
            'isoton', 'tint', 'sidr', 'caser', 'tonica', 'bati', 'gaseosa', 'licor'
        ],
        'Limpieza': [
            'detergent', 'suaviz', 'lavavajill', 'lejia', 'fregasuel', 'limpia', 
            'estropaj', 'bayet', 'fregona', 'escoba', 'bolsa basura', 'aluminio',
            'desengrasante', 'antical', 'pastillas lavavajillas', 'film'
        ],
        'Higiene y Cuidado': [
            'papel', 'higieni', 'cocin', 'servillet', 'champu', 'gel', 'desodor', 
            'dient', 'cepill', 'maquinill', 'jabon', 'crema', 'colonia',
            'compresa', 'tampon', 'acondicionador', 'mascarilla', 'protector'
        ],
        'Mascotas': [
            'perr', 'gat', 'pienso', 'mascot', 'aren', 'latit', 
            'snack gato', 'comida humeda', 'malta', 'rascador', 
            'antiparasit', 'pipet', 'collar', 'chuches', 'chur',
            'churu', 'dentastix', 'juguete perro'
        ],
    }

    for categoria, palabras in categorias.items():
        for palabra in palabras:
            if palabra in nombre:
                return categoria
                
    return 'General'