from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timezone
import json
import os
from flask import current_app

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_google_calendar_service(user):
    """Create Google Calendar service object for the given user."""
    try:
        # Get service account info from UserSettings
        if not user.google_service_account_file:
            raise ValueError("Google service account credentials not found")
        
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(user.google_service_account_file),
            scopes=SCOPES,
            subject=user.email
        )

        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        current_app.logger.error(f"Error creating Google Calendar service: {str(e)}")
        return None

def create_calendar_event(user, schedule):
    """Create a Google Calendar event from a schedule."""
    try:
        service = get_google_calendar_service(user)
        if not service:
            return None

        calendar_id = user.google_calendar_id
        if not calendar_id:
            raise ValueError("Google Calendar ID not configured")

        event = {
            'summary': schedule.title,
            'description': schedule.description or '',
            'start': {
                'dateTime': schedule.start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': schedule.end_time.isoformat(),
                'timeZone': 'UTC',
            },
        }

        # Add attendees if lead or opportunity is associated
        attendees = []
        if schedule.lead and schedule.lead.email:
            attendees.append({'email': schedule.lead.email})
        event['attendees'] = attendees

        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates='all'
        ).execute()

        return created_event['id']
    except Exception as e:
        current_app.logger.error(f"Error creating Google Calendar event: {str(e)}")
        return None

def update_calendar_event(user, schedule):
    """Update an existing Google Calendar event."""
    try:
        if not schedule.google_event_id:
            return create_calendar_event(user, schedule)

        service = get_google_calendar_service(user)
        if not service:
            return None

        calendar_id = user.google_calendar_id
        if not calendar_id:
            raise ValueError("Google Calendar ID not configured")

        # Get existing event
        try:
            service.events().get(
                calendarId=calendar_id,
                eventId=schedule.google_event_id
            ).execute()
        except HttpError:
            # If event doesn't exist, create new one
            return create_calendar_event(user, schedule)

        event = {
            'summary': schedule.title,
            'description': schedule.description or '',
            'start': {
                'dateTime': schedule.start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': schedule.end_time.isoformat(),
                'timeZone': 'UTC',
            },
        }

        # Add attendees if lead or opportunity is associated
        attendees = []
        if schedule.lead and schedule.lead.email:
            attendees.append({'email': schedule.lead.email})
        event['attendees'] = attendees

        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=schedule.google_event_id,
            body=event,
            sendUpdates='all'
        ).execute()

        return updated_event['id']
    except Exception as e:
        current_app.logger.error(f"Error updating Google Calendar event: {str(e)}")
        return None

def delete_calendar_event(user, schedule):
    """Delete a Google Calendar event."""
    try:
        if not schedule.google_event_id:
            return True

        service = get_google_calendar_service(user)
        if not service:
            return False

        calendar_id = user.google_calendar_id
        if not calendar_id:
            raise ValueError("Google Calendar ID not configured")

        try:
            service.events().delete(
                calendarId=calendar_id,
                eventId=schedule.google_event_id
            ).execute()
        except HttpError as e:
            if e.resp.status == 404:  # Event already deleted
                return True
            raise

        return True
    except Exception as e:
        current_app.logger.error(f"Error deleting Google Calendar event: {str(e)}")
        return False
