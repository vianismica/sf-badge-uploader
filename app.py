from flask import Flask, request, render_template, redirect, url_for, flash
import pandas as pd
import requests
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_badges():
    file = request.files.get('file')
    if not file:
        flash("No file uploaded.", "error")
        return redirect(url_for('index'))

    try:
        df = pd.read_csv(file)

        # Check required columns
        required_columns = {'userId', 'badgeId', 'badgeInstanceId', 'comment'}
        if not required_columns.issubset(df.columns):
            flash("CSV must contain userId, badgeId, badgeInstanceId, and comment columns.", "error")
            return redirect(url_for('index'))

        total_uploaded = 0
        for _, row in df.iterrows():
            payload = {
                "userId": row['userId'],
                "badgeId": str(row['badgeId']),
                "badgeInstanceId": str(row['badgeInstanceId']),
                "comment": row['comment']
            }

            response = requests.post(
                os.environ['SF_BASE_URL'] + os.environ['SF_API_PATH'],
                json=payload,
                auth=(os.environ['SF_USERNAME'], os.environ['SF_PASSWORD'])
            )

            print(f"Payload: {payload}")
            print(f"Status Code: {response.status_code}")
            print(f"Response Text: {response.text}")

            if response.status_code == 201:
                total_uploaded += 1

        flash(f"Success! {total_uploaded} badges uploaded.", "success")
        return redirect(url_for('index'))

    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

