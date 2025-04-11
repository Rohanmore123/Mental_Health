@echo off
echo Setting up Prasha_care database...

REM Run the create_database.sql script
echo Creating database and tables...
psql -U postgres -f create_database.sql

REM Run the seed_database.sql script
echo Seeding database with initial data...
psql -U postgres -f seed_database.sql

echo Database setup complete!
pause
