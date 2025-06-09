import io
import os
from typing import Optional

import docx
import fitz  # PyMuPDF
import modal
import google.generativeai as genai

app = modal.App(
    name="career-advisor-agent-gemini",
    image=modal.Image.debian_slim().pip_install(
        "google-generativeai",
        "pymupdf<1.24.0",
        "python-docx",
        "fastapi[standard]"
    ),
    secrets=[modal.Secret.from_name("my-google-secret")],
)

def parse_resume(file_content: bytes, filename: str) -> str:
    """Parses text from PDF or DOCX files."""
    text = ""
    try:
        if filename.lower().endswith(".pdf"):
            pdf_document = fitz.open(stream=file_content, filetype="pdf")
            for page in pdf_document:
                text += page.get_text()
            pdf_document.close()
        elif filename.lower().endswith(".docx"):
            doc = docx.Document(io.BytesIO(file_content))
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        print(f"Error parsing file {filename}: {e}")
        return f"Error parsing resume: {e}"
    return text


@app.function(timeout=120)
def get_career_advice(
    bio: str,
    interest: str,
    resume_text: Optional[str] = None,
):
    """The main agent function that queries the Gemini API."""
    try:
        # Configure the Gemini API client
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        
        # List available models to debug
        try:
            models = genai.list_models()
            print("Available models:", [model.name for model in models])
        except Exception as e:
            print(f"Could not list models: {e}")

        # Initialize the Generative Model with explicit model name
        model = genai.GenerativeModel(model_name='gemini-2.0-flash')
        
        prompt = f"""
        You are an expert career advisor and coach. Your goal is to provide clear, actionable, and visually structured career advice.
        Format your entire response in Markdown, making it highly visual and structured.

        Here is the user's profile:
        Primary Interest Area: {interest}
        Bio: {bio}
        Resume Content: {resume_text if resume_text else "No resume provided."}

        Important Instructions:
        1. Focus PRIMARILY on the user's chosen interest area ({interest}). All advice should be specifically tailored to this field.
        2. If a resume is provided, analyze their current skills and experience to provide more personalized recommendations.
        3. Ensure all recommendations, courses, and projects are SPECIFICALLY relevant to {interest}.
        4. Use the resume content to identify transferable skills that would be valuable in {interest}.

        Provide a structured response with the following sections:

        ### 💫 Quick Summary
        A brief 2-3 sentence overview focusing specifically on their potential in {interest}, highlighting relevant existing skills and clear next steps.

        ### 🎯 Recommended Roles
        Present 3 recommended roles IN THE {interest} FIELD ONLY in this format:
        1. **Role Name** (Match Score: X/10)
            - Salary Range: $XX,XXX - $XXX,XXX
            - Key Requirements: req1, req2, req3
            - Why It Fits: Brief explanation based on their background

        ### 📊 Skills Assessment
        Analyze their current skills relevant to {interest}. Use this format:
        ```skill-meter
        Current Skills Relevant to {interest}:
        Skill Name     [█████░░░░░] 50%
        ```
        Include 4-5 most relevant skills for {interest}, showing both strengths and areas for improvement.

        ### 📚 Learning Path
        Present a structured timeline SPECIFIC to {interest}:
        1. **Month 1-2: Foundation**
            - Course: "Course Name" (Platform) - Must be relevant to {interest}
            - Project: "Project idea" - Must be relevant to {interest}
            - Expected Outcome: "What they'll learn"

        ### 💡 Project Portfolio
        Present 3 project ideas AS CARDS that are SPECIFICALLY for {interest}:
        ```project-card
        Project: Name
        Difficulty: ⭐⭐⭐☆☆
        Duration: 2 weeks
        Skills: skill1, skill2
        Description: Brief description
        ```

        ### 🎓 Certifications
        List 2-3 recommended certifications SPECIFIC to {interest}:
        - Certificate Name (Provider)
        - Difficulty Level: ⭐⭐⭐☆☆
        - Time Commitment: X-Y months
        - Cost Range: $XXX (details)

        Remember to:
        - Keep ALL advice focused on {interest}
        - Use their resume/background to make recommendations more relevant
        - Be specific and actionable in all recommendations
        - Use proper formatting for visual elements (skill bars, project cards, diagram)
        """

        try:
            response = model.generate_content(prompt)
            if response and hasattr(response, 'text'):
                return response.text
            else:
                return "Error: Received empty or invalid response from Gemini API"
        except Exception as e:
            print(f"Generate content error: {str(e)}")
            return f"Error generating content: {str(e)}"
            
    except KeyError:
        return "Error: GOOGLE_API_KEY not found in environment variables"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"


# --- FIX 1: Use the new decorator name ---
@app.function()
@modal.fastapi_endpoint(method="POST")
def web_endpoint(data: dict):
    """
    This is the web endpoint that our Gradio app will call.
    """
    try:
        print("Received request with data:", data)
        bio = data.get("bio")
        interest = data.get("interest")
        resume_data = data.get("resume") 

        resume_text = None
        if resume_data:
            import base64
            file_content = base64.b64decode(resume_data["data"])
            resume_text = parse_resume(file_content, resume_data["name"])
            print("Parsed resume text length:", len(resume_text) if resume_text else 0)

        # Call the main agent function
        advice = get_career_advice.remote(bio, interest, resume_text)
        print("Generated advice length:", len(advice) if advice else 0)
        return {"advice": advice}
    except Exception as e:
        print(f"Error in web endpoint: {str(e)}")
        return {"advice": f"Error occurred in web endpoint: {str(e)}"}