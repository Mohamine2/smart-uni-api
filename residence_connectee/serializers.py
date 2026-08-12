from django.db.models import Q
from rest_framework import serializers
from .models import Student, News, SmartDevice, Room, StudyRoom, StudyRoomReservation, Apartment

class SmartDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmartDevice
        fields = [
            'id',
            'name',
            'device_type',
            'is_on',
            'power_consumption',
            'description',
            'brand',
            'connectivity',
            'battery_level',
            'last_interaction',
            'room'
        ]

class StudyRoomReservationSerializer(serializers.ModelSerializer):

    class Meta:
        model = StudyRoomReservation
        fields = [
            'id',
            'study_room',
            'student',
            'reservation_date',
            'start_time',
            'end_time',
        ]
        read_only_fields = ['id', 'student']

    def validate(self, attrs):
        if attrs['start_time'] >= attrs['end_time']:
            raise serializers.ValidationError(
                "The end date must be later than the start date."
            )

        conflict = StudyRoomReservation.objects.filter(
            study_room=attrs['study_room'],
            reservation_date=attrs['reservation_date'],
        ).filter(
            Q(
                start_time__lt=attrs['end_time'],
                end_time__gt=attrs['start_time'],
            )
        ).exists()

        if conflict:
            raise serializers.ValidationError(
                "This study room is already reserved during this time slot."
            )

        return attrs