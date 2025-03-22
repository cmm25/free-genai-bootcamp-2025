from fastapi import HTTPException
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo
)
from comps.cores.mega.constants import ServiceType, ServiceRoleType
from comps import MicroService, ServiceOrchestrator
import os
import json

EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "localhost")
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", 8008)


class ExampleService:
    def __init__(self, host="0.0.0.0", port=8000):
        print(123)
        self.host = host
        self.port = port
        self.endpoint = "/v1/example-service"
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):

        # embedding = MicroService(
        #    name="embedding",
        #    host=EMBEDDING_SERVICE_HOST_IP,
        #    port=EMBEDDING_SERVICE_PORT,
        #    endpoint="/v1/embeddings",
        #    use_remote_service=True,
        #    service_type=ServiceType.EMBEDDING,
        # )
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        print(f"\nConfiguring LLM service:")
        print(f"- Host: {LLM_SERVICE_HOST_IP}")
        print(f"- Port: {LLM_SERVICE_PORT}")
        print(f"- Endpoint: {llm.endpoint}")
        print(f"- Full URL: http://{LLM_SERVICE_HOST_IP}:{LLM_SERVICE_PORT}{llm.endpoint}") 
        self.megaservice.add(llm)

    def start(self):

        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )

        self.service.add_route(
            self.endpoint, self.handle_request, methods=["POST"])
        print(f"Service configured with endpoint: {self.endpoint}")
        self.service.start()

    async def handle_request(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        try:
            # Ensure messages is properly formatted
            messages = (
                [{"role": "user", "content": request.messages}]
                if isinstance(request.messages, str)
                else request.messages
            )

            # Format the request for Ollama
            ollama_request = {
                "model": request.model or "llama2",  # Changed default model name
                "messages": messages,
                "stream": False
            }

            # Schedule the request through the orchestrator
            result = await self.megaservice.schedule(ollama_request)

            # Improved response handling
            if not result:
                raise ValueError("No response received from LLM service")

            llm_response = result[0].get('llm/MicroService')
            if not llm_response:
                raise ValueError("Invalid response format from LLM service")

            # Extract content from response
            content = ""
            if hasattr(llm_response, 'body'):
                response_body = b""
                async for chunk in llm_response.body_iterator:
                    response_body += chunk
                content = response_body.decode('utf-8')
            else:
                raise ValueError("No response content available")

            return ChatCompletionResponse(
                model=request.model or "llama2",
                choices=[
                    ChatCompletionResponseChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=content
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=UsageInfo(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0
                )
            )

        except Exception as e:
            # More detailed error handling
            error_msg = f"Error processing request: {str(e)}"
            print(error_msg)  # Log the error
            raise HTTPException(status_code=500, detail=error_msg)


example = ExampleService()
example.add_remote_service()
example.start()
