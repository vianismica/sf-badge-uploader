from flask import Flask, request, render_template, redirect, url_for, flash
import pandas as pd
import requests
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Store uploaded badges here (for demo, resets on restart)
uploaded_badges = []

@app.route('/')
def index():
    return render_template('index.html', badges=uploaded_badges)

@app.route('/upload', methods=['POST'])
def upload_badges():
    file = request.files.get('file')
    if not file:
        flash("No file uploaded.", "error")
        return redirect(url_for('index'))

    try:
        df = pd.read_csv(file)
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

            if response.status_code == 201:
                total_uploaded += 1
                # Save badge info locally
                uploaded_badges.append({
                    "userId": row['userId'],
                    "badgeId": row['badgeId'],
                    "badgeInstanceId": row['badgeInstanceId'],
                    "comment": row['comment']
                })

        flash(f"Success! {total_uploaded} badges uploaded.", "success")
        return redirect(url_for('index'))

    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

