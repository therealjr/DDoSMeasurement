from flask import Flask, request, jsonify
import sqlite3
import subprocess
import os

app = Flask(__name__)
DB_PATH = "/data/ping_stats.db"

# Function to check if a website is already being monitored
def is_website_monitored(server):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ping_data WHERE server = ?", (server,))
    result = cursor.fetchone()[0]
    conn.close()
    return result > 0  # Returns True if monitoring is active

# Function to retrieve monitoring results
def get_monitoring_results(server):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, response_time FROM ping_data WHERE server = ? ORDER BY timestamp DESC LIMIT 10", (server,))
    data = cursor.fetchall()
    conn.close()
    return [{"timestamp": row[0], "response_time": row[1]} for row in data]

# Function to spawn a new monitoring container
def start_monitoring(server):
    container_name = f"ping_monitor_{server.replace('.', '_')}"
    
    # Run the Docker command on the host via the mounted socket
    subprocess.run([
        "docker", "run", "-d",
        "--name", container_name,
        "--network", "host",  # 🛠 Use "host" networking for full access
        "-e", f"DB_PATH={DB_PATH}",
        "-v", "ping_data:/data",
        "ping_monitor",  # Use the correct image name
        "--hostname", server
    ], check=True)

@app.route("/monitor", methods=["POST"])
def monitor():
    data = request.get_json()
    server = data.get("server")

    if not server:
        return jsonify({"error": "No server provided"}), 400

    if is_website_monitored(server):
        return jsonify({
            "message": "Already monitoring",
            "data": get_monitoring_results(server)
        })

    # Start monitoring in a new container
    start_monitoring(server)

    return jsonify({"message": f"Started monitoring {server}"}), 201

@app.route("/results", methods=["GET"])
def results():
    server = request.args.get("server")

    if not server:
        return jsonify({"error": "No server provided"}), 400

    if not is_website_monitored(server):
        return jsonify({"message": "No monitoring data available"}), 404

    return jsonify({
        "server": server,
        "data": get_monitoring_results(server)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
