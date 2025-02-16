import subprocess
import argparse
import re
import time
import statistics
import sqlite3
from datetime import datetime

# Function to get ping time
def get_ping_time(hostname):
    try:
        result = subprocess.run(
            ["ping", "-c", "1", hostname],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        match = re.search(r"time=([\d.]+)\s*ms", result.stdout)
        if match:
            return float(match.group(1))
    except Exception as e:
        print(f"Error: {e}")
    return None  # Return None if ping fails

# Function to insert data into SQLite
def save_to_db(db_path, server, timestamp, response_time):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ping_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server TEXT,
            timestamp REAL,
            response_time REAL
        )
    """)
    cursor.execute("INSERT INTO ping_data (server, timestamp, response_time) VALUES (?, ?, ?)", 
                   (server, timestamp, response_time))
    conn.commit()
    conn.close()

# Main function
def main():
    parser = argparse.ArgumentParser(description="Measure traffic of remote webserver.")
    parser.add_argument('--hostname', required=True, help="Target server")
    args = parser.parse_args()

    db_path = "/db/ping_stats.db"
    sliding_window_size = 100
    response_times = []
    min_delay = 0.5
    max_delay = 10
    delay = min_delay

    while True:
        current_time_stamp = datetime.now().timestamp()
        response_time = get_ping_time(args.hostname)

        if response_time is None and response_times:
            response_time = max(response_times)  # Keep continuity in the dataset

        response_times.append(response_time)
        response_times = response_times[-sliding_window_size:]  # Keep only latest values

        # Compute statistics
        valid_responses = [r for r in response_times if r is not None]
        if valid_responses:
            mean_time = statistics.mean(valid_responses)
            std_dev = statistics.stdev(valid_responses) if len(valid_responses) > 1 else 0
        else:
            mean_time, std_dev = 0, 0

        # Save to the database
        save_to_db(db_path, args.hostname, current_time_stamp, response_time)

        # Adjust delay dynamically
        delay = min_delay + (std_dev + mean_time) / 50  
        delay = max(min_delay, min(delay, max_delay))

        print(f"Logged {response_time}ms for {args.hostname} at {current_time_stamp} | Next check in {delay:.2f}s")

        time.sleep(delay)

if __name__ == "__main__":
    main()
