from flask import Flask, request, render_template, redirect, url_for, flash
import pandas as pd
import requests
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# In-memory tracking
uploaded_badges = []
deleted_badges = []

@app.route('/')
def index():
    return render_template('index.html', badges=uploaded_badges, deleted=deleted_badges)

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
        global uploaded_badges
        for _, row in df.iterrows():
            payload = {
                "userId": row['userId'],
                "badgeId": int(row['badgeId']),
                "badgeInstanceId": int(row['badgeInstanceId']),
                "comment": row['comment']
            }
            response = requests.post(
                os.environ['SF_BASE_URL'] + os.environ['SF_API_PATH'],
                json=payload,
                auth=(os.environ['SF_USERNAME'], os.environ['SF_PASSWORD'])
            )
            if response.status_code == 201:
                total_uploaded += 1
                uploaded_badges.append(payload)

        flash(f"Success! {total_uploaded} badges uploaded.", "success")
        return redirect(url_for('index'))

    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/delete-user-badges', methods=['POST'])
def delete_user_badges():
    user_id = request.form.get('userId')
    if not user_id:
        flash("User ID is required to delete badges.", "error")
        return redirect(url_for('index'))

    try:
        list_url = f"{os.environ['SF_BASE_URL']}/odata/v2/UserBadges?$filter=userId eq '{user_id}'&$format=json"
        response = requests.get(list_url, auth=(os.environ['SF_USERNAME'], os.environ['SF_PASSWORD']))
        if response.status_code != 200:
            flash(f"Failed to fetch badges: {response.text}", "error")
            return redirect(url_for('index'))

        badges = response.json().get('d', {}).get('results', [])
        global deleted_badges
        deleted_count = 0

        for badge in badges:
            badge_id = badge.get('badgeId')
            badge_instance_id = badge.get('badgeInstanceId')

            delete_url = f"{os.environ['SF_BASE_URL']}/odata/v2/UserBadges(badgeInstanceId={badge_instance_id},userId='{user_id}')?$format=json"
            del_response = requests.delete(delete_url, auth=(os.environ['SF_USERNAME'], os.environ['SF_PASSWORD']))
            if del_response.status_code in [200, 204]:
                deleted_count += 1
                deleted_badges.append({
                    "userId": user_id,
                    "badgeId": badge_id,
                    "badgeInstanceId": badge_instance_id
                })

        flash(f"Success! {deleted_count} badges deleted for user {user_id}.", "success")
        return redirect(url_for('index'))

    except Exception as e:
        flash(f"Error deleting badges: {str(e)}", "error")
        return redirect(url_for('index'))

