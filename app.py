from flask import Flask, request, render_template, redirect, url_for, flash
import pandas as pd
import requests
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

# Keep track of uploaded badges in memory
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
        if 'userId' not in df.columns or 'badgeId' not in df.columns or 'badgeInstanceId' not in df.columns or 'comment' not in df.columns:
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
                # Add to in-memory list
                uploaded_badges.append({
                    "userId": row['userId'],
                    "badgeId": int(row['badgeId']),
                    "badgeInstanceId": int(row['badgeInstanceId']),
                    "comment": row['comment']
                })

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

    list_url = f"{os.environ['SF_BASE_URL']}/odata/v2/UserBadges?$filter=userId eq '{user_id}'&$format=json"
    response = requests.get(list_url, auth=(os.environ['SF_USERNAME'], os.environ['SF_PASSWORD']))

    if response.status_code == 200:
        badges = response.json().get('d', {}).get('results', [])
        errors = False
        global uploaded_badges

        for badge in badges:
            badgeInstanceId = badge['badgeInstanceId']
            delete_url = f"{os.environ['SF_BASE_URL']}/odata/v2/UserBadges(badgeInstanceId={badgeInstanceId},userId='{user_id}')?$format=json"
            del_response = requests.delete(delete_url, auth=(os.environ['SF_USERNAME'], os.environ['SF_PASSWORD']))
            if del_response.status_code not in (200, 204):
                errors = True
                flash(f"Failed to delete badge {badgeInstanceId} for user {user_id}: {del_response.text}", "error")

        if not errors:
            # Remove deleted badges from in-memory list
            uploaded_badges = [b for b in uploaded_badges if b['userId'] != user_id]
            flash(f"Deleted all badges for user {user_id}.", "success")

    else:
        flash(f"Failed to list badges for user {user_id}: {response.text}", "error")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

