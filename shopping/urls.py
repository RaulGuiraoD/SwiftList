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
]