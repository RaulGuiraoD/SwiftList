from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('lista/<int:lista_id>/', views.ver_lista, name='ver_lista'),
    path('item/completar/<int:item_id>/', views.completar_item, name='completar_item'),
    path('item/eliminar/<int:item_id>/', views.eliminar_item, name='eliminar_item'),
    path('lista/finalizar/<int:lista_id>/', views.finalizar_compra, name='finalizar_compra'),
    path('archivo/', views.listas_archivadas, name='listas_archivadas'),
    path('lista/reabrir/<int:lista_id>/', views.reabrir_lista, name='reabrir_lista'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('lista/eliminar/<int:lista_id>/', views.eliminar_lista, name='eliminar_lista'),
    path('maestro/', views.gestionar_maestro, name='gestionar_maestro'),
    path('maestro/eliminar/<int:producto_id>/', views.eliminar_producto_maestro, name='eliminar_producto_maestro'),
    path('maestro/eliminar-multiple/', views.eliminar_multiple_maestros, name='eliminar_multiple_maestros'),
    path('tiendas/', views.gestionar_tiendas, name='gestionar_tiendas'),
    path('tiendas/eliminar/<int:tienda_id>/', views.eliminar_tienda, name='eliminar_tienda'),
    path('tiendas/editar/<int:tienda_id>/', views.editar_tienda, name='editar_tienda'),
    path('item/cantidad/<int:item_id>/<str:operacion>/', views.cambiar_cantidad, name='cambiar_cantidad'),

]