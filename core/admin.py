from django.contrib import admin

# Register your models here.

# core/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    PatientProfile,
    DoctorProfile,
    DoctorPatientConnection,
    Diagnosis,
    Medication,
    Prescription,
    PrescriptionItem,
    Notification
)

# --- Inline Admin Definitions ---
# These allow editing related models directly within the parent model's admin page.

class PatientProfileInline(admin.StackedInline):
    """
    Allows editing PatientProfile directly within the User admin page
    if the user's role is 'patient'.
    """
    model = PatientProfile
    can_delete = False  # Don't allow deleting the profile from the User admin
    verbose_name_plural = 'Patient Profile'
    fk_name = 'user'


class DoctorProfileInline(admin.StackedInline):
    """
    Allows editing DoctorProfile directly within the User admin page
    if the user's role is 'doctor'.
    """
    model = DoctorProfile
    can_delete = False
    verbose_name_plural = 'Doctor Profile'
    fk_name = 'user'


# --- Custom User Admin ---
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    Customizes the display of the User model in the admin.
    Includes inlines for patient and doctor profiles.
    """
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'role')
    list_filter = BaseUserAdmin.list_filter + ('role',)
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role and Profile', {'fields': ('role', 'phone_number', 'profile_picture', 'address_line1', 'city', 'state_province', 'postal_code', 'country')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role and Profile', {'fields': ('role', 'first_name', 'last_name', 'email', 'phone_number', 'profile_picture', 'address_line1', 'city', 'state_province', 'postal_code', 'country')}),
    )
    # inlines = [PatientProfileInline, DoctorProfileInline] # Original line causing both to show initially

    # Conditionally show the relevant inline based on the 'role' field when *editing* an existing user:
    def get_inlines(self, request, obj=None):
        if obj: # obj is the User instance being edited
            if obj.role == 'patient':
                return [PatientProfileInline]
            elif obj.role == 'doctor':
                return [DoctorProfileInline]
        return [] # No inlines when adding a new user, or if role is not patient/doctor

# --- Patient Profile Admin ---
@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    """
    Customizes the display of PatientProfile in the admin.
    """
    list_display = ('user_email', 'user_full_name', 'date_of_birth', 'blood_group')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'blood_group')
    list_filter = ('blood_group',)
    autocomplete_fields = ['user']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_full_name.short_description = 'Patient Name'

# --- Doctor Profile Admin ---
@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    """
    Customizes the display of DoctorProfile in the admin.
    """
    list_display = ('user_email', 'user_full_name', 'specialization', 'medical_license_number', 'is_verified')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'specialization', 'medical_license_number')
    list_filter = ('specialization', 'is_verified')
    list_editable = ('is_verified',)
    autocomplete_fields = ['user']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def user_full_name(self, obj):
        return f"Dr. {obj.user.first_name} {obj.user.last_name}"
    user_full_name.short_description = 'Doctor Name'

# --- Doctor-Patient Connection Admin ---
@admin.register(DoctorPatientConnection)
class DoctorPatientConnectionAdmin(admin.ModelAdmin):
    """
    Customizes the display of DoctorPatientConnection in the admin.
    """
    list_display = ('patient_email', 'doctor_email', 'status', 'request_date', 'response_date')
    search_fields = ('patient__user__email', 'doctor__user__email', 'patient__user__first_name', 'doctor__user__first_name')
    list_filter = ('status', 'request_date')
    autocomplete_fields = ['patient', 'doctor']

    def patient_email(self, obj):
        return obj.patient.user.email
    patient_email.short_description = 'Patient Email'

    def doctor_email(self, obj):
        return obj.doctor.user.email
    doctor_email.short_description = 'Doctor Email'

# --- Inline for Prescription Items within Prescription Admin ---
class PrescriptionItemInline(admin.TabularInline):
    """
    Allows editing PrescriptionItems directly within the Prescription admin page.
    """
    model = PrescriptionItem
    extra = 1
    autocomplete_fields = ['medication']

# --- Prescription Admin ---
@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    """
    Customizes the display of Prescription in the admin.
    Includes an inline for PrescriptionItems.
    """
    list_display = ('id', 'diagnosis_info', 'patient_email', 'doctor_email', 'date_prescribed', 'is_active')
    search_fields = (
        'diagnosis__connection__patient__user__email',
        'diagnosis__connection__doctor__user__email',
        'diagnosis__id'
    )
    list_filter = ('is_active', 'date_prescribed')
    list_editable = ('is_active',)
    inlines = [PrescriptionItemInline]
    autocomplete_fields = ['diagnosis']

    def diagnosis_info(self, obj):
        return f"Diagnosis ID: {obj.diagnosis.id}"
    diagnosis_info.short_description = 'Diagnosis'

    def patient_email(self, obj):
        return obj.diagnosis.patient.user.email
    patient_email.short_description = 'Patient'

    def doctor_email(self, obj):
        return obj.diagnosis.doctor.user.email
    doctor_email.short_description = 'Doctor'


# --- Diagnosis Admin ---
@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    """
    Customizes the display of Diagnosis in the admin.
    """
    list_display = ('id', 'patient_email', 'doctor_email', 'date_recorded', 'follow_up_date')
    search_fields = (
        'connection__patient__user__email',
        'connection__doctor__user__email',
        'symptoms',
        'diagnosis_details'
    )
    list_filter = ('date_recorded', 'follow_up_date', 'connection__doctor__specialization')
    autocomplete_fields = ['connection']

    def patient_email(self, obj):
        return obj.connection.patient.user.email
    patient_email.short_description = 'Patient'

    def doctor_email(self, obj):
        return obj.connection.doctor.user.email
    doctor_email.short_description = 'Doctor'

# --- Medication Admin ---
@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    """
    Customizes the display of Medication in the admin.
    """
    list_display = ('name', 'generic_name', 'category', 'manufacturer')
    search_fields = ('name', 'generic_name', 'category', 'manufacturer')
    list_filter = ('category', 'manufacturer')

# --- Prescription Item Admin ---
# This needs to be registered for autocomplete_fields in NotificationAdmin to work.
@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    """
    Customizes the display of PrescriptionItem in the admin.
    Primarily for supporting autocomplete_fields, but can be used for direct viewing/editing.
    """
    list_display = ('prescription_info', 'medication_name', 'dosage', 'frequency', 'start_date', 'end_date')
    search_fields = ('prescription__diagnosis__connection__patient__user__email', 'medication__name', 'prescription__id')
    list_filter = ('medication__category', 'start_date', 'end_date')
    autocomplete_fields = ['prescription', 'medication'] # For easier selection when editing directly

    def prescription_info(self, obj):
        return f"Presc. ID: {obj.prescription.id} (Diag. ID: {obj.prescription.diagnosis.id})"
    prescription_info.short_description = "Prescription"

    def medication_name(self, obj):
        return obj.medication.name
    medication_name.short_description = "Medication"


# --- Notification Admin ---
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Customizes the display of Notification in the admin.
    """
    list_display = ('user_email', 'message_summary', 'notification_type', 'notification_time', 'is_read', 'created_at')
    search_fields = ('user__email', 'message')
    list_filter = ('notification_type', 'is_read', 'notification_time', 'created_at')
    list_editable = ('is_read',)
    readonly_fields = ('created_at',)
    autocomplete_fields = ['user', 'prescription_item', 'diagnosis', 'connection_request_ref']


    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def message_summary(self, obj):
        return (obj.message[:75] + '...') if len(obj.message) > 75 else obj.message
    message_summary.short_description = 'Message'


