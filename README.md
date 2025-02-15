# DDoSMeasurement

docker-compose build
docker-compose up -d

curl -X POST http://localhost:5000/monitor -H "Content-Type: application/json" -d '{"server": "example.com"}'
curl "http://localhost:5000/results?server=example.com"



# docker run --rm -it ping-monitor --hostname google.com
