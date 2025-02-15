from flask import Flask, request, jsonify
import sqlite3
import subprocess
import os

app = Flask(__name__)
DB_PATH = "/data/ping_stats.db"
PING_MONITOR_PATH = os.path.abspath("../ping_monitor")  # Get absolute path on host
HOST_DB_PATH = os.path.abspath("../ping_data")  # Ensure absolute path

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

def start_monitoring(server):
    container_name = f"ping_monitor_{server.replace('.', '_')}"
    image_name = f"ping_monitor_{server.replace('.', '_')}"
    
    # Step 1: Check if the container already exists
    result = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )
    
    existing_containers = result.stdout.split("\n")
    
    if container_name in existing_containers:
        print(f"Container {container_name} already exists. Starting it.")
        subprocess.run(["docker", "start", container_name], check=True)
        return

    # Step 2: Ensure the unique `ping_monitor_<server>` image exists
    image_check = subprocess.run(
        ["docker", "images", "-q", image_name],
        capture_output=True,
        text=True
    )

    if not image_check.stdout.strip():
        print(f"Building the `{image_name}` image first...")
        subprocess.run(["docker", "build", "-t", image_name, PING_MONITOR_PATH], check=True)

    # Step 3: Run the new monitoring container with its unique image
    subprocess.run([
        "docker", "run", "-d",
        "--name", container_name,
        "--network", "host",
        "-e", f"DB_PATH=/db/ping_stats.db",  # Change path to avoid conflict
        "-v", f"{PING_MONITOR_PATH}:/app",  # Mount the code separately
        "-v", f"{HOST_DB_PATH}:/db",  # Mount database separately
        image_name,
        "--hostname", server
    ], check=True)
    
    print(f"Started monitoring container {container_name} for {server}")

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
