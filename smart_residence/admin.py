from django.contrib import admin
from .models import Student, Apartment, Room, SmartDevice, News

class ConnectedDeviceInline(admin.TabularInline):
    model = SmartDevice
    extra = 0
    fields = ('name', 'device_type', 'is_on', 'power_consumption', 'brand', 'connectivity', 'battery_level', 'last_interaction')

class RoomInline(admin.TabularInline):
    model = Room
    extra = 0
    show_change_link = True

class ApartmentInline(admin.StackedInline):
    model = Apartment
    extra = 0
    show_change_link = True

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('username', 'last_name', 'level', 'total_points')
    fieldsets = (
        ('Personal Information', {
            'fields': ('username', 'first_name', 'last_name', 'email', 'phone_number', 'student_id', 'age', 'sex')
        }),
        ('Statistics & Levels', {
            'fields': ('login_points', 'browsing_points')
        }),
    )
    inlines = [ApartmentInline]

@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('apartment_number', 'occupant', 'address')
    inlines = [RoomInline]

    def has_module_permission(self, request):
        return False

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'apartment', 'display_device_count')
    inlines = [ConnectedDeviceInline]

    def display_device_count(self, obj):
        return f"{obj.devices.count()} device(s)"
    display_device_count.short_description = "Number of devices"

    def has_module_permission(self, request):
        return False

@admin.register(SmartDevice)
class ConnectedDeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'device_type', 'is_on', 'power_consumption', 'brand', 'connectivity', 'battery_level', 'room')
    list_filter = ('device_type', 'is_on', 'connectivity', 'room')
    search_fields = ('name', 'brand', 'description')

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'publication_date')
    list_filter = ('category', 'publication_date')
    search_fields = ('title', 'content')