from .models import Task, TaskReview
from datetime import date

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class TaskSerializer(serializers.ModelSerializer):
    boss = serializers.ReadOnlyField(source='boss.username')
    remain_days = serializers.SerializerMethodField()
    all_days = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'problem', 'reason', 'event',
                  'deadline', 'boss', 'employee',
                  'remain_days', 'all_days', 'status',
                  'financial_help', 'created_at', 'updated'
                  ]
        read_only_fields = ('status', 'created_at', 'updated', 'financial_help')

    def validate_employee(self, value):
        boss = self.context['request'].user
        if boss and boss.status == 'manager' and value and value.sector != boss.sector:
            raise ValidationError(
                {
                    'status': False,
                    'message': 'Bunday xodim sizning bo\'limingizda mavjud emas!'
                }
            )
        return value

    def validate_deadline(self, value):
        if value.date() <= date.today():
            raise ValidationError(
                {
                    'status': False,
                    'message': 'Topshiriq Muddati - bugungi sanadan keyingi sana bo\'lishi kerak!'
                })
        return value

    def get_remain_days(self, obj):
        return obj.remain_days

    def get_all_days(self, obj):
        return obj.all_days


class TaskReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskReview
        fields = ['content']

    def validate(self, attrs):
        content = attrs.get('content', None)
        if content == '':
            raise ValidationError(
                {
                    'status': False,
                    'message': 'Izoh yo\'q'
                }
            )
        else:
            return attrs
