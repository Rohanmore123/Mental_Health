import psycopg2
from urllib.parse import unquote

# Database connection string
db_url = "postgresql://postgres:Raje%4012345@localhost:5432/Prasha_care"

# Parse the connection string
parts = db_url.split("://")[1].split("@")
user_pass = parts[0].split(":")
host_port_db = parts[1].split("/")
host_port = host_port_db[0].split(":")

username = user_pass[0]
password = unquote(user_pass[1])
host = host_port[0]
port = host_port[1] if len(host_port) > 1 else "5432"
database = host_port_db[1]

# Connect to the database
conn = psycopg2.connect(
    host=host,
    port=port,
    database=database,
    user=username,
    password=password
)

# Create a cursor
cur = conn.cursor()

# Add mobile_number column to users table if it doesn't exist
cur.execute("""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'mobile_number'
    ) THEN
        ALTER TABLE users ADD COLUMN mobile_number VARCHAR(20) UNIQUE;
    END IF;
END $$;
""")

print("Mobile number column added to users table.")

# Commit the changes
conn.commit()

# Close the connection
cur.close()
conn.close()
