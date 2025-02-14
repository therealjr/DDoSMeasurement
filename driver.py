import subprocess
import argparse
import re
import time
import statistics
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

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

def main():
    parser = argparse.ArgumentParser(description="Measure traffic of remote webserver.")
    parser.add_argument('--hostname', required=True, help="Target server")
    args = parser.parse_args()

    sliding_window_size = 100
    response_times = []
    time_stamps = []
    min_delay = 0.5
    max_delay = 10
    delay = min_delay

    plt.ion()  # Interactive mode
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlabel("Time")
    ax.set_ylabel("Response Time (ms)")
    ax.set_title(f"Server Response Time: {args.hostname}")

    while True:
        current_time_stamp = datetime.now().timestamp()
        response_time = get_ping_time(args.hostname)
        
        if response_time is None and response_times:
            response_time = max(response_times)  # Keep the graph continuous at max value

        response_times.append(response_time)
        time_stamps.append(current_time_stamp)

        # Keep only the latest `sliding_window_size` values
        response_times = response_times[-sliding_window_size:]
        time_stamps = time_stamps[-sliding_window_size:]

        # Compute statistics
        valid_responses = [r for r in response_times if r is not None]
        if valid_responses:
            mean_time = statistics.mean(valid_responses)
            std_dev = statistics.stdev(valid_responses) if len(valid_responses) > 1 else 0
        else:
            mean_time, std_dev = 0, 0

        # Adjust delay dynamically
        delay = min_delay + (std_dev + mean_time) / 50  
        delay = max(min_delay, min(delay, max_delay))

        # Update plot
        ax.clear()
        ax.set_xlabel("Time")
        ax.set_ylabel("Response Time (ms)")
        ax.set_title(f"Server Response Time: {args.hostname}")

        if len(valid_responses) > 1:
            norm = plt.Normalize(min(valid_responses), max(valid_responses))
            colors = plt.cm.RdYlGn_r(norm(np.array(response_times, dtype=np.float32)))
        else:
            colors = ['green'] * len(response_times)

        # Plot line with dynamic color
        ax.plot(time_stamps, response_times, color="black", linewidth=2, zorder=3)

        # Shaded region under the line
        for i in range(len(time_stamps) - 1):
            if response_times[i] is not None and response_times[i+1] is not None:
                ax.fill_between(
                    time_stamps[i:i+2], 
                    response_times[i:i+2], 
                    color=colors[i], 
                    alpha=0.3  # Fading effect
                )

        # Mark server failures with black dots
        for t, r in zip(time_stamps, response_times):
            if r is not None and r == max(response_times):
                ax.scatter(t, r, color='black', s=60, marker='o', label="Server Down" if 'Server Down' not in ax.get_legend_handles_labels()[1] else "")

        plt.pause(0.01)  # Update plot dynamically

        print(f"Response times: {response_times}")
        print(f"Delay: {delay}")

        time.sleep(delay)

if __name__ == "__main__":
    main()
