# Football Team Fines Configuration
SPOND_USERNAME = 'linusjb@gmail.com'
SPOND_PASSWORD = 'Nusnus88!'
GROUP_ID = '93B5A75C60B94F27BD74BBF8AC03E91C'

# Fine amounts (in your currency)
FINE_MISSING_TRAINING = 50
FINE_MISSING_MATCH = 100
FINE_LATE_RESPONSE = 25  # Fine for no response within 24 hours of event

# Alternative names for backward compatibility
NO_SHOW_FINE = FINE_MISSING_TRAINING
LATE_RESPONSE_FINE = FINE_LATE_RESPONSE

# Response time limits (hours before event when no response = fine)  
LATE_RESPONSE_THRESHOLD_HOURS = 24
LATE_RESPONSE_HOURS = LATE_RESPONSE_THRESHOLD_HOURS

# Database file for storing fine data
DATABASE_FILE = 'fines_data.json'

# Admin panel credentials
ADMIN_USERNAME = '1'
ADMIN_PASSWORD = '1'  # Change this in production!