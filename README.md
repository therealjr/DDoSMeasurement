# DDoSMeasurement

docker compose build
docker compose up -d

sudo docker system prune -a --volumes -f


curl -X POST http://social.kelvincomputers.org:5000/monitor -H "Content-Type: application/json" -d '{"server": "example.com"}'
curl "http://social.kelvincomputers.org:5000/results?server=example.com"



# docker run --rm -it ping-monitor --hostname google.com
