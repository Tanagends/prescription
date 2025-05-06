# core/models.py (or in a dedicated 'users' app)
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings # To get the User model

# --- User Model ---
class User(AbstractUser):
    """
    Custom User model to differentiate between Patient and Doctor roles
    and add any other common fields.
    """
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('admin', 'Admin'), # For site administrators
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    email = models.EmailField(unique=True, help_text="Required. Used for login.")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    # Common fields for all users
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'email' # Use email as the unique identifier for login
    REQUIRED_FIELDS = ['username'] # username is still required by AbstractUser for createsuperuser

    def __str__(self):
        return self.email

# --- Patient Profile ---
class PatientProfile(models.Model):
    """
    Stores additional information specific to patients.
    Linked one-to-one with the User model.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    blood_group = models.CharField(max_length=10, blank=True, null=True, help_text="e.g., A+, O-, AB+")
    allergies = models.TextField(blank=True, null=True, help_text="List any known allergies.")
    medical_conditions = models.TextField(blank=True, null=True, help_text="List any chronic or significant medical conditions.")
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Patient: {self.user.first_name} {self.user.last_name} ({self.user.email})"

# --- Doctor Profile ---
class DoctorProfile(models.Model):
    """
    Stores additional information specific to doctors.
    Linked one-to-one with the User model.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, related_name='doctor_profile')
    specialization = models.CharField(max_length=100, blank=True, null=True)
    medical_license_number = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="Should be verified.")
    clinic_hospital_name = models.CharField(max_length=200, blank=True, null=True)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_verified = models.BooleanField(default=False, help_text="Set to true once credentials (e.g., license) are verified by an admin.")
    # Other doctor-specific fields: availability (could be a separate model), education, awards.

    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} - {self.specialization} ({self.user.email})"

# --- Doctor-Patient Connection Model ---
class DoctorPatientConnection(models.Model):
    """
    Manages the relationship/request between a doctor and a patient.
    A patient requests connection, and a doctor accepts/rejects.
    """
    STATUS_CHOICES = (
        ('pending_approval_by_doctor', 'Pending Approval by Doctor'),
        ('approved', 'Approved'),
        ('rejected_by_doctor', 'Rejected by Doctor'),
        ('terminated_by_patient', 'Terminated by Patient'),
        ('terminated_by_doctor', 'Terminated by Doctor'),
    )
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='doctor_connections')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='patient_connections')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending_approval_by_doctor')
    request_date = models.DateTimeField(auto_now_add=True, help_text="Date when patient initiated the request.")
    response_date = models.DateTimeField(null=True, blank=True, help_text="Date when doctor responded to the request.")
    last_interaction_date = models.DateTimeField(null=True, blank=True, help_text="Tracks the last significant interaction for this connection.")

    class Meta:
        unique_together = ('patient', 'doctor') # A patient can only have one active/pending connection request with a specific doctor at a time.
        ordering = ['-request_date']

    def __str__(self):
        return f"{self.patient.user.email} - {self.doctor.user.email} ({self.get_status_display()})"

# --- Diagnosis Model ---
class Diagnosis(models.Model):
    """
    Represents a single medical diagnosis event by a doctor for a patient
    within an established connection.
    """
    connection = models.ForeignKey(DoctorPatientConnection, on_delete=models.CASCADE, related_name='diagnoses',
                                   help_text="The doctor-patient connection this diagnosis belongs to.")
    date_recorded = models.DateTimeField(default=timezone.now)
    symptoms = models.TextField(blank=True, null=True, help_text="Patient's reported symptoms.")
    diagnosis_details = models.TextField(help_text="Doctor's detailed diagnosis.")
    treatment_plan = models.TextField(blank=True, null=True, help_text="Overall treatment plan, may include lifestyle changes, etc.")
    follow_up_date = models.DateField(null=True, blank=True, help_text="Recommended follow-up date.")

    def __str__(self):
        return f"Diagnosis for {self.connection.patient.user.email} by {self.connection.doctor.user.email} on {self.date_recorded.strftime('%Y-%m-%d')}"

    @property
    def patient(self):
        return self.connection.patient

    @property
    def doctor(self):
        return self.connection.doctor

    class Meta:
        ordering = ['-date_recorded']
        verbose_name_plural = "Diagnoses"

