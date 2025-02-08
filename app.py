from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import os
import speech_recognition as sr
from pydub import AudioSegment
from pydub.effects import normalize
from pysrt import SubRipFile, SubRipItem, SubRipTime
import tempfile

from moviepy.config import change_settings

# Specify the path to the ImageMagick binary
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'mp3'}
app.secret_key = 'supersecretkey'

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        # Check if both files are present
        if 'video' not in request.files or 'audio' not in request.files:
            flash('Both video and audio files are required.')
            return redirect(request.url)
        
        video_file = request.files['video']
        audio_file = request.files['audio']
        
        # Check if files have valid extensions
        if video_file.filename == '' or audio_file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if not allowed_file(video_file.filename) or not allowed_file(audio_file.filename):
            flash('Invalid file type. Only MP4 and MP3 files are allowed.')
            return redirect(request.url)
        
        # Save the uploaded files
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_file.filename)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
        video_file.save(video_path)
        audio_file.save(audio_path)
        
        # Debugging: Print paths to verify files are saved correctly
        print(f"Video saved at: {video_path}")
        print(f"Audio saved at: {audio_path}")
        
        # Process the files
        output_filename = 'output_video_with_subtitles.mp4'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        print(f"Output path: {output_path}")
        
        try:
            subtitles_path = generate_subtitles(audio_path)
            print(f"Subtitles generated at: {subtitles_path}")
            combine_audio_video_with_subtitles(video_path, audio_path, subtitles_path, output_path)
            flash('Video processed successfully with subtitles!')
            return redirect(url_for('download_file', filename=output_filename))
        except Exception as e:
            flash(f'An error occurred: {str(e)}')
            print(f"Error details: {str(e)}")
            return redirect(request.url)
    
    return render_template_string(index_html)

