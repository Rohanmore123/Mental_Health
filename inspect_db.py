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

# Get all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
""")
tables = cur.fetchall()

print("Tables in the database:")
for table in tables:
    table_name = table[0]
    print(f"\n{table_name}:")
    
    # Get columns for each table
    cur.execute(f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = '{table_name}'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    
    for column in columns:
        col_name, data_type, is_nullable = column
        nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
        print(f"  {col_name} ({data_type}) {nullable}")

# Close the connection
cur.close()
conn.close()
