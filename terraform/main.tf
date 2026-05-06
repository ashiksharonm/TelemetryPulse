terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.1"
    }
  }
}

provider "docker" {}

# Example: Automating the Grafana container deployment
resource "docker_image" "grafana" {
  name         = "grafana/grafana:10.1.0"
  keep_locally = true
}

resource "docker_container" "grafana" {
  image = docker_image.grafana.image_id
  name  = "telemetry-grafana-tf"
  ports {
    internal = 3000
    external = 3001
  }
  networks_advanced {
    name = "telemetry-net"
  }
}
