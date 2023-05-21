from django.db.models import Q
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError

from .ordering import DateRangeFilter
from .serializers import TaskSerializer, TaskReviewSerializer
from .models import Task, TaskReview
from user.models import CustomUser, Sector
from user.serializers import UserStatSerializer
from api.permission import IsDirector, IsManager, IsOwnerOfTask, IsDirectorOrManager, IsBossOrWorker, IsOwnerOfReview, \
    IsAdmin

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, filters


class ManagerTaskListView(APIView):
    permission_classes = [IsManager]
    filter_backends = [filters.SearchFilter]
    search_fields = ['employee', 'deadline']
    filterset_fields = ['employee', 'deadline', 'created_at']

    def get(self, request):
        tasks = Task.objects.filter(Q(boss=request.user) & Q(is_active=True))
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class TaskListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsDirectorOrManager, ]
    queryset = Task.objects.filter(is_active=True)
    serializer_class = TaskSerializer

    def perform_create(self, serializer):
        serializer.save(boss=self.request.user)


class DirectorTaskListCreateView(generics.ListAPIView):
    permission_classes = [IsDirector]
    queryset = Task.objects.filter(is_active=True).exclude(boss__status='manager')
    serializer_class = TaskSerializer

    def perform_create(self, serializer):
        serializer.save(boss=self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfTask, IsAdmin]
    queryset = Task.objects.filter(is_active=True)
    serializer_class = TaskSerializer


class TaskReviewListView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsBossOrWorker]
    queryset = TaskReview.objects.all()
    serializer_class = TaskReviewSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskReviewsList(APIView):
    permission_classes = [IsBossOrWorker]

    def get(self, request, id):
        try:
            task = Task.objects.get(id=id)
            reviews = TaskReview.objects.filter(task=task)
            serializer = UserStatSerializer(reviews, many=True)
            return Response(serializer.data)
        except:
            raise ValidationError(
                {
                    'status': False,
                    'message': "Topshiriq mavjud emas !"
                }
            )


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsOwnerOfReview]
    queryset = TaskReview.objects.all()
    serializer_class = TaskReviewSerializer


class StatView(APIView):
    def get(self, request):
        tasks = Task.objects.filter(Q(boss__status='admin') | Q(boss__status='director') & Q(is_active=True))
        all_task = tasks.count()
        doing = tasks.filter(status='doing').count()
        finished = tasks.filter(status='finished').count()
        canceled = tasks.filter(status='canceled').count()
        missed = tasks.filter(status='missed').count()
        changed = tasks.filter(is_changed=True).count()
        data = {}
        if all_task != 0:
            data['doing'] = doing
            data['finished'] = finished
            data['canceled'] = canceled
            data['missed'] = missed
            data['p_doing'] = doing * 100 / all_task
            data['p_finished'] = finished * 100 / all_task
            data['p_canceled'] = canceled * 100 / all_task
            data['p_missed'] = missed * 100 / all_task
            data['changed'] = changed * 100 / all_task
        return Response(data=data)


class SectorStatView(APIView):

    def get(self, request):
        sectors = Sector.objects.all()
        l = []
        for s in sectors:
            data = {}
            tasks = Task.objects.filter((Q(boss__status='admin') | Q(boss__status='director')) & Q(is_active=True) &
                                        Q(employee__sector=s))
            all_task = tasks.count()
            doing = tasks.filter(status='doing').count()
            finished = tasks.filter(status='finished').count()
            canceled = tasks.filter(status='canceled').count()
            missed = tasks.filter(status='missed').count()
            changed = tasks.filter(is_changed=True).count()
            if all_task != 0:
                data['sector'] = s.name
                data['doing'] = doing
                data['finished'] = finished
                data['canceled'] = canceled
                data['missed'] = missed
                data['p_doing'] = doing * 100 / all_task
                data['p_finished'] = finished * 100 / all_task
                data['p_canceled'] = canceled * 100 / all_task
                data['p_missed'] = missed * 100 / all_task
                data['p_changed'] = changed * 100 / all_task
            l.append(data)
        return Response({
            'message': l
        })


class EachSectorStatView(APIView):
    def get(self, request, id=id):
        try:
            sector = Sector.objects.get(id=id)
            tasks = Task.objects.filter((Q(boss__status='admin') | Q(boss__status='director')) & Q(is_active=True) &
                                        Q(employee__sector=sector))
            all_task = tasks.count()
            doing = tasks.filter(status='doing').count()
            finished = tasks.filter(status='finished').count()
            canceled = tasks.filter(status='canceled').count()
            missed = tasks.filter(status='missed').count()
            changed = tasks.filter(is_changed=True).count()
            data = {}
            if all_task != 0:
                data["all_tasks"] = all_task
                data["doing"] = doing
                data["finished"] = finished
                data["canceled"] = canceled
                data["missed"] = missed
                data["changed"] = changed
                data['p_doing'] = doing * 100 / all_task
                data['p_finished'] = finished * 100 / all_task
                data['p_canceled'] = canceled * 100 / all_task
                data['p_missed'] = missed * 100 / all_task
                data['p_changed'] = changed * 100 / all_task
            return Response(data=data)
        except:
            raise ValidationError(
                {
                    'status': False,
                    'message': "Bu bo'lim mavjud emas !"
                }
            )


class EachSectorEmployeeStatView(APIView):
    def get(self, request, id):
        try:
            sector = Sector.objects.get(id=id)
            employees = CustomUser.objects.filter(Q(sector=sector) & Q(status='employee'))
            serializer = UserStatSerializer(employees, many=True)
            return Response(serializer.data)
        except:
            raise ValidationError(
                {
                    'status': False,
                    'message': "Bo'lim mavjud emas !"
                }
            )


