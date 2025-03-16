# from fastapi import APIRouter, Depends, HTTPException, status
# from typing import List
# import uuid
# from datetime import datetime

# from ..models.models import User, Conversation, ConversationCreate, ConversationUpdate, ChatRequest, ChatResponse, FeedbackRequest
# from ..core.auth import get_current_active_user
# from ..db.database import (
#     create_conversation,
#     get_conversation,
#     get_user_conversations,
#     update_conversation,
#     delete_conversation,
#     add_messages_to_conversation,
#     update_message_feedback
# )

# router = APIRouter()

# # Conversation CRUD routes
# @router.post("/conversations", response_model=Conversation)
# async def create_new_conversation(
#     conversation: ConversationCreate,
#     current_user: User = Depends(get_current_active_user)
# ):
#     return await create_conversation(
#         user_id=current_user.id,
#         title=conversation.title,
#         messages=[msg.dict() for msg in conversation.messages]
#     )

# @router.get("/conversations", response_model=List[Conversation])
# async def read_conversations(current_user: User = Depends(get_current_active_user)):
#     return await get_user_conversations(current_user.id)

# @router.get("/conversations/{conversation_id}", response_model=Conversation)
# async def read_conversation(
#     conversation_id: str,
#     current_user: User = Depends(get_current_active_user)
# ):
#     conversation = await get_conversation(conversation_id, current_user.id)
#     if not conversation:
#         raise HTTPException(status_code=404, detail="Conversation not found")
#     return conversation

# @router.put("/conversations/{conversation_id}", response_model=Conversation)
# async def update_existing_conversation(
#     conversation_id: str,
#     conversation_update: ConversationUpdate,
#     current_user: User = Depends(get_current_active_user)
# ):
#     # Check if conversation exists
#     conversation = await get_conversation(conversation_id, current_user.id)
#     if not conversation:
#         raise HTTPException(status_code=404, detail="Conversation not found")
    
#     # Prepare update data
#     update_data = {}
#     if conversation_update.title is not None:
#         update_data["title"] = conversation_update.title
#     if conversation_update.messages is not None:
#         update_data["messages"] = [m.dict() for m in conversation_update.messages]
    
#     # Update conversation
#     updated_conversation = await update_conversation(
#         conversation_id=conversation_id,
#         update_data=update_data,
#         user_id=current_user.id
#     )
    
#     return updated_conversation

# @router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_existing_conversation(
#     conversation_id: str,
#     current_user: User = Depends(get_current_active_user)
# ):
#     success = await delete_conversation(conversation_id, current_user.id)
#     if not success:
#         raise HTTPException(status_code=404, detail="Conversation not found")
#     return None

# # Chat endpoint
# @router.post("/chat", response_model=ChatResponse)
# async def chat(
#     request: ChatRequest,
#     current_user: User = Depends(get_current_active_user)
# ):
#     """
#     If request.conversation_id is provided and exists, update it;
#     otherwise, create a new conversation.
#     """
#     # Create user message
#     user_message = {
#         "id": str(uuid.uuid4()),
#         "role": "user",
#         "content": request.message,
#         "feedback": None
#     }
    
#     # Generate AI response (mock for now)
#     response_text = f"You said: {request.message}. This is a mock AI response."
#     ai_message = {
#         "id": str(uuid.uuid4()),
#         "role": "assistant",
#         "content": response_text,
#         "feedback": None
#     }
    
#     # If conversation_id is provided, try to update existing conversation
#     if request.conversation_id:
#         conversation = await get_conversation(request.conversation_id, current_user.id)
#         if conversation:
#             # If the conversation title is the default, update it with the text of the first message
#             if conversation.title == "New Conversation":
#                 new_title = request.message[:30] + "..." if len(request.message) > 30 else request.message
#                 await update_conversation(
#                     conversation_id=request.conversation_id,
#                     update_data={"title": new_title},
#                     user_id=current_user.id
#                 )
#             # Add messages to existing conversation
#             await add_messages_to_conversation(
#                 conversation_id=request.conversation_id,
#                 messages=[user_message, ai_message],
#                 user_id=current_user.id
#             )
#             return ChatResponse(
#                 message=response_text,
#                 conversation_id=request.conversation_id
#             )
    
#     # Create a new conversation with the first message as the title
#     title = request.message[:30] + "..." if len(request.message) > 30 else request.message
#     conversation = await create_conversation(
#         user_id=current_user.id,
#         title=title,
#         messages=[]
#     )
    
#     # Add messages to the new conversation
#     await add_messages_to_conversation(
#         conversation_id=conversation.id,
#         messages=[user_message, ai_message],
#         user_id=current_user.id
#     )
    
