from flask import Flask, request, render_template
import pandas as pd
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            return "No file uploaded", 400
        df = pd.read_csv(file)
        results = []
        for _, row in df.iterrows():
            response = requests.post(
                url=os.getenv("SF_BASE_URL") + os.getenv("SF_API_PATH"),
                auth=(os.getenv("SF_USERNAME"), os.getenv("SF_PASSWORD")),
                json={
                    "userId": row['userId'],
                    "badgeId": row['badgeId'],
                    "badgeInstanceId": row['badgeInstanceId'],
                    "comment": row.get('comment', '')
                }
            )
            results.append((row['userId'], row['badgeId'], response.status_code, response.text))
        return render_template("results.html", results=results)
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)
