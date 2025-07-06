from flask import Flask, request, jsonify
import joblib
import pandas as pd
import requests

app = Flask(__name__)

# Load trained model, encoder, and grouped data
model = joblib.load("model.pkl")
mlb = joblib.load("mlb.pkl")
grouped = pd.read_pickle("grouped_tasks.pkl")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    
    sample = [[
        data['pattern_score'],
        data['subtraction_score'],
        data['income_bracket']
    ]]
    
    # Predict based on input
    prediction = model.predict(sample)
    task_titles = mlb.inverse_transform(prediction)[0]

    # Get the row from grouped that matches input
    match = grouped[
        (grouped['pattern_score'] == data['pattern_score']) &
        (grouped['subtraction_score'] == data['subtraction_score']) &
        (grouped['income_bracket'] == data['income_bracket'])
    ]

    if match.empty:
        return jsonify({"error": "No tasks found for this input."}), 404

    titles = match.iloc[0]['task_title']
    details = match.iloc[0]['task_details']
    objectives = match.iloc[0]['task_objective']

    # Combine all 3 fields
    tasks = []
    for i in range(min(6, len(titles))):
        tasks.append({
            "task_title": titles[i],
            "task_details": details[i],
            "task_objective": objectives[i]
        })

    return jsonify(tasks)

@app.route('/gpt', methods=['POST'])
def gpt():
    data = request.get_json()
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({"error": "Prompt is required."}), 400

    # Insert your Bearer token here
    bearer_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0IjoiYXUiLCJ2IjoiMC4wLjAiLCJ1dSI6IjZZbCtMd25iUlplUFZ3d1NzZzZLY3c9PSIsImF1IjoiaWRnL2ZEMDdVTkdhSk5sNXpXUGZhUT09IiwicyI6IjRBT3JMcGpBeHY3U1EyU3dmMnZJY3c9PSIsImlhdCI6MTc1MTgyMDkzOH0.mxAT7cm6UNUtl8zgkD5P1FwWa28xNxmZzIyWRiDPpQQ"

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://docs.puter.com"
    }

    payload = {
        "interface": "puter-chat-completion",
        "driver": "openai-completion",
        "test_mode": False,
        "method": "complete",
        "args": {
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    }

    try:
        response = requests.post(
            "https://api.puter.com/drivers/call",
            headers=headers,
            json=payload
        )
        if response.status_code != 200:
            return jsonify({"error": "Puter API error", "details": response.text}), 500
        result = response.json()
        # Extract the assistant's reply
        message = result.get("result", {}).get("message", {}).get("content", "")
        return jsonify({"response": message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