# --- Medication Model ---
class Medication(models.Model):
    """
    Represents a specific medication.
    This can be a master list of medications available in the system, potentially managed by admins.
    """
    name = models.CharField(max_length=200, unique=True, help_text="Official name of the medication.")
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    manufacturer = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Antibiotic, Analgesic, Antihypertensive")
    description = models.TextField(blank=And, null=True, help_text="General description, common uses, important warnings.")

    def __str__(self):
        return self.name

# --- Prescription Model ---
class Prescription(models.Model):
    """
    Represents a set of medications prescribed as part of a diagnosis.
    """
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE, related_name='prescriptions')
    date_prescribed = models.DateTimeField(default=timezone.now)
    notes_for_patient = models.TextField(blank=True, null=True, help_text="Overall notes for the patient regarding this set of medications.")
    is_active = models.BooleanField(default=True, help_text="Is this prescription currently active? (e.g., for refills or current treatment)")

    def __str__(self):
        return f"Prescription for Diagnosis ID {self.diagnosis.id} on {self.date_prescribed.strftime('%Y-%m-%d')}"

    @property
    def patient(self):
        return self.diagnosis.patient

    @property
    def doctor(self):
        return self.diagnosis.doctor

    class Meta:
        ordering = ['-date_prescribed']

# --- Prescription Item Model ---
class PrescriptionItem(models.Model):
    """
    Details of each individual medication within a prescription.
    """
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medication = models.ForeignKey(Medication, on_delete=models.PROTECT, help_text="The specific medication being prescribed.")
    dosage = models.CharField(max_length=100, help_text="e.g., '1 tablet', '10mg', '5ml'")
    route = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., 'Oral', 'Topical', 'Intravenous'")
    frequency = models.CharField(max_length=100, help_text="e.g., 'Twice a day', 'Every 6 hours', 'As needed'")
    duration_value = models.PositiveIntegerField(null=True, blank=True, help_text="Numerical value for duration (e.g., 7, 30).")
    DURATION_UNIT_CHOICES = (
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('indefinite', 'Indefinite'),
    )
    duration_unit = models.CharField(max_length=10, choices=DURATION_UNIT_CHOICES, null=True, blank=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True, help_text="Automatically calculated if duration is provided, or can be set manually.")
    instructions = models.TextField(blank=True, null=True, help_text="Specific instructions for this medication, e.g., 'Take with food', 'Avoid sunlight'.")
    refills_allowed = models.PositiveIntegerField(default=0, help_text="Number of refills allowed.")

    def save(self, *args, **kwargs):
        if self.start_date and self.duration_value and self.duration_unit and not self.end_date:
            if self.duration_unit == 'days':
                self.end_date = self.start_date + timezone.timedelta(days=self.duration_value)
            elif self.duration_unit == 'weeks':
                self.end_date = self.start_date + timezone.timedelta(weeks=self.duration_value)
            elif self.duration_unit == 'months':
                self.end_date = self.start_date + timezone.timedelta(days=self.duration_value * 30) # Approximation
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.medication.name} - {self.dosage}, {self.frequency}"

# --- Notification Model ---
class Notification(models.Model):
    """
    For medication reminders, appointment reminders, connection request updates, or other alerts.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_time = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    TYPE_CHOICES = (
        ('medication_reminder', 'Medication Reminder'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('connection_request', 'Connection Request Update'),
        ('new_diagnosis', 'New Diagnosis Added'),
        ('new_prescription', 'New Prescription Added'),
        ('general_update', 'General Update'),
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='general_update')
    prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    connection_request_ref = models.ForeignKey(DoctorPatientConnection, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')

    def __str__(self):
        return f"Notification for {self.user.email} ({self.get_notification_type_display()}): {self.message[:50]}"

    class Meta:
        ordering = ['-created_at']

