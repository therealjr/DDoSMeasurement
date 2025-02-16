import subprocess
import argparse
import re
import time
import statistics
import sqlite3
import logging
from datetime import datetime

# ✅ Setup Logging
logging.basicConfig(
    level=logging.DEBUG,  # ✅ Set logging level to DEBUG for detailed output
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]  # ✅ Log to console
)

# Function to get ping time
def get_ping_time(hostname):
    logging.info(f"Pinging {hostname}...")
    
    try:
        result = subprocess.run(
            ["ping", "-c", "1", hostname],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            logging.warning(f"Ping to {hostname} failed: {result.stderr.strip()}")
            return None

        match = re.search(r"time=([\d.]+)\s*ms", result.stdout)
        if match:
            ping_time = float(match.group(1))
            logging.info(f"Ping response: {ping_time}ms")
            return ping_time
        else:
            logging.warning(f"No valid response time found in ping output: {result.stdout.strip()}")
    
    except FileNotFoundError:
        logging.critical("Ping command not found! Ensure the `ping` utility is installed.")
    except Exception as e:
        logging.error(f"Unexpected error during ping: {e}")
    
    return None  # Return None if ping fails

# Function to insert data into SQLite
def save_to_db(db_path, server, timestamp, response_time):
    logging.debug(f"Saving data to database: {server}, {timestamp}, {response_time}ms")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ensure the table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ping_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server TEXT,
                timestamp REAL,
                response_time REAL
            )
        """)

        # Insert data
        cursor.execute("INSERT INTO ping_data (server, timestamp, response_time) VALUES (?, ?, ?)", 
                       (server, timestamp, response_time))
        conn.commit()
        conn.close()

        logging.info(f"Database updated successfully for {server} at {timestamp}")

    except sqlite3.OperationalError as e:
        logging.critical(f"Database connection error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error inserting data into DB: {e}")

# Main function
def main():
    logging.info("Starting Ping Monitoring Script...")

    parser = argparse.ArgumentParser(description="Measure traffic of remote webserver.")
    parser.add_argument('--hostname', required=True, help="Target server")
    args = parser.parse_args()

    db_path = "/db/ping_stats.db"
    sliding_window_size = 100
    response_times = []
    min_delay = 0.5
    max_delay = 10
    delay = min_delay

    logging.info(f"Monitoring {args.hostname}, results stored in {db_path}")

    while True:
        current_time_stamp = datetime.now().timestamp()
        response_time = get_ping_time(args.hostname)

        # Handle None case for continuity
        if response_time is None:
            if response_times:
                response_time = max(response_times)  # Keep continuity
                logging.warning(f"No response from {args.hostname}. Using max recorded value: {response_time}ms")
            else:
                response_time = None  # If no past data exists, keep None
                logging.error(f"First ping to {args.hostname} failed, waiting for next attempt.")

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

        logging.info(f"Logged {response_time}ms for {args.hostname} at {current_time_stamp} | Next check in {delay:.2f}s")
        
        time.sleep(delay)

if __name__ == "__main__":
    main()
