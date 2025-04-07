from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime
import json
import aiohttp

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins during development
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Configure Hugging Face API
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

# Google OAuth configuration
CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URI = "http://localhost:8000/oauth2callback"

# Store user credentials (in memory for demo purposes)
user_credentials = {}

class MeetingRequest(BaseModel):
    title: str
    description: str
    start_time: str
    end_time: str
    participants: List[str]

class SummaryRequest(BaseModel):
    transcript: str

def get_google_calendar_service(credentials_dict=None):
    if not credentials_dict:
        return None
    
    try:
        credentials = Credentials.from_authorized_user_info(credentials_dict)
        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error creating calendar service: {e}")
        return None

@app.get("/")
async def root():
    return {"message": "AI Meeting Assistant API"}

@app.post("/schedule-meeting")
async def schedule_meeting(meeting: MeetingRequest):
    try:
        # Check if user is authenticated
        if not user_credentials:
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'  # Force consent screen
            )
            return {"auth_required": True, "auth_url": authorization_url}

        # Get calendar service
        service = get_google_calendar_service(user_credentials)
        if not service:
            raise HTTPException(status_code=401, detail="Failed to create calendar service")

        # Format dates for Google Calendar API
        start_time = datetime.fromisoformat(meeting.start_time.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(meeting.end_time.replace('Z', '+00:00'))

        # Create calendar event
        event = {
            'summary': meeting.title,
            'description': meeting.description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
            'attendees': [{'email': email} for email in meeting.participants],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 30},
                ],
            },
            'guestsCanSeeOtherGuests': True,
            'guestsCanModify': False,
            'sendUpdates': 'all'  # This ensures emails are sent to all attendees
        }

        # Insert the event with email notifications
        event = service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all'  # This will send email notifications to all attendees
        ).execute()
        
        return {
            "message": "Meeting scheduled successfully!",
            "event_id": event['id'],
            "event_link": event.get('htmlLink'),
            "attendees": [attendee['email'] for attendee in event.get('attendees', [])]
        }

    except Exception as e:
        if "access_denied" in str(e):
            raise HTTPException(status_code=403, detail="Please make sure you're using a test user account. Contact the developer if you need access.")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-summary")
async def generate_summary_endpoint(request: SummaryRequest):
    """Generate meeting summary endpoint."""
    try:
        if not request.transcript:
            raise HTTPException(status_code=400, detail="Transcript cannot be empty")

        # Call the generate_summary function with the transcript
        summary = await generate_summary_service(request.transcript)
        return {"summary": summary}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def generate_summary_service(transcript: str) -> str:
    """Generate meeting summary using Hugging Face's API."""
    try:
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # BART model expects a simpler input format
        data = {
            "inputs": transcript,
            "parameters": {
                "max_length": 300,
                "min_length": 100,
                "do_sample": False
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(HUGGINGFACE_API_URL, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    # BART model returns a list with a single summary
                    return result[0]["summary_text"].strip()
                else:
                    response_text = await response.text()
                    error_message = f"Hugging Face API Error (Status {response.status}): {response_text}"
                    raise Exception(error_message)
    except Exception as e:
        raise Exception(f"Failed to generate summary: {str(e)}")

@app.get("/auth/google")
async def google_auth():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent screen
    )
    return RedirectResponse(authorization_url)

@app.get("/oauth2callback")
async def oauth2callback(code: str):
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Convert credentials to a dictionary
        creds_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        # Update user credentials
        user_credentials.update(creds_dict)
        
        return RedirectResponse(url="http://localhost:3001")
    except Exception as e:
        if "access_denied" in str(e):
            raise HTTPException(status_code=403, detail="Please make sure you're using a test user account. Contact the developer if you need access.")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint that doesn't require any external API calls."""
    return {"message": "Backend is working correctly!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 