@app.route('/download/<filename>')
def download_file(filename):
    return render_template_string(download_html, filename=filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def generate_subtitles(audio_path):
    recognizer = sr.Recognizer()
    audio_segment = AudioSegment.from_mp3(audio_path)

    # Use a temporary directory for intermediate files
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_wav_path = temp_wav.name
        print(f"Temporary WAV file created at: {temp_wav_path}")

        # Export MP3 to WAV
        try:
            audio_segment.export(temp_wav_path, format="wav")
            print(f"WAV file exported successfully to: {temp_wav_path}")
        except Exception as e:
            print(f"Error exporting WAV file: {e}")
            raise

        # Verify the temporary WAV file exists
        if not os.path.exists(temp_wav_path):
            raise FileNotFoundError(f"Temporary WAV file not found at: {temp_wav_path}")

        # Perform speech recognition
        with sr.AudioFile(temp_wav_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                print("Transcription:", text)
            except sr.UnknownValueError:
                raise Exception("Google Speech Recognition could not understand the audio")
            except sr.RequestError as e:
                raise Exception(f"Could not request results from Google Speech Recognition service; {e}")

        # Clean up the temporary WAV file
        try:
            os.unlink(temp_wav_path)
            print(f"Temporary WAV file deleted: {temp_wav_path}")
        except Exception as e:
            print(f"Error deleting temporary WAV file: {e}")

        # Generate subtitles
        subtitles_path = os.path.join(app.config['UPLOAD_FOLDER'], 'subtitles.srt')
        srt_file = SubRipFile()

        # Split the transcription into smaller chunks
        def split_into_chunks(text, max_words=8):
            words = text.split()
            chunks = []
            current_chunk = []

            for word in words:
                current_chunk.append(word)
                if len(current_chunk) >= max_words or any(punct in word for punct in '.!?'):
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []

            if current_chunk:
                chunks.append(' '.join(current_chunk))

            return chunks

        chunks = split_into_chunks(text)
        total_duration = len(audio_segment) / 1000  # Total audio duration in seconds
        duration_per_chunk = total_duration / len(chunks)

        for i, chunk in enumerate(chunks):
            start_time = i * duration_per_chunk
            end_time = (i + 1) * duration_per_chunk

            # Convert float seconds to hours, minutes, seconds, milliseconds
            def seconds_to_time_components(seconds):
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                seconds_remainder = int(seconds % 60)
                milliseconds = int((seconds % 1) * 1000)
                return hours, minutes, seconds_remainder, milliseconds

            # Create SubRipTime objects with integer components
            start_components = seconds_to_time_components(start_time)
            end_components = seconds_to_time_components(end_time)

            subtitle_item = SubRipItem(
                index=i + 1,
                start=SubRipTime(
                    hours=start_components[0],
                    minutes=start_components[1],
                    seconds=start_components[2],
                    milliseconds=start_components[3]
                ),
                end=SubRipTime(
                    hours=end_components[0],
                    minutes=end_components[1],
                    seconds=end_components[2],
                    milliseconds=end_components[3]
                ),
                text=chunk.strip()
            )
            srt_file.append(subtitle_item)

        srt_file.save(subtitles_path, encoding='utf-8')
        return subtitles_path

def parse_time(time_str):
    """Convert time string (e.g., '1m 23.456s') into hours, minutes, seconds, milliseconds."""
    minutes, seconds = time_str.split('m ')
    seconds, milliseconds = seconds.split('.')
    hours = int(minutes) // 60
    minutes = int(minutes) % 60
    seconds = int(seconds)
    milliseconds = int(milliseconds)
    return hours, minutes, seconds, milliseconds

def combine_audio_video_with_subtitles(video_path, audio_path, subtitles_path, output_path):
    try:
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)
        subtitle_clips = []  # Initialize subtitle_clips list before use
        
        # Debugging: Print durations of video and audio
        print(f"Video duration: {video_clip.duration}, Audio duration: {audio_clip.duration}")
        
        # If the video is longer than the audio, trim the video to match the audio duration
        if video_clip.duration > audio_clip.duration:
            video_clip = video_clip.subclip(0, audio_clip.duration)
        
        # Load subtitles
        subtitles = SubRipFile.open(subtitles_path)
        
        # Create subtitle clips
        for subtitle in subtitles:
            start_time = subtitle.start.ordinal / 1000  # Convert milliseconds to seconds
            end_time = subtitle.end.ordinal / 1000
            duration = end_time - start_time
            
            # Create TextClip with proper method
            txt_clip = TextClip(
                txt=subtitle.text,
                fontsize=12,
                color='yellow',
                font="Arial-Bold",
                size=(int(video_clip.w * 0.8), None),
                method="caption"
            ).set_position(('center', 'bottom')).set_duration(duration).set_start(start_time)
            subtitle_clips.append(txt_clip)
        
        # Combine video, audio, and subtitles
        final_clip = CompositeVideoClip([video_clip] + subtitle_clips)
        final_clip = final_clip.set_audio(audio_clip)
        
        # Write the result to the output file
        final_clip.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=video_clip.fps
        )
    except Exception as e:
        print(f"Error in video processing: {str(e)}")
        raise
    finally:
        # Ensure all clips are properly closed
        try:
            if 'video_clip' in locals(): video_clip.close()
            if 'audio_clip' in locals(): audio_clip.close()
            if 'final_clip' in locals(): final_clip.close()
            for clip in subtitle_clips:
                clip.close()
        except Exception as e:
            print(f"Error while closing clips: {str(e)}")

# HTML Templates embedded as multi-line strings
index_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Upload Audio and Video</title>
</head>
<body>
    <h1>Upload Audio and Video Files</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
        {% for message in messages %}
          <li>{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form action="/" method="post" enctype="multipart/form-data">
        Select Video File (MP4): <input type="file" name="video"><br><br>
        Select Audio File (MP3): <input type="file" name="audio"><br><br>
        <input type="submit" value="Upload and Combine">
    </form>
</body>
</html>
'''

download_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Download Combined Video</title>
</head>
<body>
    <h1>Your Video is Ready!</h1>
    <p>Click the link below to download the combined video:</p>
    <a href="{{ url_for('uploaded_file', filename=filename) }}">Download Combined Video</a>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)