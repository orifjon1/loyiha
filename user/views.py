from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from .serializers import UserSignUpSerializer, SectorSerializer, RefreshTokenSerializer, UserProfileSerializer, UserStatSerializer
from .models import CustomUser, Sector
from api import permission

from rest_framework.views import APIView
from rest_framework import generics, permissions, filters


class SignUpView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSignUpSerializer
    permission_classes = [permissions.AllowAny, ]


class LogoutView(GenericAPIView):
    serializer_class = RefreshTokenSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args):
        sz = self.get_serializer(data=request.data)
        sz.is_valid(raise_exception=True)
        sz.save()
        return Response({"detail": "Logout successful."})


class UserProfileView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer


class RequestUserProfileView(APIView):
    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        user = request.user
        serializer = UserProfileSerializer(data=request.data, instance=user, partial=True)
        return Response(
            {
                'status': True,
                'message': "O'zgarishlar saqlandi"
            }
        )


class RequestUserStatView(APIView):
    def get(self, request):
        user = request.user
        serializer = UserStatSerializer(user)
        return Response(serializer.data)


class UserProfileListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer


class UserStatListView(generics.ListAPIView):
    queryset = CustomUser.objects.all().exclude(status='director').exclude(status='admin')
    serializer_class = UserStatSerializer


class ManagerStatListView(generics.ListAPIView):
    queryset = CustomUser.objects.filter(status='manager')
    serializer_class = UserStatSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = ['first_name', 'last_name']
    search_fields = ['first_name', 'last_name']


class EmployeeStatListView(generics.RetrieveAPIView):
    queryset = CustomUser.objects.filter(status='employee')
    serializer_class = UserStatSerializer


class SectorCreateListView(generics.ListCreateAPIView):
    permission_classes = [permission.IsDirector]
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer


class SectorDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permission.IsDirector]
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer



