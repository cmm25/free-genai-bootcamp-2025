# Docker Compose Setup for Jaeger and Ollama Server

## Overview
This repository provides a Docker Compose configuration to run two key services:
- **Jaeger** for distributed tracing.
- **Ollama-Server** for serving large language models.

Using Windows with Docker Desktop and the Visual Studio Docker extension simplifies the process by automatically managing networking and environment configuration. Manual IP discovery and variable setup are not required in this environment.

## Requirements
- Windows OS with Docker Desktop installed.
- Visual Studio with the Docker extension (or any IDE that supports Docker integration).

## Running the Services
Launch the project directly from Visual Studio using the Docker extension. The integration with Docker Desktop automatically handles container startup, port mapping, and environment variable provisioning. Simply open the compose file and run the services—no manual adjustments are needed.

## Service Configuration
**Jaeger Service**
- **Image:** `jaegertracing/all-in-one:latest`
- **Ports:**  
  - `16686` (Jaeger UI)  
  - `4317` and `4318` (trace data)
  - `9411` (Zipkin compatibility)
- **IPC Mode:** `host`
- **Environment:** Inherits proxy settings and sets `COLLECTOR_ZIPKIN_HOST_PORT` to `9411`.
- **Restart Policy:** `unless-stopped`

**Ollama-Server Service**
- **Image:** `ollama/ollama`
- **Port Mapping:** Maps container port `11434` to the host port defined by `LLM_ENDPOINT_PORT` (default is `8008`).
- **Environment:** Includes proxy variables and passes `LLM_MODEL_ID` and `host_ip`. In this Windows setup, these values are automatically managed by Docker Desktop and the VS extension.

## Environment Variables
The Compose file references several environment variables (e.g., `LLM_MODEL_ID` and `host_ip`). In this configuration on Windows with Docker Desktop and the VS extension, these variables are managed automatically. There is no need for manual IP lookup or additional configuration steps—the extension supplies the necessary settings for local development.

## Networking
The services run on the default bridge network provided by Docker Desktop. This ensures seamless inter-container communication without any extra network configuration.
