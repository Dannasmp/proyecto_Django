# Importación de APIView para crear vistas basadas en clases en Django REST Framework
from rest_framework.views import APIView

# Permite devolver respuestas HTTP en formato JSON
from rest_framework.response import Response

# Contiene códigos de estado HTTP (200, 404, 500, etc.)
from rest_framework import status

# Permite restringir acceso solo a usuarios autenticados
from rest_framework.permissions import IsAuthenticated

# Importa el serializador encargado de validar los datos de tareas
from .serializers import TareasSerializer

# Importa la autenticación personalizada con Firebase
from .authentication import FirebaseAuthentication

# Función que conecta con Firestore
from backend.firebase_config import get_firestore_client

# Importa utilidades especiales de Firestore
from firebase_admin import firestore

# Librería para subir imágenes a Cloudinary
import cloudinary.uploader


# Se inicializa la conexión con Firestore
db = get_firestore_client()


# =========================
# API PARA GESTIÓN DE TAREAS
# =========================
class TareaAPIView(APIView):

    # Se define el sistema de autenticación personalizado
    authentication_classes = [FirebaseAuthentication]

    # Solo usuarios autenticados pueden acceder
    permission_classes = [IsAuthenticated]

    """
    GET: Obtiene tareas según el rol del usuario:
    - Instructor: ve todas las tareas
    - Aprendiz: solo ve sus propias tareas
    """

    def get(self, request, tarea_id=None):

        # UID del usuario autenticado
        uid_usuario = request.user.uid

        # Rol del usuario autenticado
        rol_usuario = request.user.rol

        try:
            # Si es instructor obtiene todas las tareas
            if rol_usuario == 'instructor':
                docs = db.collection('api_tareas').stream()

            # Si no, solo obtiene tareas propias
            else:
                docs = db.collection('api_tareas').where(
                    'uid_usuario', '==', uid_usuario
                ).stream()

            tareas = []

            # Se recorren los documentos encontrados
            for doc in docs:
                tarea_data = doc.to_dict()
                tarea_data['id'] = doc.id
                tareas.append(tarea_data)

            # Respuesta exitosa
            return Response(
                {
                    "mensaje": f"Listando tareas desde el rol de {rol_usuario}",
                    "datos": tareas
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"mensaje": f"Error al obtener tareas: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    # =========================
    # CREAR NUEVA TAREA
    # =========================
    def post(self, request):

        # Validación de datos recibidos
        serializer = TareasSerializer(data=request.data)

        if serializer.is_valid():

            # Datos validados
            datos_validados = serializer.validated_data

            # Se asigna automáticamente el usuario dueño de la tarea
            datos_validados['uid_usuario'] = request.user.uid

            # Fecha automática de creación desde servidor Firestore
            datos_validados['fecha_creacion'] = firestore.SERVER_TIMESTAMP

            try:
                # Guarda documento en Firestore
                nuevo_doc = db.collection('api_tareas').add(datos_validados)

                # Obtiene ID generado
                id_generador = nuevo_doc[1].id

                return Response(
                    {
                        "mensaje": "Tarea creada correctamente",
                        "id": id_generador
                    },
                    status=status.HTTP_201_CREATED,
                )

            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    # =========================
    # ACTUALIZAR TAREA
    # =========================
    def put(self, request, tarea_id):

        # Verifica que llegue ID
        if not tarea_id:
            return Response(
                {"error": "El ID es requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Referencia al documento
            tarea_ref = db.collection('api_tareas').document(tarea_id)

            doc = tarea_ref.get()

            # Si no existe
            if not doc.exists:
                return Response(
                    {"error": "El ID no se ha encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )

            tarea_data = doc.to_dict()

            # Solo el dueño puede editar
            if tarea_data.get('uid_usuario') != request.user.uid:
                return Response(
                    {"Error": "No tienes acceso a esta tarea"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Validación parcial
            serializer = TareasSerializer(data=request.data, partial=True)

            if serializer.is_valid():

                # Actualiza documento
                tarea_ref.update(serializer.validated_data)

                return Response({
                    "mensaje": f"Tarea {tarea_id} actualizada",
                    "datos": serializer.validated_data
                }, status=status.HTTP_200_OK)

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    # =========================
    # ELIMINAR TAREAS
    # =========================
    def delete(self, request, tarea_id=None):

        try:
            # Si no llega ID → eliminar todas (solo instructor)
            if tarea_id is None:

                if request.user.rol != 'instructor':
                    return Response(
                        {"error": "No tienes permiso para eliminar todas las tareas"},
                        status=status.HTTP_403_FORBIDDEN
                    )

                docs = db.collection('api_tareas').stream()
                eliminadas = 0

                # Elimina todas las tareas
                for doc in docs:
                    db.collection('api_tareas').document(doc.id).delete()
                    eliminadas += 1

                return Response(
                    {"mensaje": f"Se eliminaron {eliminadas} tareas"},
                    status=status.HTTP_200_OK
                )

            # Eliminar una sola tarea
            tarea_ref = db.collection('api_tareas').document(tarea_id)

            if not tarea_ref.get().exists:
                return Response(
                    {"error": "No encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )

            doc = tarea_ref.get()
            tarea_data = doc.to_dict()

            # Solo el dueño puede eliminar
            if tarea_data.get('uid_usuario') != request.user.uid:
                return Response(
                    {"error": "No tienes permiso para eliminar esta tarea"},
                    status=status.HTTP_403_FORBIDDEN
                )

            tarea_ref.delete()

            return Response(
                {"mensaje": f"Tarea {tarea_id} se ha eliminado correctamente"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================
# API PERFIL DE USUARIO
# =========================
class PerfilAPIView(APIView):

    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]


    # =========================
    # OBTENER PERFIL
    # =========================
    def get(self, request):

        try:
            uid = request.user.uid

            # Busca perfil por UID
            doc = db.collection('perfiles').document(uid).get()

            # Si no existe perfil devuelve valores por defecto
            if not doc.exists:
                return Response({
                    "username": "Usuario ADSO",
                    "rol": "aprendiz",
                    "foto_url": None
                })

            data = doc.to_dict()

            return Response({
                "username": data.get('username'),
                "rol": data.get('rol'),
                "foto_url": data.get('foto_url')
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)


    # =========================
    # SUBIR O ACTUALIZAR IMAGEN
    # =========================
    def put(self, request):

        try:
            uid = request.user.uid

            # Muestra archivos recibidos (debug)
            print("FILES:", request.FILES)

            # Verifica que llegue imagen
            if 'imagen' not in request.FILES:
                return Response(
                    {"error": "No se envió imagen"},
                    status=400
                )

            imagen = request.FILES['imagen']

            # Subida a Cloudinary
            resultado = cloudinary.uploader.upload(
                imagen,
                folder="perfiles"
            )

            # URL segura generada
            foto_url = resultado.get('secure_url')

            # Guarda URL en Firestore
            db.collection('perfiles').document(uid).set({
                "foto_url": foto_url
            }, merge=True)

            return Response({
                "mensaje": "Imagen actualizada",
                "foto_url": foto_url
            })

        except Exception as e:
            print("ERROR:", e)
            return Response({"error": str(e)}, status=500)