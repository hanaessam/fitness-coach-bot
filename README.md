---
title: FitBot - Fitness Coach Bot
emoji: 🏋️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# FitBot - Your Personal Fitness Coach

A RAG-based fitness and nutrition chatbot that generates personalized workout
and meal plans based on your body metrics, goals, and dietary preferences.

## Features

- Personalized calorie calculations using the Mifflin-St Jeor equation
- RAG-powered exercise and nutrition recommendations from real datasets
- Safety checks: 1200 kcal floor, BMI-aware goal validation, ED awareness
- Interactive chat to ask follow-up questions about your plan
- Six fitness goals: lose, aggressive lose, maintain, recomp, lean bulk, bulk

## How to Use

1. Enter your body metrics in the sidebar (weight, height, age, sex)
2. Select your fitness goal, activity level, and dietary restrictions
3. Click "Generate My Plan"
4. Review your calorie summary, workout plan, and meal plan
5. Use the chat to ask follow-up questions or request modifications

## Architecture
```
User (Browser)
     |
     v
Streamlit UI (port 7860)
     |
     v
FastAPI Backend (port 8000)
     |
     +---> Calorie Calculator (Mifflin-St Jeor + safety checks)
     |
     +---> RAG Chain (LangChain LCEL)
              |
              +---> ChromaDB (exercises collection)
              +---> ChromaDB (nutrients collection)
              +---> OpenAI GPT-4o-mini
```

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **LLM**: OpenAI GPT-4o-mini
- **Embeddings**: OpenAI text-embedding-ada-002
- **Vector Store**: ChromaDB
- **Orchestration**: LangChain (LCEL)
- **Deployment**: Hugging Face Spaces (Docker)

## Datasets

- [Gym Exercise Data](https://www.kaggle.com/datasets/niharika41298/gym-exercise-data) by Niharika
- [Nutritional Values for Common Foods](https://www.kaggle.com/datasets/trolukovich/nutritional-values-for-common-foods-and-products) by Trolukovich

## Safety

FitBot enforces the following safety rules:
- Minimum 1200 kcal/day floor
- Blocks aggressive deficits for normal/underweight BMI users
- Refuses to diagnose injuries or medical conditions
- Always recommends consulting a healthcare professional
- Provides eating disorder helpline information when appropriate