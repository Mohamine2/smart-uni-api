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
        # Retrieve values from incoming payload, falling back to existing instance data (useful for PATCH)
        study_room = attrs.get('study_room', getattr(self.instance, 'study_room', None))
        date = attrs.get('reservation_date', getattr(self.instance, 'reservation_date', None))
        start_time = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end_time = attrs.get('end_time', getattr(self.instance, 'end_time', None))

        # 1. Chronological order check
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError({
                'end_time': "End time must be later than start time."
            })

        # 2. Overlapping reservation check
        if study_room and date and start_time and end_time:
            conflicts = StudyRoomReservation.objects.filter(
                study_room=study_room,
                reservation_date=date,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            # Ignore the current instance when updating (PATCH / PUT)
            if self.instance:
                conflicts = conflicts.exclude(pk=self.instance.pk)

            if conflicts.exists():
                raise serializers.ValidationError(
                    "This study room is already booked during the selected time slot."
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