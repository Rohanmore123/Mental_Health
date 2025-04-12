# Import models to make them available when importing the package
from app.models.users import User, Patient, Doctor, DoctorAvailability, Role, UserRole
from app.models.appointments import Appointment, AppointmentStatus
from app.models.medical import Prescription, MedicalHistory
from app.models.communication import ChatMessage, Notification, UserNotificationPreference, NotificationLog, Otp, Mydiary, MyTimeline, MyTimelineEvent
from app.models.ratings import Rating
