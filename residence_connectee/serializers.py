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
        """Ensure the target room belongs to the authenticated student's apartment."""
        user = self.context['request'].user
        if value.apartment.occupant != user:
            raise serializers.ValidationError(
                "You cannot assign a device to a room that does not belong to your apartment."
            )
        return value

    def validate(self, attrs):
        """Enforce zero power consumption when device is turned off."""
        is_on = attrs.get('is_on', getattr(self.instance, 'is_on', False))

        if not is_on:
            attrs['power_consumption'] = 0.0

        return attrs

class StudyRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyRoom
        fields = [
            'id',
            'name',
            'capacity',
            'description'
        ]

    def validate_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be strictly greater than 0.")
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