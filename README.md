# DDoSMeasurement

sudo docker compose build
sudo docker compose up -d

sudo docker compose down -v
sudo docker system prune -a --volumes -f
sudo docker volume rm ping_data ddosmeasurement_ping_data || true 


curl -X POST http://social.kelvincomputers.org:5000/monitor -H "Content-Type: application/json" -d '{"server": "example.com"}'
curl "http://social.kelvincomputers.org:5000/results?server=example.com"



# docker run --rm -it ping-monitor --hostname google.com


sudo docker exec -it monitor_api sqlite3 /data/ping_stats.db "SELECT COUNT(*) FROM ping_data;"
sudo docker exec -it ping_monitor_example_com sqlite3 /data/ping_stats.db "SELECT COUNT(*) FROM ping_data;"

sudo docker volume ls
sudo docker volume inspect ping_data
sudo docker volume inspect ddosmeasurement_ping_data
sudo docker inspect ping_db | grep -A 5 "Mounts"
sudo docker inspect monitor_api | grep -A 5 "Mounts"
