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

    def validate_room(self, value):
        """
        Verify that the specified item belongs to the authenticated user.
        """
        user = self.context['request'].user

        # If the user is not the owner of the apartment linked to this room
        if value.apartment.occupant != user:
            raise serializers.ValidationError(
                "You cannot assign a device to a room that does not belong to you."
            )
        return value

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

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = [
            'id',
            'title',
            'content',
            'image',
            'publication_date',
            'category'
        ]