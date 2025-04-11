# Prasha Care - Mental Health Platform

## Database Population

The database has been populated with:
- 50+ doctors with various specializations
- 100+ patients
- 200+ appointments between doctors and patients

## User Credentials

### Doctor Credentials
All doctors have the password: `doctor123`

Sample doctor accounts:
- Email: doctor1@prasha.com (Dr. Melanie Small - Psychology)
- Email: doctor2@prasha.com (Dr. Anthony Craig - Counseling)
- Email: doctor3@prasha.com (Dr. Thomas Coleman - Neurology)
- Email: doctor4@prasha.com (Dr. Megan Price - Therapy)
- Email: doctor5@prasha.com (Dr. Shannon Coleman - Psychology)

### Patient Credentials
All patients have the password: `patient123`

Sample patient accounts:
- Email: patient1@prasha.com (Kristina Fritz)
- Email: patient2@prasha.com (Adam Reyes)
- Email: patient3@prasha.com (Catherine Garcia)
- Email: patient4@prasha.com (Kurt Mccormick)
- Email: patient5@prasha.com (Shari Walker)

## Appointments

The system contains over 200 appointments between doctors and patients with various:
- Visit reasons (Regular check-up, Anxiety issues, Depression symptoms, Sleep problems, Stress management, Relationship counseling)
- Consultation types (In-person, Video call, Phone call)
- Statuses (Scheduled, Completed, Cancelled)

## Scripts

The following scripts were used to populate the database:

1. `populate_db.py` - Creates doctors and patients
2. `create_appointments_sql.py` - Creates appointments between doctors and patients
3. `display_credentials.py` - Displays user credentials and sample appointments

## How to Run the Application

1. Start the backend server:
   ```
   uvicorn app.main:app --reload
   ```

2. Access the API documentation:
   ```
   http://localhost:8000/docs
   ```

3. Login using the provided credentials to access the system.

## Database Schema

The database contains the following main tables:
- users - User accounts for both doctors and patients
- doctors - Doctor profiles with specializations
- patients - Patient profiles with medical information
- appointments - Appointments between doctors and patients
- doctors_availability - Doctor availability schedules

## Notes

- All passwords are set to simple values for testing purposes. In a production environment, strong passwords should be used.
- The appointment dates are set in the future (within 30 days from the date of creation).
- The database is populated with realistic but fictional data.
