from flask import Flask, render_template_string
import requests
import json
import os

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
ES_HOST = os.environ.get("ES_HOST", "192.168.56.11")
ES_PORT = os.environ.get("ES_PORT", "9200")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ELK AI Synthesis</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .card { background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .summary { background: #e8f4fd; border-left: 4px solid #007bff; padding: 15px; border-radius: 4px; line-height: 1.8; }
        .stats { display: flex; gap: 20px; flex-wrap: wrap; }
        .stat-box { background: #007bff; color: white; padding: 15px 25px; border-radius: 8px; text-align: center; }
        .stat-box h3 { margin: 0; font-size: 2em; }
        .stat-box p { margin: 5px 0 0 0; font-size: 0.9em; }
        .loading { color: #888; font-style: italic; }
        table { width: 100%; border-collapse: collapse; }
        th { background: #007bff; color: white; padding: 10px; text-align: left; }
        td { padding: 8px 10px; border-bottom: 1px solid #eee; }
        tr:hover { background: #f9f9f9; }
    </style>
</head>
<body>
    <h1> ELK Stack AI Synthesis</h1>

    <div class="card">
        <h2> Data Overview</h2>
        <div class="stats">
            <div class="stat-box">
                <h3>{{ total_logs }}</h3>
                <p>Total System Logs</p>
            </div>
            <div class="stat-box">
                <h3>{{ total_airports }}</h3>
                <p>Airports Indexed</p>
            </div>
            <div class="stat-box">
                <h3>{{ total_indices }}</h3>
                <p>Elasticsearch Indices</p>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>✈️Top Airports by Country</h2>
        <table>
            <tr><th>Airport Code</th><th>City</th><th>Country</th></tr>
            {% for airport in airports %}
            <tr>
                <td>{{ airport.code }}</td>
                <td>{{ airport.city }}</td>
                <td>{{ airport.country }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="card">
        <h2> AI Synthesis</h2>
        <div class="summary">{{ ai_summary }}</div>
    </div>
</body>
</html>
"""

def get_elasticsearch_stats():
    try:
        # Get indices stats
        indices_response = requests.get(f"http://{ES_HOST}:{ES_PORT}/_cat/indices?format=json", timeout=5)
        indices = indices_response.json()

        # Count logs
        total_logs = sum(int(i.get("docs.count", 0)) for i in indices if i["index"].startswith("filebeat"))

        # Count airports
        total_airports = sum(int(i.get("docs.count", 0)) for i in indices if i["index"].startswith("airports"))

        # Total indices
        total_indices = len([i for i in indices if not i["index"].startswith(".")])

        # Get airport data
        airports_response = requests.get(
            f"http://{ES_HOST}:{ES_PORT}/airports-*/_search",
            json={"size": 30, "_source": ["code", "city", "country", "name"]},
            timeout=5
        )
        airports_data = airports_response.json()
        airports = [hit["_source"] for hit in airports_data.get("hits", {}).get("hits", [])]

        # Get log counts per host
        log_stats_response = requests.post(
            f"http://{ES_HOST}:{ES_PORT}/filebeat-*/_search",
            json={
                "size": 0,
                "aggs": {
                    "logs_per_host": {
                        "terms": {"field": "agent.name.keyword", "size": 10}
                    }
                }
            },
            timeout=5
        )
        log_stats = log_stats_response.json()
        buckets = log_stats.get("aggregations", {}).get("logs_per_host", {}).get("buckets", [])
        host_stats = {b["key"]: b["doc_count"] for b in buckets}

        return {
            "total_logs": total_logs,
            "total_airports": total_airports,
            "total_indices": total_indices,
            "airports": airports,
            "host_stats": host_stats
        }
    except Exception as e:
        return {
            "total_logs": 0,
            "total_airports": 0,
            "total_indices": 0,
            "airports": [],
            "host_stats": {},
            "error": str(e)
        }

def get_ai_summary(stats):
    try:
        prompt = f"""You are a data analyst. Analyze this ELK stack data and provide a clear, concise synthesis in 4-5 sentences:

Infrastructure:
- 3 VMs monitored: elasticsearch (192.168.56.11), logstash (192.168.56.12), kibana (192.168.56.13)
- Total system logs collected: {stats['total_logs']}
- Log distribution per VM: {stats['host_stats']}
- Airports dataset: {stats['total_airports']} major world airports indexed with geolocation data
- Total Elasticsearch indices: {stats['total_indices']}

Please provide:
1. A summary of what data is being monitored
2. Key observations about the log distribution
3. What the airports dataset represents
4. Overall health assessment of the ELK stack"""

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500
            },
            timeout=30
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI summary unavailable: {str(e)}"

@app.route("/")
def index():
    stats = get_elasticsearch_stats()
    ai_summary = get_ai_summary(stats)
    return render_template_string(
        HTML_TEMPLATE,
        total_logs=stats["total_logs"],
        total_airports=stats["total_airports"],
        total_indices=stats["total_indices"],
        airports=stats["airports"],
        ai_summary=ai_summary
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("APP_PORT", 5000)))
