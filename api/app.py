from flask import Flask, request, jsonify
import sqlite3
import subprocess
import os
import logging
from datetime import datetime

# ✅ Setup Logging
logging.basicConfig(
    level=logging.DEBUG,  # ✅ Set logging to DEBUG for detailed output
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

app = Flask(__name__)
DB_PATH = "/db/ping_stats.db"  # ✅ Use correct DB path inside the container
PING_MONITOR_PATH = "/ping_monitor"  # ✅ Must match mounted path in `docker-compose.yml`
HOST_DB_PATH = "/db"  # ✅ Ensure correct database path

# Function to check if a website is already being monitored
def is_website_monitored(server):
    container_name = f"ping_monitor_{server.replace('.', '_')}"

    try:
        logging.info(f"🔎 Checking if {server} is already monitored...")

        # ✅ Ensure the database exists
        if not os.path.exists(DB_PATH):
            logging.error(f"❌ Database file not found at {DB_PATH}")
            return False

        # ✅ Check if the server exists in the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ping_data WHERE server = ?", (server,))
        db_result = cursor.fetchone()[0]
        conn.close()

        # ✅ Check if the container is running
        running_containers = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True
        ).stdout.strip().split("\n")

        # ✅ Ensure proper comparison
        running_containers = [c.strip() for c in running_containers if c.strip()]  # Remove empty strings
        is_running = container_name in running_containers

        logging.info(f"🔍 Container: {container_name} | Running: {is_running} | Found in DB: {db_result > 0}")

        # ✅ Return True only if BOTH the database and container match
        return db_result > 0 and is_running

    except sqlite3.OperationalError as e:
        logging.error(f"❌ Database error while checking {server}: {e}")
        return False
    except subprocess.SubprocessError as e:
        logging.error(f"❌ Docker error while checking {server}: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Unexpected error while checking {server}: {e}")
        return False

# Function to retrieve monitoring results
def get_monitoring_results(server):
    logging.info(f"Retrieving monitoring results for {server}...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT timestamp, response_time FROM ping_data WHERE server = ? ORDER BY timestamp DESC LIMIT 10",
            (server,)
        )
        data = cursor.fetchall()
        conn.close()

        logging.info(f"Retrieved {len(data)} records for {server}")
        return [{"timestamp": row[0], "response_time": row[1]} for row in data]
    except Exception as e:
        logging.error(f"Error retrieving monitoring results for {server}: {e}")
        return []

def start_monitoring(server):
    container_name = f"ping_monitor_{server.replace('.', '_')}"
    logging.info(f"Starting monitoring for {server}...")

    try:
        # Check if the container already exists
        existing_containers = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True
        ).stdout.split("\n")

        if container_name in existing_containers:
            logging.info(f"Container {container_name} already exists. Restarting it.")
            subprocess.run(["docker", "start", container_name], check=True)
            return

        # Build a new image for the server
        logging.info(f"Building image `{container_name}` for {server}...")
        build_process = subprocess.run(
            ["docker", "build", "-t", container_name, PING_MONITOR_PATH],
            capture_output=True,
            text=True
        )
        if build_process.returncode != 0:
            logging.error(f"Failed to build image for {server}: {build_process.stderr}")
            return

        logging.info(f"Successfully built image `{container_name}`.")

        # Run the monitoring container
        logging.info(f"Running monitoring container `{container_name}` for {server}...")
        run_process = subprocess.run([
            "docker", "run", "-d",
            "--name", container_name,
            "--network", "host",
            "-e", f"DB_PATH=/db/ping_stats.db",
            "-v", "ping_data:/db",
            container_name,
            "--hostname", server
        ], capture_output=True, text=True)

        if run_process.returncode != 0:
            logging.error(f"Failed to start monitoring container `{container_name}`: {run_process.stderr}")
            return

        logging.info(f"Started monitoring container `{container_name}` for {server}.")

    except Exception as e:
        logging.error(f"Error starting monitoring for {server}: {e}")

@app.route("/monitor", methods=["POST"])
def monitor():
    data = request.get_json()
    server = data.get("server")

    if not server:
        logging.warning("Monitor request received without a server field.")
        return jsonify({"error": "No server provided"}), 400

    logging.info(f"Received monitor request for {server}.")

    if is_website_monitored(server):
        logging.info(f"{server} is already being monitored. Returning existing data.")
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
        logging.warning("Results request received without a server field.")
        return jsonify({"error": "No server provided"}), 400

    logging.info(f"Received results request for {server}.")

    if not is_website_monitored(server):
        logging.info(f"No monitoring data available for {server}.")
        return jsonify({"message": "No monitoring data available"}), 404

    return jsonify({
        "server": server,
        "data": get_monitoring_results(server)
    })

if __name__ == "__main__":
    logging.info("Starting Monitor API service...")
    app.run(host="0.0.0.0", port=5000)
