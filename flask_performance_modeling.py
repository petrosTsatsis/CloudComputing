from flask import Flask
import requests
import time
import psutil
from tabulate import tabulate
import statistics

# create a Flask web application
app = Flask(__name__)

# define the api key and the url that fetches 100 tracks
LASTFM_API_KEY = "0d9d73635f49a0937227f959d55f53dd"
LASTFM_API_URL = f"http://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks&tag=pop&api_key={LASTFM_API_KEY}&format=json&limit=100&album=1"

# define the 2 workloads
workloads = [
    {'batch_size': 36, 'frequency': 1},
    {'batch_size': 1, 'frequency': 36},
]

# method that runs the experiments
def run_experiment(workload):
    global response
    response_times = []
    cpu_utilizations = []
    memories = []
    bandwidths = []

    for _ in range(workload['batch_size']):
        start_time = time.time()

        for _ in range(workload['batch_size']):
            try:
                response = requests.get(LASTFM_API_URL, timeout=5)
                data = response.json()
            except requests.exceptions.RequestException as e:
                print(f"Error making request: {e}")

        end_time = time.time()
        response_time = end_time - start_time

        # collect the metrics we need
        cpu_utilization = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent

        bytes_sent = len(response.content) if response and response.content else 0
        bandwidth = bytes_sent / response_time if response_time > 0 else 0

        # save the metrics for every iteration
        response_times.append(response_time)
        cpu_utilizations.append(cpu_utilization)
        memories.append(memory)
        bandwidths.append(bandwidth)

    tail_latency = max(response_times)

    return {
        'workload': workload,
        'response_times': response_times,
        'cpu_utilizations': cpu_utilizations,
        'memories': memories,
        'bandwidths': bandwidths,
        'tail_latency': tail_latency
    }

@app.route('/', methods=['GET'])
def get_lastfm_data():
    results = []

    # run experiments for each workload
    for workload in workloads:
        result = run_experiment(workload)
        results.append(result)

    headers = ['Batch Size', 'Frequency', 'Avg Response Time', 'Avg CPU Utilization', 'Avg Memory', 'Avg Bandwidth', 'Tail Latency']
    table_data = []

    # calculate the metrics and statistics
    for result in results:
        avg_response_time = statistics.mean(result['response_times'])
        avg_cpu_utilization = statistics.mean(result['cpu_utilizations'])
        avg_memory = statistics.mean(result['memories'])
        avg_bandwidth = statistics.mean(result['bandwidths'])
        avg_tail_latency = result['tail_latency']

        table_data.append([
            result['workload']['batch_size'],
            result['workload']['frequency'],
            avg_response_time,
            avg_cpu_utilization,
            avg_memory,
            avg_bandwidth,
            avg_tail_latency
        ])
    # display the results
    print(tabulate(table_data, headers=headers, tablefmt='grid'))
    return ''
# run the app
if __name__ == '__main__':
    app.run(debug=True)