class EachSectorTasksView(APIView):
    filter_backends = [DjangoFilterBackend, DateRangeFilter]
    ordering_fields = ['employee__first_name', 'deadline', 'created_at', 'boss', 'status', 'date_range']

    def get(self, request, id=id):
        try:
            sector = Sector.objects.get(id=id)
            tasks = Task.objects.filter(Q(is_active=True) & Q(boss__sector=sector))
            tasks = self.filter_queryset(tasks)
            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data)
        except:
            raise ValidationError(
                {
                    'status': False,
                    'message': "Bu bo'lim mavjud emas !"
                }
            )

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        ordering = self.request.query_params.get("ordering", None)
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset


class EachTaskReview(APIView):
    def get(self, request, id=id):
        try:
            task = Task.objects.get(id=id)
            reviews = TaskReview.objects.filter(task=task)
            serializer = TaskReviewSerializer(reviews, many=True)
            return Response(serializer.data)
        except:
            raise ValidationError(
                {
                    'status': False,
                    'message': "Bu topshiriq mavjud emas !"
                }
            )


class FinishTaskView(APIView):
    permission_classes = [IsBossOrWorker]

    def patch(self, request, id):
        try:
            task = Task.objects.get(id=id)
            if task.status == 'doing':
                task.status = 'finished'
                task.save()
                return Response(
                    {
                        'status': True,
                        'message': 'Topshiriq yakunlandi'
                    }
                )
            elif task.status == 'finished':
                task.status = 'doing'
                task.save()
                return Response(
                    {
                        'status': True,
                        'message': 'Topshiriq faol holatda !'
                    }
                )
            elif task.status == 'canceled':
                return Response(
                    {
                        'status': True,
                        'message': 'Topshiriq bekor qilingan, yakunlay olmaysiz !'
                    }
                )
            else:
                return Response(
                    {
                        'status': True,
                        'message': 'Topshiriqni bajarilish muddati tugagan !'
                    }
                )
        except:
            raise ValidationError(
                {
                    'status': False,
                    'message': 'Topshiriq mavjud emas!'
                }
            )


class CancelTaskView(APIView):
    permission_classes = [IsBossOrWorker]

    def patch(self, request, id):
        try:
            task = Task.objects.get(id=id)
            if task.status == 'doing':
                task.status = 'canceled'
                task.save()
                return Response(
                    {
                        'status': True,
                        'message': 'Topshiriq bekor qilindi'
                    }
                )
            elif task.status == 'canceled':
                task.status = 'doing'
                task.save()
                return Response(
                    {
                        'status': True,
                        'message': 'Topshiriq faol holatda !'
                    }
                )
            elif task.status == 'finished':
                return Response(
                    {
                        'status': True,
                        'message': 'Topshiriq yakunlangan !'
                    }
                )
            else:
                return Response(
                    {
                        'status': True,
                        'message': 'Topshiriqni bajarilish muddati tugagan !'
                    }
                )
        except:
            raise ValidationError(
                {
                    'status': False,
                    'message': 'Topshiriq mavjud emas!'
                }
            )


class UserSectorTasksView(APIView):
    filter_backends = [DjangoFilterBackend, DateRangeFilter]
    ordering_fields = ['employee__first_name', 'deadline', 'created_at', 'boss', 'status', 'date_range']

    def get(self, request, id):
        try:
            user = CustomUser.objects.get(id=id)
            tasks = Task.objects.filter(Q(employee=user) & Q(boss__status='manager'))
            tasks = self.filter_queryset(tasks)
            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data)
        except:
            raise ValidationError(
                {
                    'status': False,
                    'message': "Bu foydalanuvchi mavjud emas !"
                }
            )

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        ordering = self.request.query_params.get("ordering", None)
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset


class UserDirectorTasksView(APIView):
    filter_backends = [DjangoFilterBackend, DateRangeFilter]
    ordering_fields = ['employee__first_name', 'deadline', 'created_at', 'boss', 'status', 'date_range']

    def get(self, request, id):
        try:
            user = CustomUser.objects.get(id=id)
            tasks = Task.objects.filter(Q(employee=user) & (Q(boss__status='director') | Q(boss__status='admin')))
            tasks = self.filter_queryset(tasks)
            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data)
        except:
            raise ValidationError(
                {
                    'status': False,
                    'message': "Bu foydalanuvchi mavjud emas !"
                }
            )

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        ordering = self.request.query_params.get("ordering", None)
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset


class RequestUserSectorTasksView(APIView):
    filter_backends = [DjangoFilterBackend, DateRangeFilter]
    ordering_fields = ['employee__first_name', 'deadline', 'created_at', 'boss', 'status', 'date_range']

    def get(self, request):
        tasks = Task.objects.filter(Q(employee=request.user) & Q(boss__status='manager'))
        tasks = self.filter_queryset(tasks)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        ordering = self.request.query_params.get("ordering", None)
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset


class RequestUserDirectorTasksView(APIView):
    filter_backends = [DjangoFilterBackend, DateRangeFilter]
    ordering_fields = ['employee__first_name', 'deadline', 'created_at', 'boss', 'status', 'date_range']

    def get(self, request):
        user = CustomUser.objects.get(id=id)
        tasks = Task.objects.filter(Q(employee=user) & (Q(boss__status='director') | Q(boss__status='admin')))
        tasks = self.filter_queryset(tasks)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        ordering = self.request.query_params.get("ordering", None)
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset
