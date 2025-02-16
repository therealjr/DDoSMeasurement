# DDoSMeasurement

docker compose build
docker compose up -d

sudo docker system prune -a --volumes -f


curl -X POST http://social.kelvincomputers.org:5000/monitor -H "Content-Type: application/json" -d '{"server": "example.com"}'
curl "http://social.kelvincomputers.org:5000/results?server=example.com"



# docker run --rm -it ping-monitor --hostname google.com


# Check database inside monitor_api
docker exec -it monitor_api sqlite3 /db/ping_stats.db "SELECT COUNT(*) FROM ping_data;"

# Check database inside ping_monitor
docker exec -it ping_monitor_example_com sqlite3 /db/ping_stats.db "SELECT COUNT(*) FROM ping_data;"
