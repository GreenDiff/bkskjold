# Football Team Fines Manager

A Streamlit web application for managing football team fines based on Spond attendance data.

## Features

- 🔄 **Automatic Sync**: Connects to Spond API to fetch team events and attendance data
- 💰 **Fine Calculation**: Automatically calculates fines for missing training/matches
- 📊 **Dashboard**: Visual overview of team fines and payment status
- 👥 **Player Management**: Track individual player fines and payment history
- 🔧 **Admin Panel**: Manage payments and configure fine amounts
- 📈 **Analytics**: Charts and statistics for fine trends

## Fine Types

- **Missing Training**: Configurable fine for missing training sessions
- **Missing Match**: Higher fine for missing matches
- **Late Response**: Fine for late responses to event invitations

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Spond Credentials**
   - Copy your Spond credentials from `config.py.sample` 
   - Edit `app_config.py` with your actual credentials:
     ```python
     SPOND_USERNAME = 'your_spond_username@email.com'
     SPOND_PASSWORD = 'your_spond_password'
     GROUP_ID = 'your_spond_group_id'
     ```

3. **Configure Fine Amounts**
   - Edit `app_config.py` to set your fine amounts:
     ```python
     FINE_MISSING_TRAINING = 50  # Amount for missing training
     FINE_MISSING_MATCH = 100    # Amount for missing match
     FINE_LATE_RESPONSE = 25     # Amount for late response
     ```

4. **Run the Application**
   ```bash
   streamlit run app.py
   ```

5. **Access the App**
   - Open your browser to `http://localhost:8501`
   - Click "Sync with Spond" to fetch initial data

## Usage Guide

### Dashboard
- View overall statistics and recent sync status
- Quick overview of total fines, payments, and outstanding amounts

### Player Fines
- See fines breakdown by player
- Visual charts showing payment rates and top offenders
- Sortable table with payment status

### Detailed Fines
- Complete list of all fines with filtering options
- Filter by player, payment status, and date range
- Export data for external use

### Admin Panel
- Mark fines as paid when payments are received
- Export fines data to CSV
- Manage fine configuration
- Clear data if needed (use with caution)

## Data Storage

- Fines data is stored in `fines_data.json`
- Backup this file regularly to prevent data loss
- Data persists between app restarts

## Configuration Options

Edit `app_config.py` to customize:

- **Fine Amounts**: Set different amounts for different violation types
- **Response Thresholds**: Configure what constitutes a "late" response
- **Database File**: Change where fines data is stored

## Troubleshooting

### Connection Issues
- Verify Spond credentials in `app_config.py`
- Check internet connection
- Ensure GROUP_ID is correct

### Data Issues
- Try refreshing data using the "Refresh Data" button
- Re-sync with Spond if events are missing
- Check that the group has recent events

### Performance
- Limit sync to recent events (30-60 days) for better performance
- Clear old data periodically if needed

## Security Notes

- Keep your Spond credentials secure
- Don't commit `app_config.py` with real credentials to version control
- Run the app on a secure network if handling sensitive team data

## Support

For issues or feature requests, check the Spond API documentation or modify the code to fit your team's specific needs.