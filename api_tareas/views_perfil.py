# Importa APIView para crear vistas basadas en clases en Django REST Framework
from rest_framework.views import APIView

# Permite devolver respuestas HTTP en formato JSON
from rest_framework.response import Response

# Restringe acceso solo a usuarios autenticados
from rest_framework.permissions import IsAuthenticated

# Importa autenticación personalizada con Firebase
from .authentication import FirebaseAuthentication

# Función que conecta con Firestore
from backend.firebase_config import get_firestore_client

# Librería para subir imágenes a Cloudinary
import cloudinary.uploader


# Inicializa conexión con Firestore
db = get_firestore_client()


# =========================
# API PARA CONSULTAR PERFIL
# =========================
class PerfilAPIView(APIView):

    # Sistema de autenticación personalizado
    authentication_classes = [FirebaseAuthentication]

    # Solo usuarios autenticados pueden acceder
    permission_classes = [IsAuthenticated]


    # =========================
    # GET → OBTENER PERFIL
    # =========================
    def get(self, request):

        try:
            # Obtiene el UID del usuario autenticado
            uid = request.user.uid

            # Busca el perfil en Firestore usando el UID
            doc = db.collection('perfiles').document(uid).get()

            # Si el perfil no existe, devuelve datos por defecto
            if not doc.exists:
                return Response({
                    "username": "Usuario ADSO",
                    "rol": "aprendiz",
                    "foto_url": None
                })

            # Convierte el documento en diccionario
            data = doc.to_dict()

            # Retorna datos del perfil encontrados
            return Response({
                "username": data.get('username'),
                "rol": data.get('rol'),
                "foto_url": data.get('foto_url')
            })

        except Exception as e:
            # Manejo de error general
            return Response({"error": str(e)}, status=500)


# =========================
# API PARA ACTUALIZAR IMAGEN DE PERFIL
# =========================
class PerfilImagenAPIView(APIView):

    # Sistema de autenticación con Firebase
    authentication_classes = [FirebaseAuthentication]

    # Solo usuarios autenticados pueden acceder
    permission_classes = [IsAuthenticated]


    # =========================
    # PUT → ACTUALIZAR SOLO IMAGEN
    # =========================
    def put(self, request):

        try:
            # Obtiene UID del usuario autenticado
            uid = request.user.uid

            # Verifica que se haya enviado una imagen
            if 'imagen' not in request.FILES:
                return Response(
                    {"error": "No se envió imagen"},
                    status=400
                )

            # Captura archivo enviado
            imagen = request.FILES['imagen']

            # Sube imagen a Cloudinary en carpeta perfiles
            resultado = cloudinary.uploader.upload(
                imagen,
                folder="perfiles"
            )

            # Obtiene URL segura generada
            foto_url = resultado.get('secure_url')

            # Guarda URL en Firestore
            db.collection('perfiles').document(uid).set({
                "foto_url": foto_url
            }, merge=True)

            # Respuesta exitosa
            return Response({
                "mensaje": "Imagen actualizada",
                "foto_url": foto_url
            })

        except Exception as e:
            # Manejo de error general
            return Response({"error": str(e)}, status=500)