from flask import Flask, request, render_template_string, redirect, url_for, session, send_file
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Secret key for session management
app.secret_key = os.urandom(24)

# Path to the license text file
LICENSE_FILE = "licenses.txt"

# The owner's license key for accessing the admin panel
OWNER_LICENSE_KEY = "owner-12345"
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Global variable to store uploaded log file
log_file = None

# Function to process the log file and filter based on the target
# Function to process the log file and filter based on the target
def process_file(log_file_path, target, output_filename):

    target_keywords = {
        'twitter': 'Twitter',
        'facebook': 'Facebook',
        'instagram': 'Instagram',
        'discord': 'Discord',
        'spotify': 'Spotify',
        'netflix': 'Netflix',
        'paypal': 'PayPal'
    }

    target_keyword = None
    for key, value in target_keywords.items():
        if key in target.lower():  
            target_keyword = value
            break

    if not target_keyword:
        target_keyword = target.capitalize()

    output_file_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
    count = 0

    with open(log_file_path, 'r') as log_file:
        lines = log_file.readlines()
    
    with open(output_file_path, 'a') as output_file:
        for line in lines:
            if target_keyword.lower() in line.lower():
                split = line.split(":")
                if len(split) < 2:
                    continue
                email = split[-2]
                password = split[-1]
                output_file.write(email+':'+password)
                count += 1

    return output_filename, count
# Helper functions for license management
def read_licenses():
    licenses = []
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE, 'r') as f:
            for line in f:
                license_key, subscription_name, expiry_date = line.strip().split('|')
                expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d")
                licenses.append({
                    "license_key": license_key,
                    "subscription_name": subscription_name,
                    "expiry_date": expiry_date,
                })
    return licenses

def save_licenses(licenses):
    with open(LICENSE_FILE, 'w') as f:
        for license in licenses:
            f.write(f"{license['license_key']}|{license['subscription_name']}|{license['expiry_date'].strftime('%Y-%m-%d')}\n")

def add_license(license_key, subscription_name, expiry_date):
    licenses = read_licenses()
    licenses.append({
        "license_key": license_key,
        "subscription_name": subscription_name,
        "expiry_date": datetime.strptime(expiry_date, "%Y-%m-%d"),
    })
    save_licenses(licenses)

def remove_license(license_key):
    licenses = read_licenses()
    licenses = [license for license in licenses if license['license_key'] != license_key]
    save_licenses(licenses)

