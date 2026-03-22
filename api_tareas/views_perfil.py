from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .authentication import FirebaseAuthentication
from backend.firebase_config import get_firestore_client
import cloudinary.uploader

db = get_firestore_client()

class PerfilAPIView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    #  GET → Obtener perfil
    def get(self, request):
        try:
            uid = request.user.uid

            doc = db.collection('perfiles').document(uid).get()

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


class PerfilImagenAPIView(APIView):
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    #  PUT → Actualizar solo imagen
    def put(self, request):
        try:
            uid = request.user.uid

            if 'imagen' not in request.FILES:
                return Response({"error": "No se envió imagen"}, status=400)

            imagen = request.FILES['imagen']

            resultado = cloudinary.uploader.upload(
                imagen,
                folder="perfiles"
            )

            foto_url = resultado.get('secure_url')

            db.collection('perfiles').document(uid).set({
                "foto_url": foto_url
            }, merge=True)

            return Response({
                "mensaje": "Imagen actualizada",
                "foto_url": foto_url
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)