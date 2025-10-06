"""
Dify Workflow Service
Handles integration with Dify workflows for HR automation tasks
"""
import json
import uuid
from typing import Dict, Any, AsyncGenerator, Optional
import httpx
from fastapi import HTTPException
from app.core.config import settings
from app.core.logging import logger


class DifyService:
    """Service for interacting with Dify workflows"""
    
    def __init__(self):
        self.base_url = settings.DIFY_BASE_URL
        self.api_key = settings.DIFY_API_KEY
        self.user_id = settings.DIFY_USER_ID
        
        if not self.api_key:
            raise ValueError("DIFY_API_KEY is required but not configured")
    
    async def call_workflow_stream(
        self,
        workflow_type: int,
        query: str,
        conversation_id: Optional[str] = None,
        additional_inputs: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Call Dify workflow with streaming response
        
        Args:
            workflow_type: Type of workflow (1=JD生成, 2=简历评价, etc.)
            query: User query/prompt
            conversation_id: Optional conversation ID for context
            additional_inputs: Additional input parameters
            
        Yields:
            Streaming response data
        """
        try:
            # Prepare request data
            inputs = {"type": workflow_type}
            if additional_inputs:
                inputs.update(additional_inputs)
            
            request_data = {
                "inputs": inputs,
                "query": query,
                "response_mode": "streaming",
                "conversation_id": conversation_id or "",
                "user": self.user_id
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Calling Dify workflow type {workflow_type} with query: {query[:100]}...")
            
            # Make streaming request to Dify
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat-messages",
                    headers=headers,
                    json=request_data
                ) as response:
                    
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Dify API error: {response.status_code} - {error_text}")
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"Dify API error: {error_text.decode()}"
                        )
                    
                    # Stream the response
                    async for chunk in response.aiter_lines():
                        if chunk:
                            # Remove 'data: ' prefix if present
                            if chunk.startswith("data: "):
                                chunk = chunk[6:]
                            
                            # Skip empty lines and [DONE] markers
                            if not chunk or chunk == "[DONE]":
                                continue
                            
                            try:
                                # Parse JSON chunk
                                data = json.loads(chunk)
                                yield chunk
                            except json.JSONDecodeError:
                                # If not valid JSON, yield as is
                                yield chunk
                                
        except httpx.TimeoutException:
            logger.error("Dify API request timeout")
            raise HTTPException(status_code=504, detail="Dify API request timeout")
        except httpx.RequestError as e:
            logger.error(f"Dify API request error: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Dify API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Dify workflow call: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    async def call_workflow_sync(
        self,
        workflow_type: int,
        query: str,
        conversation_id: Optional[str] = None,
        additional_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call Dify workflow with synchronous response
        
        Args:
            workflow_type: Type of workflow
            query: User query/prompt
            conversation_id: Optional conversation ID
            additional_inputs: Additional input parameters
            
        Returns:
            Complete response data
        """
        try:
            inputs = {"type": workflow_type}
            if additional_inputs:
                inputs.update(additional_inputs)
            
            request_data = {
                "inputs": inputs,
                "query": query,
                "response_mode": "blocking",
                "conversation_id": conversation_id or "",
                "user": self.user_id
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Calling Dify workflow type {workflow_type} (sync) with query: {query[:100]}...")
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat-messages",
                    headers=headers,
                    json=request_data
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Dify API error: {response.status_code} - {error_text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Dify API error: {error_text}"
                    )
                
                return response.json()
                
        except httpx.TimeoutException:
            logger.error("Dify API request timeout")
            raise HTTPException(status_code=504, detail="Dify API request timeout")
        except httpx.RequestError as e:
            logger.error(f"Dify API request error: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Dify API request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in Dify workflow call: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    def get_workflow_type_description(self, workflow_type: int) -> str:
        """Get description for workflow type"""
        workflow_descriptions = {
            1: "生成岗位JD (Job Description)",
            2: "简历评价模型 (Resume Evaluation)",
            3: "面试方案生成 (Interview Plan Generation)",
            4: "候选人匹配 (Candidate Matching)",
            5: "薪资建议 (Salary Recommendation)"
        }
        return workflow_descriptions.get(workflow_type, f"未知工作流类型 {workflow_type}")