@app.route('/process', methods=['POST'])
def process():
    global log_file
    target = request.form['target']
    output = request.form['output']

    if log_file is None:
        return "Log file not uploaded yet.", 400

    output_filename, count = process_file(log_file, target, output)

    if output_filename:
        return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Download File</title>
            <style>
                body {
                    font-family: 'Arial', sans-serif;
                    background: linear-gradient(45deg, #6a11cb, #2575fc);
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    color: #fff;
                }
                .output-info {
                    background-color: rgba(255, 255, 255, 0.9);
                    padding: 40px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
                    border-radius: 15px;
                    width: 450px;
                    text-align: center;
                    margin-top: 20px;
                    animation: fadeIn 1s ease-out;
                }
                h2 {
                    font-size: 32px;
                    color: #2575fc;
                    text-shadow: 2px 2px 10px rgba(0, 0, 0, 0.2);
                }
                p {
                    font-size: 18px;
                    color: #333;
                    margin: 15px 0;
                    font-weight: bold;
                }
                .download-btn {
                    background-color: #2575fc;
                    color: white;
                    padding: 12px 24px;
                    border-radius: 5px;
                    font-size: 18px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    margin-top: 20px;
                }
                .download-btn:hover {
                    background-color: #6a11cb;
                    transform: translateY(-3px);
                }
                @keyframes fadeIn {
                    0% { opacity: 0; }
                    100% { opacity: 1; }
                }
            </style>
        </head>
        <body>
            <div class="output-info">
                <h2>File Processing Completed!</h2>
                <p>Total Lines Processed: <span style="color: #2575fc;">{{ count }}</span></p>
                <p>Output File: <span style="color: #2575fc;">{{ output_filename }}</span></p>
                <form action="{{ url_for('download_file', filename=output_filename) }}" method="GET">
                    <button class="download-btn" type="submit">Download File</button>
                </form>
            </div>
        </body>
        </html>
        ''', count=count, output_filename=output_filename)
    else:
        return "Error during file processing", 500
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "File not found", 404
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    global log_file
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'logfile.txt')
            file.save(filepath)
            log_file = filepath
            return '''
                <html>
                    <head>
                        <style>
                            body {
                                font-family: 'Arial', sans-serif;
                                background-color: #f4f4f9;
                                margin: 0;
                                padding: 0;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                height: 100vh;
                            }
                            .container {
                                text-align: center;
                                background-color: #ffffff;
                                border-radius: 10px;
                                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                                padding: 30px;
                                width: 50%;
                            }
                            h1 {
                                font-size: 36px;
                                color: #333;
                            }
                            .message {
                                font-size: 20px;
                                color: #4CAF50;
                                font-weight: bold;
                                margin: 20px 0;
                                animation: fadeIn 2s ease-in-out;
                            }
                            .back-link {
                                font-size: 18px;
                                color: #007BFF;
                                text-decoration: none;
                            }
                            .back-link:hover {
                                text-decoration: underline;
                            }
                            @keyframes fadeIn {
                                0% { opacity: 0; }
                                100% { opacity: 1; }
                            }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>File Uploaded Successfully!</h1>
                            <div class="message">Your log file has been uploaded successfully.</div>
                            <a href="/" class="back-link">Go back to process</a>
                        </div>
                    </body>
                </html>
            '''
    return '''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Upload Log File</title>
            <style>
                body {
                    font-family: 'Arial', sans-serif;
                    background-color: #f4f4f9;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                }
                .form-container {
                    background-color: #ffffff;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    padding: 40px;
                    width: 40%;
                    text-align: center;
                }
                h1 {
                    font-size: 32px;
                    color: #333;
                    margin-bottom: 20px;
                }
                input[type="file"] {
                    border: 1px solid #ccc;
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    font-size: 16px;
                }
                button {
                    background-color: #4CAF50;
                    color: white;
                    font-size: 18px;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    transition: background-color 0.3s ease;
                }
                button:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <div class="form-container">
                <h1>Upload Your Log File</h1>
                <form method="POST" enctype="multipart/form-data">
                    <input type="file" name="file" required>
                    <br>
                    <button type="submit">Upload</button>
                </form>
            </div>
        </body>
        </html>
    '''
@app.route('/remove/ulp', methods=['GET'])
def remove_file():
    global log_file
    if log_file and os.path.exists(log_file):
        os.remove(log_file)
        log_file = None
        return '''
            <html>
                <head>
                    <style>
                        body {
                            font-family: 'Arial', sans-serif;
                            background-color: #f9f9f9;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                        }
                        .container {
                            text-align: center;
                            background-color: #ffffff;
                            border-radius: 10px;
                            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                            padding: 40px;
                            width: 40%;
                            max-width: 600px;
                        }
                        h1 {
                            font-size: 36px;
                            color: #333;
                        }
                        .message {
                            font-size: 24px;
                            color: #D32F2F;
                            font-weight: bold;
                            margin: 20px 0;
                            animation: fadeIn 2s ease-in-out;
                        }
                        a {
                            font-size: 18px;
                            color: #007BFF;
                            text-decoration: none;
                            transition: color 0.3s ease;
                        }
                        a:hover {
                            color: #0056b3;
                        }
                        @keyframes fadeIn {
                            0% { opacity: 0; }
                            100% { opacity: 1; }
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>File Removed Successfully!</h1>
                        <div class="message">The log file has been deleted successfully.</div>
                        <a href="/">Go back to home</a>
                    </div>
                </body>
            </html>
        '''
    return '''
        <html>
            <head>
                <style>
                    body {
                        font-family: 'Arial', sans-serif;
                        background-color: #f9f9f9;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .container {
                        text-align: center;
                        background-color: #ffffff;
                        border-radius: 10px;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        padding: 40px;
                        width: 40%;
                        max-width: 600px;
                    }
                    h1 {
                        font-size: 36px;
                        color: #333;
                    }
                    .message {
                        font-size: 24px;
                        color: #D32F2F;
                        font-weight: bold;
                        margin: 20px 0;
                        animation: fadeIn 2s ease-in-out;
                    }
                    a {
                        font-size: 18px;
                        color: #007BFF;
                        text-decoration: none;
                        transition: color 0.3s ease;
                    }
                    a:hover {
                        color: #0056b3;
                    }
                    @keyframes fadeIn {
                        0% { opacity: 0; }
                        100% { opacity: 1; }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Error</h1>
                    <div class="message">No log file found to remove.</div>
                    <a href="/">Go back to home</a>
                </div>
            </body>
        </html>
    '''
@app.route("/", methods=["GET", "POST"])
def index():
    error_message = None
    success_message = None
    
    if 'license_valid' in session and session['license_valid']:
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        license_key = request.form.get("license_key")

        # Check if license is valid
        licenses = read_licenses()
        valid_license = next((license for license in licenses if license['license_key'] == license_key), None)
        
        if valid_license and valid_license['expiry_date'] >= datetime.now():
            session['license_valid'] = True
            session['license_key'] = license_key
            success_message = "License validated successfully!"
            return redirect(url_for('dashboard'))
        else:
            error_message = "Invalid or expired license key. Please try again."

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>License Management</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f7f7f7;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                background-color: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                width: 300px;
            }
            h1 {
                font-size: 24px;
                margin-bottom: 10px;
                text-align: center;
            }
            p {
                font-size: 16px;
                text-align: center;
                color: #555;
            }
            .input-group {
                margin-bottom: 15px;
                display: flex;
                flex-direction: column;
            }
            .input-group input {
                padding: 10px;
                font-size: 16px;
                border: 1px solid #ccc;
                border-radius: 4px;
                outline: none;
                transition: border 0.3s ease;
            }
            .input-group input:focus {
                border: 1px solid #007bff;
            }
            .button {
                background-color: #007bff;
                color: white;
                padding: 10px;
                font-size: 16px;
                border: none;
                border-radius: 4px;
                width: 100%;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }
            .button:hover {
                background-color: #0056b3;
            }
            .error-message {
                color: red;
                font-size: 14px;
                text-align: center;
            }
            .success-message {
                color: green;
                font-size: 14px;
                text-align: center;
            }
        </style>
    </head>
    <body>

    <div class="container">
        <h1>License Management</h1>
        <p>Please enter your license key to continue:</p>
        
        <form method="POST">
            <div class="input-group">
                <input type="text" name="license_key" placeholder="Enter your license key" required>
            </div>
            <button type="submit" class="button">Submit</button>
            
            {% if error_message %}
                <p class="error-message">{{ error_message }}</p>
            {% endif %}
            
            {% if success_message %}
                <p class="success-message">{{ success_message }}</p>
            {% endif %}
        </form>
    </div>

    </body>
    </html>
    """
    
    return render_template_string(html_content, error_message=error_message, success_message=success_message)
    
    
    
    

@app.route('/dashboard')
def dashboard():
    if 'license_valid' not in session or not session['license_valid']:
        return redirect(url_for('index'))
    if log_file is None:
        return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Log Sorter</title>
            <style>
                body {
                    font-family: 'Arial', sans-serif;
                    background: linear-gradient(45deg, #6a11cb, #2575fc);
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    color: #fff;
                }
                .container {
                    background-color: rgba(0, 0, 0, 0.7);
                    padding: 40px;
                    border-radius: 15px;
                    width: 400px;
                    text-align: center;
                    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
                    transition: transform 0.3s ease;
                }
                .container:hover {
                    transform: scale(1.05);
                }
                h1 {
                    font-size: 38px;
                    color: #f0f0f0;
                    margin-bottom: 20px;
                    text-shadow: 3px 3px 10px rgba(0, 0, 0, 0.4);
                }
                .error-message {
                    font-size: 20px;
                    color: #ff4f4f;
                    margin-top: 30px;
                    font-weight: bold;
                }
                .contact-link {
                    color: #2575fc;
                    font-size: 18px;
                    text-decoration: none;
                    font-weight: bold;
                }
                .contact-link:hover {
                    text-decoration: underline;
                }
                .footer {
                    margin-top: 20px;
                }
                .footer p {
                    font-size: 14px;
                    color: #ddd;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Log Sorter</h1>
                <div class="error-message">
                    Log file not uploaded.<br>
                    Please contact the owner to upload the data.<br>
                    <a href="https://t.me/EssaPythonista" class="contact-link">Contact Owner</a>
                </div>
            </div>
        </body>
        </html>
        ''')

    html_content = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Log Sorter</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background: linear-gradient(45deg, #6a11cb, #2575fc);
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                color: #fff;
            }
            .container {
                background-color: rgba(0, 0, 0, 0.7);
                padding: 40px;
                border-radius: 15px;
                width: 400px;
                text-align: center;
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
                transition: transform 0.3s ease;
            }
            .container:hover {
                transform: scale(1.05);
            }
            h1 {
                font-size: 38px;
                color: #f0f0f0;
                margin-bottom: 20px;
                text-shadow: 3px 3px 10px rgba(0, 0, 0, 0.4);
            }
            label {
                font-size: 16px;
                color: #ddd;
                margin: 10px 0;
                display: block;
            }
            input, select {
                width: 100%;
                padding: 15px;
                margin: 12px 0;
                border-radius: 8px;
                border: 2px solid #fff;
                font-size: 16px;
                background-color: rgba(255, 255, 255, 0.1);
                color: #fff;
                transition: all 0.3s ease;
            }
            input:focus, select:focus {
                border-color: #2575fc;
                outline: none;
                background-color: rgba(255, 255, 255, 0.2);
                box-shadow: 0 0 10px rgba(37, 117, 252, 0.8);
            }
            button {
                background-color: #2575fc;
                color: white;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 18px;
                border: none;
                cursor: pointer;
                transition: all 0.3s ease;
                width: 100%;
                margin-top: 15px;
            }
            button:hover {
                background-color: #6a11cb;
                transform: translateY(-3px);
            }
            .footer {
                margin-top: 30px;
                font-size: 14px;
                color: #ddd;
            }
            .footer p {
                margin: 5px;
            }
            .upload-message {
                font-size: 18px;
                color: green;
                font-weight: bold;
                margin-top: 20px;
                transition: opacity 1s ease-in-out;
            }
            .remove-message {
                font-size: 18px;
                color: red;
                font-weight: bold;
                margin-top: 20px;
                transition: opacity 1s ease-in-out;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Log Sorter</h1>
            <form action="{{ url_for('process') }}" method="POST">
                <label for="target">Enter a target (e.g., twitter, facebook, instagram):</label>
                <input type="text" name="target" id="target" placeholder="Enter target here" required><br><br>

                <label for="output">Output file name:</label>
                <input type="text" name="output" id="output" placeholder="e.g., results.txt" required><br><br>

                <button type="submit">Process</button>
            </form>
            <div class="footer">
                <p>Version 1.2 | Created by Romeo</p>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_content)


def load_licenses():
    licenses = []
    try:
        with open(LICENSE_FILE, "r") as file:
            for line in file:
                parts = line.strip().split('|')  # Use '|' as delimiter
                if len(parts) == 3:
                    key, status, expiry_date_str = parts
                    expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
                    licenses.append({"key": key, "status": status, "expiry_date": expiry_date})
    except FileNotFoundError:
        pass  # File not found, return an empty list
    return licenses

def save_licenses(licenses):
    with open(LICENSE_FILE, "w") as file:
        for license in licenses:
            file.write(f"{license['key']}|{license['status']}|{license['expiry_date'].strftime('%Y-%m-%d')}\n")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>License Management</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f5f5f5;
            padding: 20px;
            margin: 0;
            color: #333;
            background: linear-gradient(135deg, #d4e157, #ffeb3b, #8e24aa);
            animation: backgroundEffect 10s infinite alternate;
        }
        @keyframes backgroundEffect {
            0% { background: linear-gradient(135deg, #d4e157, #ffeb3b, #8e24aa); }
            50% { background: linear-gradient(135deg, #4caf50, #03a9f4, #9c27b0); }
            100% { background: linear-gradient(135deg, #d4e157, #ffeb3b, #8e24aa); }
        }
        h1 {
            text-align: center;
            color: #fff;
            font-size: 28px;
            margin-bottom: 30px;
        }
        table {
            width: 60%;  /* Make the table narrower */
            margin: 0 auto;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            padding: 6px 10px;  /* Smaller padding for compactness */
            text-align: center;
        }
        th {
            background-color: #4CAF50;
            color: white;
        }
        td {
            background-color: #fff;
        }
        button {
            padding: 8px 16px;
            background-color: #007BFF;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 8px;
            border-radius: 4px;
            transition: background-color 0.3s;
            display: block;
            width: 160px;  /* Limit button width */
            margin-left: auto;
            margin-right: auto;
        }
        button:hover {
            background-color: #0056b3;
        }
        .action-button-blue {
            background-color: #1e90ff;
        }
        .action-button-yellow {
            background-color: #ffeb3b;
            color: #000;
        }
        .action-button-cyan {
            background-color: #00bcd4;
        }
        .action-button-green {
            background-color: #4caf50;
        }
        .action-button-purple {
            background-color: #9c27b0;
        }
        .action-button:hover {
            opacity: 0.9;
        }
        form {
            display: inline;
        }
        .form-container {
            margin: 20px auto;
            width: 60%;
            padding: 20px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        .form-container h2 {
            margin-top: 0;
            text-align: center;
            color: #333;
        }
        input[type="text"], input[type="date"], input[type="number"] {
            width: calc(100% - 20px);
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
            font-size: 14px;
        }
        .action-form {
            margin-top: 30px;
        }
        .centered-button {
            text-align: center;
            margin-top: 20px;
        }
        .centered-button button {
            width: 150px;
            font-size: 16px;
        }
        .increase-decrease-days {
            margin-top: 10px;
            text-align: center;
        }
        .increase-decrease-days input {
            width: 70px;
            padding: 6px;
            margin-right: 10px;
            font-size: 14px;
        }
        .increase-decrease-days button {
            padding: 6px 10px;
            font-size: 14px;
        }
    </style>
</head>
<body>

    <h1>License Management</h1>
    
    <div class="centered-button">
        <a href="{{ url_for('create_license') }}">
            <button>Create New License</button>
        </a>
    </div>

    <h2>Active Licenses</h2>
    <table>
        <tr>
            <th>License Key</th>
            <th>Status</th>
            <th>Expiry Date</th>
            <th>Actions</th>
        </tr>
        {% for license in licenses %}
        <tr>
            <td>{{ license.key }}</td>
            <td>{{ license.status }}</td>
            <td>{{ license.expiry_date.strftime('%Y-%m-%d') }}</td>
            <td>
                <form method="POST" action="{{ url_for('licenses_view') }}">
                    <input type="hidden" name="license_key" value="{{ license.key }}">
                    <button type="submit" name="action" value="remove" class="action-button-red">Remove</button>
                </form>
                <div class="increase-decrease-days">
                    <button class="action-button-blue" onclick="showDaysInput('{{ license.key }}', 'increase')">Increase Expiry</button>
                </div>
                <div class="increase-decrease-days">
                    <button class="action-button-yellow" onclick="showDaysInput('{{ license.key }}', 'decrease')">Decrease Expiry</button>
                </div>
                <div id="days-input-{{ license.key }}" class="increase-decrease-days" style="display:none;">
                    <input type="number" id="days-{{ license.key }}" placeholder="Days" min="1" required>
                    <button onclick="adjustExpiry('{{ license.key }}')">Apply</button>
                </div>
            </td>
        </tr>
        {% endfor %}
    </table>

</body>

<script>
    // Function to show the input box for days
    function showDaysInput(licenseKey, action) {
        const inputDiv = document.getElementById('days-input-' + licenseKey);
        inputDiv.style.display = 'block';
        inputDiv.setAttribute('data-action', action);
    }

    // Function to apply the increase or decrease
    function adjustExpiry(licenseKey) {
        const daysInput = document.getElementById('days-' + licenseKey);
        const days = daysInput.value;
        const action = document.getElementById('days-input-' + licenseKey).getAttribute('data-action');
        
        if (days && !isNaN(days)) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '{{ url_for("licenses_view") }}';
            const inputAction = document.createElement('input');
            inputAction.type = 'hidden';
            inputAction.name = 'action';
            inputAction.value = action + '_expiry';
            form.appendChild(inputAction);

            const inputKey = document.createElement('input');
            inputKey.type = 'hidden';
            inputKey.name = 'license_key';
            inputKey.value = licenseKey;
            form.appendChild(inputKey);

            const inputDays = document.createElement('input');
            inputDays.type = 'hidden';
            inputDays.name = 'custom_days';
            inputDays.value = days;
            form.appendChild(inputDays);

            document.body.appendChild(form);
            form.submit();
        }
    }
</script>

</html>
"""

@app.route("/licenses", methods=["GET", "POST"])
def licenses_view():
    # Load licenses from file
    licenses = load_licenses()

    if request.method == "POST":
        action = request.form.get("action")
        license_key = request.form.get("license_key")
        custom_days = request.form.get("custom_days", type=int)

        # Process actions based on the action received from the form
        if action == "remove":
            licenses = [license for license in licenses if license["key"] != license_key]
        elif action == "increase_expiry" or action == "decrease_expiry":
            for license in licenses:
                if license["key"] == license_key:
                    if action == "increase_expiry":
                        license["expiry_date"] += timedelta(days=custom_days)
                    elif action == "decrease_expiry":
                        license["expiry_date"] -= timedelta(days=custom_days)

        # Save the updated licenses back to the file
        save_licenses(licenses)

    return render_template_string(HTML_TEMPLATE, licenses=licenses)

# Route to create a new license
@app.route("/create-license", methods=["GET", "POST"])
def create_license():
    if request.method == "POST":
        # Getting the form data
        key = request.form.get("key")
        status = request.form.get("status")
        expiry_date = request.form.get("expiry_date")
        expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d")
        
        # Load existing licenses from the file
        licenses = load_licenses()
        
        # Add the new license to the list
        licenses.append({"key": key, "status": status, "expiry_date": expiry_date})
        
        # Save updated licenses to the file
        save_licenses(licenses)
        
        return redirect(url_for('licenses_view'))
    
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Create New License</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background-color: #f5f5f5;
                padding: 20px;
                margin: 0;
                color: #333;
                background: linear-gradient(135deg, #d4e157, #ffeb3b, #8e24aa);
                animation: backgroundEffect 10s infinite alternate;
            }
            @keyframes backgroundEffect {
                0% { background: linear-gradient(135deg, #d4e157, #ffeb3b, #8e24aa); }
                50% { background: linear-gradient(135deg, #4caf50, #03a9f4, #9c27b0); }
                100% { background: linear-gradient(135deg, #d4e157, #ffeb3b, #8e24aa); }
            }

            h1 {
                text-align: center;
                color: #fff;
                font-size: 32px;
                margin-bottom: 30px;
            }

            .form-container {
                width: 100%;
                max-width: 600px;
                margin: 0 auto;
                padding: 30px;
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                text-align: center;
            }

            .input-group {
                margin: 10px 0;
                text-align: center;
            }

            input[type="text"], input[type="date"] {
                width: 100%;
                padding: 12px;
                font-size: 16px;
                border-radius: 8px;
                border: 1px solid #ddd;
                box-sizing: border-box;
                transition: all 0.3s ease-in-out;
            }

            input[type="text"]:focus, input[type="date"]:focus {
                border: 1px solid #4caf50;
                outline: none;
            }

            .centered-button {
                margin-top: 20px;
                text-align: center;
            }

            .action-button-green {
                background-color: #4caf50;
                color: white;
                padding: 12px 20px;
                font-size: 18px;
                border: none;
                cursor: pointer;
                border-radius: 8px;
                transition: background-color 0.3s;
            }

            .action-button-green:hover {
                background-color: #45a049;
            }

            .input-group input {
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>

        <h1>Create New License</h1>
        <div class="form-container">
            <form method="POST">
                <div class="input-group">
                    <input type="text" name="key" placeholder="License Key" required>
                </div>
                <div class="input-group">
                    <input type="text" name="status" placeholder="Status (active/expired)" required>
                </div>
                <div class="input-group">
                    <input type="date" name="expiry_date" required>
                </div>
                <div class="centered-button">
                    <button type="submit" class="action-button-green">Create License</button>
                </div>
            </form>
        </div>

    </body>
    </html>
    """
if __name__ == "__main__":
    app.run(debug=False)