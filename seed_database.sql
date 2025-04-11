-- Connect to the database
\c "Prasha_care"

-- Insert roles
INSERT INTO roles (role_id, role_name) VALUES 
(gen_random_uuid(), 'admin'),
(gen_random_uuid(), 'doctor'),
(gen_random_uuid(), 'patient');

-- Insert admin user (password: admin123)
INSERT INTO users (user_id, title, first_name, last_name, gender, email, password_hash, roles, is_active)
VALUES (
    gen_random_uuid(),
    'Mr.',
    'Admin',
    'User',
    'M',
    'admin@prasha.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- hashed 'admin123'
    'admin',
    TRUE
);

-- Insert doctor user (password: doctor123)
WITH doctor_user AS (
    INSERT INTO users (user_id, title, first_name, last_name, gender, email, password_hash, roles, is_active)
    VALUES (
        gen_random_uuid(),
        'Dr.',
        'John',
        'Smith',
        'M',
        'doctor@prasha.com',
        '$2b$12$S7RKX1KGnrOApmVvTDZzfODwF0kV88JTJ1vXD7GmMQXHPP2vYqvLe', -- hashed 'doctor123'
        'doctor',
        TRUE
    )
    RETURNING user_id
)
INSERT INTO doctors (
    doctor_id, user_id, title, first_name, last_name, dob, gender, 
    language, address, phone, email, specialization, consultation_fee, treatment
)
SELECT 
    gen_random_uuid(), user_id, 'Dr.', 'John', 'Smith', '1980-01-15', 'M',
    'English', '123 Medical Center, New York', '555-123-4567', 'doctor@prasha.com',
    'Cardiology', 150.00, 'General cardiology consultation'
FROM doctor_user;

-- Insert patient user (password: patient123)
WITH patient_user AS (
    INSERT INTO users (user_id, title, first_name, last_name, gender, email, password_hash, roles, is_active)
    VALUES (
        gen_random_uuid(),
        'Ms.',
        'Jane',
        'Doe',
        'F',
        'patient@prasha.com',
        '$2b$12$1InE4nJwSM.JZSQtl5HLR.Mhx6EBVSz9qHf9XQQVIzLjVIHMxvGGS', -- hashed 'patient123'
        'patient',
        TRUE
    )
    RETURNING user_id
)
INSERT INTO patients (
    patient_id, user_id, title, first_name, last_name, dob, gender,
    language, address, phone, email, interests, treatment
)
SELECT 
    gen_random_uuid(), user_id, 'Ms.', 'Jane', 'Doe', '1990-05-20', 'F',
    'English', '456 Residential St, New York', '555-987-6543', 'patient@prasha.com',
    'Yoga, Meditation', 'Regular check-up'
FROM patient_user;

-- Insert doctor availability
WITH doctor_data AS (
    SELECT doctor_id FROM doctors WHERE email = 'doctor@prasha.com' LIMIT 1
)
INSERT INTO doctors_availability (availability_id, doctor_id, day_of_week, start_time, end_time)
SELECT 
    gen_random_uuid(), 
    doctor_id, 
    day, 
    CURRENT_DATE + '09:00:00'::time, 
    CURRENT_DATE + '17:00:00'::time
FROM doctor_data, unnest(ARRAY['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']) AS day;

-- Insert appointment status options
INSERT INTO appointment_status (status_code, description) VALUES
('Scheduled', 'Appointment is scheduled'),
('Completed', 'Appointment has been completed'),
('Cancelled', 'Appointment has been cancelled');
