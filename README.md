# YouTube Downloader

A desktop application built with Python and Tkinter that allows users to download videos from YouTube. The application supports both video and audio downloads, user authentication, and download history tracking.

## Features

- Download YouTube videos in up to 1080p quality
- Download audio-only in MP3 format
- User authentication system
- Track download history
- User-friendly GUI interface
- Copy/paste support for URLs
- Video length and title display
- Account management capabilities

## Prerequisites

Before running the application, make sure you have the following installed:

1. Python 3.x
2. FFmpeg (required for audio conversion)
   - Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/youtube-downloader.git
cd Youtube-Downloader
```

2. Install required Python packages:
```bash
pip install yt-dlp
pip install python-dotenv
pip install mysql-connector-python
```

3. Set up the MySQL database:
   - Create a new database
   - Import the provided SQL schema (see Database Setup section)

4. Configure environment variables:
   - Create a `.env` file in the project root
   - Add the following configurations:
```
HOST=your_mysql_host
USER=your_mysql_user
PASSWORD=your_mysql_password
DATABASE=your_database_name
```

5. Create required directories:
```bash
mkdir Downloads
mkdir data
```

## Database Setup

Execute the following SQL commands to create the necessary tables:

```sql
CREATE TABLE Users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE VideoHistory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    link TEXT NOT NULL,
    length INT NOT NULL,
    userId INT,
    FOREIGN KEY (userId) REFERENCES Users(id)
);
```

## Usage

1. Start the application:
```bash
python main.py
```

2. Using the application:
   - **Download without account**:
     1. Paste a YouTube URL
     2. Select format (Video/Audio)
     3. Click Download

   - **Create an account**:
     1. Click "Sign in" in the User menu
     2. Enter your email and password
     3. Confirm password
     4. Click "Sign in"

   - **Login to existing account**:
     1. Click "Log in" in the User menu
     2. Enter your credentials
     3. Click "Log in"

   - **View download history** (requires login):
     1. Click on your email in the top menu
     2. Select "View Download History"

   - **Modify account information** (requires login):
     1. Click on your email in the top menu
     2. Select "View Account Info"
     3. Click "Modify Information"

## Customization

You can customize the application appearance by adding:
- `AppIcon.png` in the `data` folder for the application icon
- `AppLogo.png` in the `data` folder for the application logo

If these images are not present, the application will use text-based alternatives.

## Security Notes

- Passwords are stored in plain text. For production use, implement proper password hashing.
- Consider implementing input sanitization for database operations.
- Use secure connection strings for database access.

## Troubleshooting

1. **FFmpeg errors**:
   - Ensure FFmpeg is properly installed and accessible from PATH
   - For Windows users, restart the computer after adding FFmpeg to PATH

2. **Database connection issues**:
   - Verify MySQL service is running
   - Check `.env` file configurations
   - Ensure database user has proper permissions

3. **Download errors**:
   - Check internet connection
   - Verify YouTube URL is valid
   - Ensure "Downloads" directory exists and is writable

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for the downloading functionality
- [FFmpeg](https://ffmpeg.org/) for audio conversion

