import os
import requests
import logging
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for

load_dotenv()

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_TOKEN = "as62Tgmr5yOqwzGhDYHcTcfXaPYuU0PE" 

def transcribe_audio(file_path, token):
    url = 'https://asr.snr.audio/v1/rest/transcribe'
    headers = {
        'Authorization': f'Bearer {token}'
    }

    if not os.path.isfile(file_path):
        logging.error(f"File not found: {file_path}")
        return None

    with open(file_path, 'rb') as audio_file:
        files = {
            'file': audio_file
        }

        try:
            response = requests.post(url, headers=headers, files=files)
            response.raise_for_status()
            logging.info("Transcription successful.")
           
            logging.info(f"Raw response content: {response.text}")
            try:
                return response.json()
            except ValueError:
                logging.error("Response content is not valid JSON")
                return response.text 
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
        except Exception as err:
            logging.error(f"An error occurred: {err}")
        return None

def save_transcription_to_file(transcription, output_path):
    try:
        with open(output_path, 'w') as output_file:
            output_file.write(transcription)
        logging.info(f"Transcription saved to {output_path}")
    except Exception as err:
        logging.error(f"Failed to save transcription to file: {err}")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            logging.error('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            logging.error('No selected file')
            return redirect(request.url)
        if file:
            filename = file.filename
            file_path = os.path.join('uploads', filename)
            file.save(file_path)
            result = transcribe_audio(file_path, API_TOKEN)
            if result:
                logging.info(f"Result type: {type(result)}, content: {result}")
                if isinstance(result, dict):
                    transcription_text = result.get('transcription', '')
                    if transcription_text:
                        save_transcription_to_file(transcription_text, 'output.txt')
                    else:
                        logging.error("No transcription text found in the response.")
                elif isinstance(result, str):
                    save_transcription_to_file(result, 'output.txt')
                else:
                    logging.error("Unexpected response format.")
            else:
                logging.error("No result returned from the transcription service.")
            return redirect(url_for('result'))
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SNR Audio Transcription</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #e7f1ff;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                background-color: #fff;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            h1 {
                text-align: center;
                color: #333;
            }
            form {
                text-align: center;
            }
            input[type="file"] {
                margin-top: 20px;
                padding: 10px;
                border: 2px solid #80b3ff;
                border-radius: 5px;
                background-color: #fff;
                font-size: 16px;
            }
            button[type="submit"] {
                margin-top: 20px;
                padding: 10px 20px;
                background-color: #4CAF50;
                color: #fff;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SNR Audio Transcription</h1>
            <form method="POST" enctype="multipart/form-data">
                <input type="file" name="file" accept="audio/*" required>
                <br>
                <button type="submit">Upload</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.route('/result')
def result():
    with open('output.txt', 'r') as output_file:
        transcription = output_file.read()
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SNR Transcription Result</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #e7f1ff;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 50px auto;
                padding: 20px;
                background-color: #fff;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                text-align: center;
                color: #333;
            }}
            p {{
                margin-top: 20px;
                padding: 10px;
                background-color: #f9f9f9;
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Transcription Result</h1>
            <p>{transcription}</p>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True)
