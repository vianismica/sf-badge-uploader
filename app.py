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

    deleted_badges = []

    if response.status_code == 200:
        badges = response.json().get('d', {}).get('results', [])
        for badge in badges:
            badge_id = badge.get('badgeInstanceId')
            delete_url = f"{os.environ['SF_BASE_URL']}/odata/v2/UserBadges(badgeInstanceId={badge_id},userId='{user_id}')?$format=json"
            delete_response = requests.delete(
                delete_url,
                auth=(os.environ['SF_USERNAME'], os.environ['SF_PASSWORD'])
            )

            print(f"DELETE URL: {delete_url} — Status: {delete_response.status_code}")

            if delete_response.status_code in [200, 204]:
                deleted_badges.append({
                    "userId": user_id,
                    "badgeInstanceId": badge_id,
                    "badgeId": badge.get('badgeId'),
                    "comment": badge.get('comment')
                })

        if deleted_badges:
            flash(f"Deleted {len(deleted_badges)} badges for user {user_id}.", "success")
        else:
            flash("No badges were deleted.", "error")
    else:
        flash("Failed to retrieve user badges from SuccessFactors.", "error")

    return render_template('index.html', deleted_badges=deleted_badges)

if __name__ == '__main__':
    app.run(debug=True)

