from django.urls import path
from .views import TareaAPIView
from .views_auth import LoginAPIView, RegistroAPIView
from .views_perfil import PerfilAPIView, PerfilImagenAPIView  # 🔥 FIX

urlpatterns = [
    path('auth/login/', LoginAPIView.as_view()),
    path('auth/registro/', RegistroAPIView.as_view()),

    path('tareas/', TareaAPIView.as_view()),
    path('tareas/<str:tarea_id>/', TareaAPIView.as_view()),

    path('perfil/', PerfilAPIView.as_view()),  # 🔥 PERFIL DATOS
    path('perfil/imagen/', PerfilImagenAPIView.as_view()),  # 🔥 SOLO IMAGEN
]