#     return ChatResponse(
#         message=response_text,
#         conversation_id=conversation.id
#     )

# # Feedback endpoint
# @router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
# async def submit_feedback(
#     feedback: FeedbackRequest,
#     current_user: User = Depends(get_current_active_user)
# ):
#     # Update message feedback
#     success = await update_message_feedback(
#         conversation_id=feedback.conversation_id,
#         message_id=feedback.message_id,
#         feedback={
#             "rating": feedback.rating,
#             "comment": feedback.comment
#         },
#         user_id=current_user.id
#     )
    
#     if not success:
#         raise HTTPException(status_code=404, detail="Conversation or message not found")
    
#     return None

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import uuid

from datetime import datetime

from ..models.models import (
    User,
    Conversation,
    ConversationCreate,
    ConversationUpdate,
    ChatRequest,
    ChatResponse,
    FeedbackRequest
)
from ..core.auth import get_current_active_user
from ..db.database import (
    create_conversation,
    get_conversation,
    get_user_conversations,
    update_conversation,
    delete_conversation,
    add_messages_to_conversation,
    update_message_feedback
)

import httpx

router = APIRouter()

############################
# Conversation CRUD routes #
############################

@router.post("/conversations", response_model=Conversation)
async def create_new_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_active_user)
):
    return await create_conversation(
        user_id=current_user.id,
        title=conversation.title,
        messages=[msg.dict() for msg in conversation.messages]
    )

@router.get("/conversations", response_model=List[Conversation])
async def read_conversations(current_user: User = Depends(get_current_active_user)):
    return await get_user_conversations(current_user.id)

@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def read_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    conversation = await get_conversation(conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def update_existing_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(get_current_active_user)
):
    # Check if conversation exists
    conversation = await get_conversation(conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Prepare update data
    update_data = {}
    if conversation_update.title is not None:
        update_data["title"] = conversation_update.title
    if conversation_update.messages is not None:
        update_data["messages"] = [m.dict() for m in conversation_update.messages]

    # Update conversation
    updated_conversation = await update_conversation(
        conversation_id=conversation_id,
        update_data=update_data,
        user_id=current_user.id
    )

    return updated_conversation

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    success = await delete_conversation(conversation_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return None

###################
# Chat endpoint   #
###################

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    If request.conversation_id is provided and exists, update it;
    otherwise, create a new conversation.
    """
    # Create user message
    user_message = {
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": request.message,
        "feedback": None
    }

    # Call the /provide_response endpoint from the other script
    # to get the AI-generated answer
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://localhost:8001/provide_response",
                params={"question": request.message}
            )
            response.raise_for_status()
            data = response.json()
            # We'll use the "final_response" field as the AI's reply
            response_text = data.get("final_response", "I'm sorry, no response available.")
        except Exception as e:
            # In case of error, return a fallback
            response_text = f"AI service error: {str(e)}"

    ai_message = {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": response_text,
        "feedback": None
    }

    # If conversation_id is provided, try to update existing conversation
    if request.conversation_id:
        conversation = await get_conversation(request.conversation_id, current_user.id)
        if conversation:
            # If the conversation title is the default, update it with the text of the first message
            if conversation.title == "New Conversation":
                new_title = request.message[:30] + "..." if len(request.message) > 30 else request.message
                await update_conversation(
                    conversation_id=request.conversation_id,
                    update_data={"title": new_title},
                    user_id=current_user.id
                )
            # Add messages to existing conversation
            await add_messages_to_conversation(
                conversation_id=request.conversation_id,
                messages=[user_message, ai_message],
                user_id=current_user.id
            )
            return ChatResponse(
                message=response_text,
                conversation_id=request.conversation_id
            )

    # Create a new conversation with the first message as the title
    title = request.message[:30] + "..." if len(request.message) > 30 else request.message
    conversation = await create_conversation(
        user_id=current_user.id,
        title=title,
        messages=[]
    )

    # Add messages to the new conversation
    await add_messages_to_conversation(
        conversation_id=conversation.id,
        messages=[user_message, ai_message],
        user_id=current_user.id
    )

    return ChatResponse(
        message=response_text,
        conversation_id=conversation.id
    )

####################
# Feedback endpoint#
####################

@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def submit_feedback(
    feedback: FeedbackRequest,
    current_user: User = Depends(get_current_active_user)
):
    # Update message feedback
    success = await update_message_feedback(
        conversation_id=feedback.conversation_id,
        message_id=feedback.message_id,
        feedback={
            "rating": feedback.rating,
            "comment": feedback.comment
        },
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Conversation or message not found")

    return None
