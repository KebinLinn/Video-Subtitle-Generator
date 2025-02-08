# Video Subtitle Generator - Flask App

## Overview

This Flask-based web application allows users to upload a **video file (MP4)** and an **audio file (MP3)**. 
The app processes the files by extracting subtitles from the audio using speech recognition, 
synchronizing them with the video, and generating a final video with **embedded subtitles**.

## Features

- Upload an **MP4** video file and an **MP3** audio file.
- Extract subtitles from the audio using Google Speech Recognition.
- Embed generated subtitles into the video.
- Download the final video with **synchronized audio and subtitles**.

---

## Prerequisites

### Required Software
1. **Python 3.x** installed on your system.
2. **FFmpeg** must be installed and its `bin` folder added to the **system PATH**.
   - Download from: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - Add `ffmpeg/bin` to **System Environment Variables**.
3. **ImageMagick** must be installed and its path configured in the script.
   - Update the `IMAGEMAGICK_BINARY` path in `app.py`:
     ```python
     change_settings({"IMAGEMAGICK_BINARY": r"C:\Path\To\ImageMagick\magick.exe"})
     ```
   - Download from: [https://imagemagick.org/script/download.php](https://imagemagick.org/script/download.php)

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/video-subtitle-generator.git
cd video-subtitle-generator
```

### 2. Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
The required packages include:
- Flask
- moviepy
- SpeechRecognition
- pydub
- pysrt

---

## Usage

### 1. Run the Application
```bash
python app.py
```

### 2. Upload Files
- Open your browser and go to `http://127.0.0.1:5000/`.
- Upload an **MP4** video file and an **MP3** audio file.
- Click "Upload and Combine."

### 3. Download the Processed Video
- Once the video processing is complete, a **download link** will be provided.
- Click the link to download the **MP4 file with subtitles**.

---

## File Processing Flow

1. **Upload**: Users upload an MP4 video and an MP3 audio file.
2. **Save**: The files are stored in the `uploads/` folder.
3. **Extract Subtitles**:
   - Convert the MP3 file to WAV.
   - Use **Google Speech Recognition** to transcribe the audio.
   - Format the transcriptions into an **SRT subtitle file**.
4. **Embed Subtitles**:
   - Load the **MP4 video** and **MP3 audio**.
   - Add subtitle text at appropriate timestamps.
   - Combine the video, audio, and subtitles into a final MP4 file.
5. **Download**: Users can download the final video with **embedded subtitles**.

---

## Troubleshooting

### 1. **FFmpeg Not Found**
- Ensure FFmpeg is installed and added to the system **PATH**.
- Test by running:
  ```bash
  ffmpeg -version
  ```

### 2. **Speech Recognition Issues**
- Make sure the MP3 file has **clear speech** for better accuracy.
- Google Speech API may have **limitations on long audio**.

### 3. **ImageMagick Errors**
- Ensure `magick.exe` is properly installed and referenced in `app.py`.

### 4. **MoviePy Issues**
- If subtitles do not appear, check **font availability** in ImageMagick.

---

## Contributing
Feel free to **fork** this repository and submit pull requests for improvements!

---

## License
This project is open-source under the **MIT License**.
