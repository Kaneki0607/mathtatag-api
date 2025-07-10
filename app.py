from flask import Flask, request, jsonify
import joblib
import pandas as pd
import requests
import threading
import time
import subprocess
import logging

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Load trained model, encoder, and grouped data
model = joblib.load("model.pkl")
mlb = joblib.load("mlb.pkl")
grouped = pd.read_pickle("grouped_tasks.pkl")

DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1392709998294863974/F_i0zuooyo-E2y1RA173TZrDD_mcrYW9URDdk_g5MgYN1GxwDTS3wsQ9f_1i_R_kPytO"

class DiscordLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        send_discord_log(log_entry)

def send_discord_log(message):
    data = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        response.raise_for_status()
    except Exception as e:
        print("Failed to send Discord log:", e)

# Set up logging
logger = logging.getLogger("mathtatag-api")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
discord_handler = DiscordLogHandler()
discord_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(discord_handler)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    logger.info(f"/predict called with data: {data}")
    
    max_attempts = 10  # Avoid infinite loops
    attempt = 0
    unique_titles = set()
    tasks = []
    while attempt < max_attempts:
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
            logger.warning(f"No tasks found for input: {data}")
            return jsonify({"error": "No tasks found for this input."}), 404

        titles = match.iloc[0]['task_title']
        details = match.iloc[0]['task_details']
        objectives = match.iloc[0]['task_objective']

        # Combine all 3 fields, but only add unique task_titles
        tasks = []
        unique_titles = set()
        for i in range(len(titles)):
            if titles[i] not in unique_titles:
                tasks.append({
                    "task_title": titles[i],
                    "task_details": details[i],
                    "task_objective": objectives[i]
                })
                unique_titles.add(titles[i])
            if len(tasks) == 6:
                break
        if len(tasks) == min(6, len(titles)) and len(tasks) == len(set([t["task_title"] for t in tasks])):
            break  # All tasks are unique
        attempt += 1
    if len(tasks) == 0:
        logger.warning(f"No unique tasks found for input: {data}")
        return jsonify({"error": "No unique tasks found for this input."}), 404

    # Top up with more unique tasks from anywhere in the dataset if less than 6
    if len(tasks) < 6:
        for idx, row in grouped.iterrows():
            titles = row['task_title']
            details = row['task_details']
            objectives = row['task_objective']
            for i in range(len(titles)):
                if titles[i] not in unique_titles:
                    tasks.append({
                        "task_title": titles[i],
                        "task_details": details[i],
                        "task_objective": objectives[i]
                    })
                    unique_titles.add(titles[i])
                if len(tasks) == 6:
                    break
            if len(tasks) == 6:
                break

    logger.info(f"Returning {len(tasks)} tasks for input: {data}")
    return jsonify(tasks)

@app.route('/gpt', methods=['POST'])
def gpt():
    data = request.get_json()
    prompt = data.get('prompt', '')
    logger.info(f"/gpt called with prompt: {prompt}")
    if not prompt:
        logger.warning("Prompt is required for /gpt endpoint.")
        return jsonify({"error": "Prompt is required."}), 400

    # Gemini API key placeholder
    gemini_api_key = "AIzaSyDsUXZXUDTMRQI0axt_A9ulaSe_m-HQvZk"
    if not gemini_api_key or gemini_api_key == "YOUR_GEMINI_API_KEY_HERE":
        logger.error("Gemini API key not set.")
        return jsonify({"error": "Gemini API key not set."}), 500

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": gemini_api_key
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    max_retries = 5
    retry_delay = 1
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
                headers=headers,
                json=payload
            )
            if response.status_code == 503:
                try:
                    error_json = response.json()
                    error_message = error_json.get("error", {}).get("message", "")
                except Exception:
                    error_message = ""
                if "model is overloaded" in error_message:
                    logger.warning("Gemini API model is overloaded. Retrying...")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                logger.error(f"Gemini API error: {response.text}")
                return jsonify({"error": "Gemini API error", "details": response.text}), 500
            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.text}")
                return jsonify({"error": "Gemini API error", "details": response.text}), 500
            result = response.json()
            # Extract the AI's reply
            message = (
                result.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text")
            )
            if not message:
                logger.error("No AI response found in Gemini API reply.")
                return jsonify({"error": "No AI response found in Gemini API reply."}), 500
            logger.info("Gemini API call successful.")
            return jsonify({"response": message})
        except Exception as e:
            logger.error(f"Gemini API exception: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return jsonify({"error": str(e)}), 500
    
def get_git_version():
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').strip()
        commit_msg = subprocess.check_output(['git', 'log', '-1', '--pretty=%B']).decode('utf-8').strip()
        version = f"{commit_hash}: {commit_msg}"
        logger.info(f"Git version: {version}")
        return version
    except Exception as e:
        logger.error(f"Failed to get git version: {e}")
        return "unknown"

@app.route('/health')
def health():
    api_version = "2.0"
    num_task_groups = len(grouped)
    unique_tasks = set()
    for titles in grouped['task_title']:
        unique_tasks.update(titles)
    num_unique_tasks = len(unique_tasks)
    git_version = get_git_version()
    logger.info(f"/health checked. Version: {api_version}, Task groups: {num_task_groups}, Unique tasks: {num_unique_tasks}")
    return jsonify({
        "status": "ok",
        "message": "✅ Mathtatag API is running",
        "version": api_version,
        "git_version": git_version,
        "num_task_groups": num_task_groups,
        "num_unique_tasks": num_unique_tasks
    }), 200

def keep_alive():
    while True:
        try:
            logger.info("Sending keep-alive ping...")
            # Change the URL to your deployed app's health endpoint
            requests.get("https://mathtatag-api.onrender.com/health")
            logger.info("✅ Mathtatag API keep-alive ping sent and server is alive!")
        except Exception as e:
            logger.error(f"Keep-alive ping failed: {e}")
        time.sleep(600)  # Ping every 10 minutes

if __name__ == '__main__':
    threading.Thread(target=keep_alive, daemon=True).start()
    logger.info("Mathtatag API server starting...")
    app.run(debug=True, host='0.0.0.0')
