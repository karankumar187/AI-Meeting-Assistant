# AI Meeting Assistant

A web application that helps you schedule meetings and generate summaries from meeting transcripts using AI.

## Features

- Schedule meetings with Google Calendar integration
- Generate meeting summaries using AI
- Modern and responsive user interface
- Google OAuth authentication

## Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account with Calendar API enabled
- Hugging Face API key
- Web browser

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-meeting-assistant
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your Hugging Face API key:
     ```
     HUGGINGFACE_API_KEY=your_huggingface_api_key_here
     ```

4. Set up Google OAuth:
   - Go to the Google Cloud Console
   - Create a new project or select an existing one
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials
   - Download the credentials and save them as `credentials.json` in the project root
   - Update the redirect URIs in the Google Cloud Console to include `http://localhost:8000/oauth2callback`

## Running the Application

1. Start the backend server:
```bash
python main.py
```

2. Open the frontend:
   - Open `index.html` in your web browser
   - Or serve it using a local server (e.g., Python's `http.server`)

## Usage

### Scheduling Meetings

1. Fill in the meeting details:
   - Title
   - Description
   - Start time
   - End time
   - Participant email addresses (one per line)
2. Click "Schedule Meeting"
3. Authenticate with Google if prompted
4. The meeting will be scheduled in your Google Calendar

### Generating Summaries

1. Paste your meeting transcript into the text area
2. Click "Generate Summary"
3. The AI will generate a concise summary of the meeting

## Security Notes

- Never commit your `.env` file or `credentials.json` to version control
- Keep your API keys and credentials secure
- Use environment variables for sensitive information

## Troubleshooting

- If you encounter CORS issues, ensure the backend server is running and accessible
- For Google OAuth issues, verify your credentials and redirect URIs
- Check the browser console for any JavaScript errors
- Verify your Hugging Face API key is valid and has sufficient quota

## License

This project is licensed under the MIT License - see the LICENSE file for details. 