from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.prompts.system_prompt import SYSTEM_PROMPT

from app.utils.calorie_calc import calculate_calorie_target
from app.rag.chain import generate_plan


# --- Enums for validation ---

class SexEnum(str, Enum):
    male = "male"
    female = "female"


class GoalEnum(str, Enum):
    lose = "lose"
    aggressive_lose = "aggressive_lose"
    maintain = "maintain"
    recomp = "recomp"
    lean_bulk = "lean_bulk"
    bulk = "bulk"


class ActivityEnum(str, Enum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    active = "active"
    very_active = "very_active"


class PlanDurationEnum(str, Enum):
    daily = "daily"
    weekly = "weekly"


# --- Request / Response models ---

class PlanRequest(BaseModel):
    weight_kg: float = Field(gt=0, description="Body weight in kilograms")
    height_cm: float = Field(gt=0, description="Height in centimeters")
    age: int = Field(gt=0, le=120, description="Age in years")
    sex: SexEnum
    goal: GoalEnum
    activity_level: ActivityEnum
    dietary_restrictions: list[str] = Field(default_factory=list)
    plan_duration: PlanDurationEnum = PlanDurationEnum.weekly


class CalorieInfo(BaseModel):
    bmr: float
    tdee: float
    bmi: float
    target: float


class PlanResponse(BaseModel):
    plan: str
    calories: CalorieInfo
    warning: Optional[str] = None


# --- App setup ---

app = FastAPI(
    title="FitBot API",
    description="RAG-based fitness and nutrition plan generator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Endpoints ---

@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/generate-plan", response_model=PlanResponse)
def create_plan(request: PlanRequest):
    # Step 1: Calculate calories
    try:
        calorie_result = calculate_calorie_target(
            weight_kg=request.weight_kg,
            height_cm=request.height_cm,
            age=request.age,
            sex=request.sex.value,
            activity_level=request.activity_level.value,
            goal=request.goal.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Step 2: Build profile for the RAG chain
    profile = {
        "weight_kg": request.weight_kg,
        "height_cm": request.height_cm,
        "age": request.age,
        "sex": request.sex.value,
        "goal": calorie_result["goal"],
        "activity_level": request.activity_level.value,
        "dietary_restrictions": ", ".join(request.dietary_restrictions) or "None",
        "plan_duration": request.plan_duration.value,
        "target_calories": calorie_result["target_calories"],
    }

    # Step 3: Generate plan via LLM
    try:
        plan_text = generate_plan(profile)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate plan: {str(e)}",
        )

    # Step 4: Build response
    return PlanResponse(
        plan=plan_text,
        calories=CalorieInfo(
            bmr=calorie_result["bmr"],
            tdee=calorie_result["tdee"],
            bmi=calorie_result["bmi"],
            target=calorie_result["target_calories"],
        ),
        warning=calorie_result["warning"],
    )

# --- Chat models ---

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    plan_context: str = ""
    chat_history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str


# --- Chat endpoint ---

@app.post("/chat", response_model=ChatResponse)
def chat_with_fitbot(request: ChatRequest):
    try:
        # Build conversation messages
        messages = [("system", SYSTEM_PROMPT)]

        # Add plan context as an initial assistant message
        if request.plan_context:
            messages.append((
                "assistant",
                f"Here is the plan I previously generated for you:\n\n{request.plan_context}"
            ))

        # Add chat history
        for msg in request.chat_history:
            if msg.role in ("user", "assistant"):
                messages.append((msg.role, msg.content))

        # Add current user message
        messages.append(("human", request.message))

        prompt = ChatPromptTemplate.from_messages(messages)
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, max_tokens=1000)
        chain = prompt | llm

        response = chain.invoke({})
        return ChatResponse(reply=response.content)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat error: {str(e)}",
        )