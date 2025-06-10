---
title: AI Career Advisor
emoji: 🏆
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.33.0
app_file: app.py
pinned: true
license: mit
thumbnail: >-
  https://cdn-uploads.huggingface.co/production/uploads/66c0a274737c4ed8904e3581/C29bSp2Urwqws3wRzsBYT.png
short_description: '"An interactive AI Career Advisor powered by Gemini '
tags:
  - custom-component-track
---

# AI Career Advisor

Get personalized career advice, skill-gap analysis, and a learning roadmap from an AI agent powered by Gemini. This application uses Gradio for a user-friendly interface and Modal for serverless AI processing.

## Features
- Personalized career recommendations based on your profile
- Skill assessment with visual skill meters
- Recommended roles with match scores
- Customized learning path
- Project portfolio ideas
- Relevant certification recommendations

## How to use
1. Enter your bio or career goals
2. Select your primary area of interest
3. Optionally upload your resume (PDF or DOCX)
4. Get comprehensive career guidance

## How Gradio and Modal are Used

This project leverages both Gradio and Modal to deliver a seamless AI-powered career advisor experience:

- **Gradio** is used to build the interactive web interface (`app.py`). It provides an easy-to-use UI where users can enter their bio, select an interest area, and upload a resume. The interface displays personalized career advice, skill assessments, learning paths, project ideas, and certification recommendations in a visually appealing format.

- **Modal** is used to securely run the AI agent logic (`modal_agent_gemini.py`). When a user submits their information through the Gradio app, the data is sent to a Modal web endpoint. Modal handles the backend processing, including securely accessing the Gemini API (using secrets and environment variables), analyzing the user's profile and resume, and generating structured career advice. The results are then sent back to the Gradio UI for display.

This separation ensures that sensitive operations and API keys are kept secure on the backend, while users interact with a friendly and responsive web app on the frontend.