import gradio as gr
import requests
import base64
import time
import re

# --- IMPORTANT ---
# Paste the web endpoint URL you got from deploying the Modal app here.
MODAL_WEB_ENDPOINT_URL = "https://aryanjathar0723--career-advisor-agent-gemini-web-endpoint.modal.run"

if MODAL_WEB_ENDPOINT_URL.startswith("https://your-org"):
    print("="*80)
    print("!!! WARNING: You have not replaced the placeholder MODAL_WEB_ENDPOINT_URL. !!!")
    print("!!! Please deploy the modal_agent.py script and paste the URL in app.py.  !!!")
    print("="*80)

def extract_sections(markdown_text):
    """Extract different sections from the markdown response"""
    sections = {
        'summary': '',
        'roles': '',
        'skills': '',
        'learning': '',
        'projects': '',
        'certifications': ''
    }
    
    current_section = None
    current_content = []
    
    for line in markdown_text.split('\n'):
        if line.startswith('### 💫'):
            current_section = 'summary'
            current_content = []
        elif line.startswith('### 🎯'):
            current_section = 'roles'
            current_content = []
        elif line.startswith('### 📊'):
            current_section = 'skills'
            current_content = []
        elif line.startswith('### 📚'):
            current_section = 'learning'
            current_content = []
        elif line.startswith('### 💡'):
            current_section = 'projects'
            current_content = []
        elif line.startswith('### 🎓'):
            current_section = 'certifications'
            current_content = []
        # Skip roadmap section
        elif line.startswith('### 🗺️'):
            current_section = None
            current_content = []
        elif current_section:
            current_content.append(line)
            sections[current_section] = '\n'.join(current_content)
    
    return sections

def format_skill_bars(text):
    """Convert skill meter text to HTML progress bars"""
    formatted = []
    in_skill_meter = False
    for line in text.split('\n'):
        if '```skill-meter' in line:
            in_skill_meter = True
            formatted.append('<div class="skill-bars">')
            continue
        elif '```' in line and in_skill_meter:
            in_skill_meter = False
            formatted.append('</div>')
            continue
        
        if in_skill_meter and '[' in line and ']' in line:
            try:
                skill_name, rest = line.split('[')
                percentage = re.search(r'(\d+)%', rest)
                if percentage:
                    pct = int(percentage.group(1))
                    formatted.append(f'''
                    <div class="skill-bar">
                        <div class="skill-name">{skill_name.strip()}</div>
                        <div class="progress-bar">
                            <div class="progress" style="width: {pct}%; background-color: #3498db;"></div>
                        </div>
                        <div class="percentage">{pct}%</div>
                    </div>
                    ''')
            except:
                formatted.append(line)
        else:
            formatted.append(line)
    
    return '\n'.join(formatted)

def format_project_cards(text):
    """Convert project-card text to HTML cards"""
    formatted = []
    in_project_card = False
    current_card = {}
    
    for line in text.split('\n'):
        if '```project-card' in line:
            in_project_card = True
            current_card = {}
            continue
        elif '```' in line and in_project_card:
            in_project_card = False
            if current_card:
                card_html = f'''
                <div class="project-card">
                    <div>{current_card.get('project', 'Project')}</div>
                    <div><strong>Difficulty:</strong> {current_card.get('difficulty', '⭐⭐⭐')}</div>
                    <div><strong>Duration:</strong> {current_card.get('duration', '2 weeks')}</div>
                    <div><strong>Skills:</strong> {current_card.get('skills', 'Various skills')}</div>
                    <div><strong>Description:</strong> {current_card.get('description', 'Project description')}</div>
                </div>
                '''
                formatted.append(card_html)
            continue
        
        if in_project_card:
            line = line.strip()
            if line.startswith('Project:'):
                current_card['project'] = line[len('Project:'):].strip()
            elif line.startswith('Difficulty:'):
                current_card['difficulty'] = line[len('Difficulty:'):].strip()
            elif line.startswith('Duration:'):
                current_card['duration'] = line[len('Duration:'):].strip()
            elif line.startswith('Skills:'):
                current_card['skills'] = line[len('Skills:'):].strip()
            elif line.startswith('Description:'):
                current_card['description'] = line[len('Description:'):].strip()
        else:
            formatted.append(line)
    
    return '\n'.join(formatted)

def format_roles(content):
    """Format roles as cards"""
    formatted_content = []
    current_role = []
    in_role = False
    
    for line in content.split('\n'):
        if line.strip().startswith('1.') or line.strip().startswith('2.') or line.strip().startswith('3.'):
            if in_role:
                formatted_content.append(format_role_card(current_role))
            in_role = True
            current_role = [line]
        elif in_role and line.strip():
            current_role.append(line)
    
    if current_role:
        formatted_content.append(format_role_card(current_role))
    
    return '\n'.join(formatted_content)

def format_role_card(role_lines):
    """Helper function to format role card"""
    role_title = role_lines[0].strip()
    # Extract role name and match score
    role_name = ""
    match_score = ""
    if "**" in role_title:
        parts = role_title.split("**")
        if len(parts) > 1:
            role_name = parts[1].strip()
            if "(Match Score:" in role_title:
                match_parts = role_title.split("(Match Score:")
                if len(match_parts) > 1:
                    match_score = match_parts[1].split(")")[0].strip()
    
    card_html = f'''
    <div class="role-card">
        <div class="role-title">{role_name} (Match Score: {match_score})</div>
    '''
    
    for line in role_lines[1:]:
        line = line.strip()
        if line.startswith('-'):
            detail = line[1:].strip()
            if "Salary Range:" in detail:
                card_html += f'<div class="role-detail"><strong>Salary Range:</strong> {detail.split("Salary Range:")[1].strip()}</div>'
            elif "Key Requirements:" in detail:
                card_html += f'<div class="role-detail"><strong>Key Requirements:</strong> {detail.split("Key Requirements:")[1].strip()}</div>'
            elif "Why It Fits:" in detail:
                card_html += f'<div class="role-detail"><strong>Why It Fits:</strong> {detail.split("Why It Fits:")[1].strip()}</div>'
            else:
                card_html += f'<div class="role-detail">{detail}</div>'
    
    card_html += '</div>'
    return card_html

def format_certification_card(cert_lines):
    """Helper function to format certification card"""
    cert_name = cert_lines[0].replace('*', '').strip()
    card_html = f'''
    <div class="cert-card">
        <div class="cert-name">{cert_name}</div>
    '''
    
    for line in cert_lines[1:]:
        if line.strip():
            line = line.strip().strip('*').strip('-').strip()
            if "difficulty level:" in line.lower():
                stars = line.split(":", 1)[1].strip() if ":" in line else ""
                card_html += f'<div class="cert-detail">- Difficulty Level: {stars}</div>'
            elif "time commitment:" in line.lower():
                time = line.split(":", 1)[1].strip() if ":" in line else ""
                card_html += f'<div class="cert-detail">- Time Commitment: {time}</div>'
            elif "cost range:" in line.lower():
                cost = line.split(":", 1)[1].strip() if ":" in line else ""
                card_html += f'<div class="cert-detail">- Cost Range: {cost}</div>'
            else:
                card_html += f'<div class="cert-detail">• {line}</div>'
    
    card_html += '</div>'
    return card_html

def parse_certifications(content):
    """Parse certification content to group details by certification"""
    lines = content.split('\n')
    cert_groups = []
    current_cert = []
    
    # Check if content follows the format from the screenshot with dashes
    has_cert_headers = any(line.strip().startswith('- ') for line in lines)
    
    if has_cert_headers:
        cert_name = ""
        cert_details = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('- ') and not any(detail in line.lower() for detail in ['difficulty level', 'time commitment', 'cost range']):
                # This is a new certificate name
                if cert_name:
                    # Save the previous certificate
                    cert_groups.append([f"* {cert_name}"] + cert_details)
                
                cert_name = line[2:].strip()
                cert_details = []
            elif line.startswith('- '):
                # This is a detail for the current certificate
                cert_details.append(line)
        
        # Add the last certificate
        if cert_name:
            cert_groups.append([f"* {cert_name}"] + cert_details)
    else:
        # Fall back to original parsing
        in_cert = False
        for line in lines:
            if line.strip().startswith('*'):
                if in_cert and current_cert:
                    cert_groups.append(current_cert)
                in_cert = True
                current_cert = [line]
            elif in_cert and line.strip():
                current_cert.append(line)
        
        if current_cert:
            cert_groups.append(current_cert)
    
    return cert_groups

def format_sections(sections):
    """Format all sections with proper styling"""
    css = """
    <style>
    :root {
        --bg-color: #1a1b26;
        --text-color: #a9b1d6;
        --heading-color: #7aa2f7;
        --card-bg: #24283b;
        --card-border: #414868;
        --highlight: #bb9af7;
        --progress-bg: #414868;
        --progress-fill: linear-gradient(90deg, #7aa2f7, #bb9af7);
        --card-hover: #2f3549;
    }

    body {
        font-size: 16px;
        line-height: 1.6;
        background-color: var(--bg-color);
        color: var(--text-color);
    }

    .skill-bars {
        font-family: monospace;
        margin: 25px 0;
        font-size: 1.1em;
        background-color: var(--card-bg);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid var(--card-border);
    }

    .skill-bar {
        display: flex;
        align-items: center;
        margin: 15px 0;
        gap: 15px;
    }

    .skill-name {
        width: 180px;
        text-align: right;
        font-size: 1.1em;
        color: var(--heading-color);
    }

    .progress-bar {
        flex-grow: 1;
        height: 25px;
        background-color: var(--progress-bg);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);
    }

    .progress {
        height: 100%;
        border-radius: 12px;
        transition: width 0.5s ease-in-out;
        background: var(--progress-fill);
    }

    .percentage {
        width: 60px;
        font-size: 1.1em;
        font-weight: 500;
        color: var(--text-color);
    }

    .project-card {
        border: 1px solid var(--card-border);
        padding: 25px;
        margin: 20px 0;
        border-radius: 12px;
        background-color: var(--card-bg);
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        font-size: 1.1em;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .project-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }

    .project-card div {
        margin: 10px 0;
        line-height: 1.6;
    }

    .project-card strong {
        color: var(--heading-color);
        margin-right: 10px;
        font-weight: 600;
    }

    .project-card div:first-child {
        font-size: 1.2em;
        color: var(--highlight);
        margin-bottom: 15px;
        font-weight: 500;
    }

    h3 {
        font-size: 1.5em;
        margin: 1.5em 0 1em;
        color: var(--heading-color);
        border-bottom: 2px solid var(--card-border);
        padding-bottom: 0.5em;
    }

    p {
        font-size: 1.1em;
        line-height: 1.6;
        color: var(--text-color);
        margin: 1em 0;
    }

    ul, ol {
        font-size: 1.1em;
        line-height: 1.6;
        padding-left: 1.5em;
        margin: 1em 0;
    }

    li {
        margin: 0.8em 0;
        padding-left: 0.5em;
    }

    strong {
        color: var(--highlight);
    }

    .role-card {
        background-color: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
    }

    .role-title {
        color: var(--highlight);
        font-size: 1.2em;
        margin-bottom: 10px;
    }

    .role-detail {
        margin: 8px 0;
        color: var(--text-color);
    }

    .bullet-point {
        margin: 10px 0;
        padding-left: 20px;
        position: relative;
        color: var(--text-color);
    }

    .bullet-point:before {
        content: "•";
        color: var(--highlight);
        position: absolute;
        left: 0;
        font-size: 1.2em;
    }

    .content-line {
        margin: 10px 0;
        padding: 5px 0;
        color: var(--text-color);
    }

    .content-line strong {
        color: var(--highlight);
        font-weight: 600;
    }

    .expandable-card {
        border: 1px solid var(--card-border);
        border-radius: 12px;
        background-color: var(--card-bg);
        margin: 15px 0;
        overflow: hidden;
        transition: all 0.3s ease;
    }

    .expandable-card .card-header {
        padding: 15px 20px;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid var(--card-border);
    }

    .expandable-card .card-header:hover {
        background-color: var(--card-hover);
    }

    .expandable-card .card-title {
        color: var(--highlight);
        font-size: 1.2em;
        font-weight: 500;
    }

    .expandable-card .card-content {
        padding: 20px;
        display: none;
    }

    .expandable-card.expanded .card-content {
        display: block;
    }

    .learning-card {
        border: 1px solid var(--card-border);
        border-radius: 12px;
        background-color: var(--card-bg);
        padding: 20px;
        margin: 15px 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .learning-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }

    .learning-card .month-range {
        color: var(--highlight);
        font-size: 1.2em;
        margin-bottom: 10px;
        font-weight: 500;
    }

    .learning-card .course-name {
        color: var(--heading-color);
        margin: 10px 0;
    }

    .learning-card .project-name {
        color: var(--text-color);
        margin: 10px 0;
    }

    .learning-card .outcome {
        color: var(--text-color);
        font-style: italic;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid var(--card-border);
    }

    .cert-card {
        border: 1px solid var(--card-border);
        border-radius: 12px;
        background-color: var(--card-bg);
        padding: 20px;
        margin: 15px 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .cert-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }

    .cert-card .cert-name {
        color: var(--highlight);
        font-size: 1.2em;
        margin-bottom: 10px;
        font-weight: 500;
    }

    .cert-card .cert-detail {
        color: var(--text-color);
        margin: 8px 0;
    }
    </style>

    <script>
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('.expandable-card .card-header').forEach(header => {
            header.addEventListener('click', () => {
                const card = header.parentElement;
                card.classList.toggle('expanded');
            });
        });
    });
    </script>
    """
    
    formatted = {}
    for key, content in sections.items():
        if key == 'skills':
            formatted[key] = css + format_skill_bars(content)
        elif key == 'summary':
            # Format summary as an expandable card
            lines = content.split('\n')
            formatted_content = ['<div class="expandable-card expanded">']
            formatted_content.append('<div class="card-header">')
            formatted_content.append('<div class="card-title">Quick Summary</div>')
            formatted_content.append('<div class="expand-icon">▼</div>')
            formatted_content.append('</div>')
            formatted_content.append('<div class="card-content">')
            for line in lines:
                if line.strip():
                    formatted_content.append(f'<div class="content-line">{line}</div>')
            formatted_content.append('</div>')
            formatted_content.append('</div>')
            formatted[key] = '\n'.join(formatted_content)
        elif key == 'roles':
            # Format roles as cards
            formatted[key] = css + format_roles(content)
        elif key == 'projects':
            # Format projects as cards
            formatted[key] = css + format_project_cards(content)
        elif key == 'learning':
            # Format learning path as cards
            formatted_content = []
            current_month = []
            in_month = False
            
            for line in content.split('\n'):
                if line.strip().startswith('1.') or line.strip().startswith('2.') or line.strip().startswith('3.'):
                    if in_month:
                        card_content = '\n'.join(current_month)
                        month_range = current_month[0].split(':')[0].replace('*', '').strip()
                        card_html = f'''
                        <div class="learning-card">
                            <div class="month-range">{month_range}</div>
                            {format_learning_content(card_content)}
                        </div>
                        '''
                        formatted_content.append(card_html)
                    in_month = True
                    current_month = [line]
                elif in_month:
                    current_month.append(line)
            
            if current_month:
                card_content = '\n'.join(current_month)
                month_range = current_month[0].split(':')[0].replace('*', '').strip()
                card_html = f'''
                <div class="learning-card">
                    <div class="month-range">{month_range}</div>
                    {format_learning_content(card_content)}
                </div>
                '''
                formatted_content.append(card_html)
            
            formatted[key] = css + '\n'.join(formatted_content)
        elif key == 'certifications':
            # Format certifications as cards
            formatted_content = []
            
            # Parse certifications into groups
            cert_groups = parse_certifications(content)
            
            for cert_group in cert_groups:
                formatted_content.append(format_certification_card(cert_group))
            
            if not formatted_content:
                # If no certifications were found, add a placeholder
                formatted_content.append('<div class="cert-card"><div class="cert-name">No certifications found</div></div>')
            
            formatted[key] = css + '\n'.join(formatted_content)
        else:
            formatted[key] = content
    
    return formatted

def format_learning_content(content):
    """Helper function to format learning card content"""
    formatted = []
    for line in content.split('\n'):
        line = line.strip()
        if 'Course:' in line:
            course = line.split('Course:')[1].strip().strip('"')
            formatted.append(f'<div class="course-name">📚 Course: {course}</div>')
        elif 'Project:' in line:
            project = line.split('Project:')[1].strip().strip('"')
            formatted.append(f'<div class="project-name">💻 Project: {project}</div>')
        elif 'Expected Outcome:' in line:
            outcome = line.split('Expected Outcome:')[1].strip().strip('"')
            formatted.append(f'<div class="outcome">🎯 Expected Outcome: {outcome}</div>')
    return '\n'.join(formatted)

def get_advice_from_agent(bio, interest, resume_file):
    """
    This function prepares the data and calls the Modal backend.
    """
    if not bio or not interest:
        sections = {
            "summary": "Please provide your bio/goals and select an interest area.",
            "roles": "", "skills": "", "learning": "",
            "projects": "", "certifications": ""
        }
        formatted = format_sections(sections)
        return [
            formatted["summary"],
            formatted["roles"],
            formatted["skills"],
            formatted["learning"],
            formatted["projects"],
            formatted["certifications"]
        ]

    # Show a thinking message immediately
    sections = {
        "summary": "🤔 Agent is thinking... Parsing your profile and crafting a response. This may take a moment.",
        "roles": "", "skills": "", "learning": "",
        "projects": "", "certifications": ""
    }
    formatted = format_sections(sections)
    yield [
        formatted["summary"],
        formatted["roles"],
        formatted["skills"],
        formatted["learning"],
        formatted["projects"],
        formatted["certifications"]
    ]

    payload = {
        "bio": bio,
        "interest": interest,
    }

    # Handle the optional resume file
    if resume_file is not None:
        with open(resume_file.name, "rb") as f:
            file_content = f.read()
        encoded_file = base64.b64encode(file_content).decode("utf-8")
        payload["resume"] = {
            "name": resume_file.name,
            "data": encoded_file
        }

    try:
        print("Making request to Modal endpoint...")
        response = requests.post(MODAL_WEB_ENDPOINT_URL, json=payload, timeout=120)
        print(f"Response status code: {response.status_code}")
        response.raise_for_status()
        
        result = response.json()
        print("Raw response from Modal:", result)
        
        advice_text = result.get("advice", "")
        print("Advice text:", advice_text[:200] + "..." if advice_text else "No advice text")
        
        sections = extract_sections(advice_text)
        print("Extracted sections:", sections.keys())
        
        # Format sections with proper styling
        formatted = format_sections(sections)
        
        output = [
            formatted["summary"],
            formatted["roles"],
            formatted["skills"],
            formatted["learning"],
            formatted["projects"],
            formatted["certifications"]
        ]
        print("Returning output with lengths:", [len(str(x)) for x in output])
        yield output

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        error_sections = {
            "summary": f"An error occurred: {str(e)}",
            "roles": "Error occurred", 
            "skills": "Error occurred", 
            "learning": "Error occurred",
            "projects": "Error occurred", 
            "certifications": "Error occurred"
        }
        formatted = format_sections(error_sections)
        yield [
            formatted["summary"],
            formatted["roles"],
            formatted["skills"],
            formatted["learning"],
            formatted["projects"],
            formatted["certifications"]
        ]

# Define the Gradio UI using Blocks for custom layout
with gr.Blocks(theme=gr.themes.Soft(), title="AI Career Advisor") as demo:
    gr.Markdown(
        """
        # 🎯 AI Career Advisor
        Get personalized career advice, skill-gap analysis, and a learning roadmap from an AI agent.
        """
    )

    with gr.Row():
        # Left column for input
        with gr.Column(scale=1):
            gr.Markdown("### 📝 Your Profile")
            user_bio = gr.Textbox(
                label="Your Bio or Goal",
                placeholder="e.g., I'm a 3rd-year IT student interested in Machine Learning and want to become an ML Engineer.",
                lines=4
            )
            interest_area = gr.Dropdown(
                label="Primary Area of Interest",
                choices=["AI / Data Science", "Web Development", "Cybersecurity", 
                        "Cloud Computing", "DevOps", "Game Development"]
            )
            resume_upload = gr.File(
                label="Upload Resume (PDF or DOCX)",
                file_types=[".pdf", ".docx"]
            )
            submit_btn = gr.Button("Get Career Advice", variant="primary")

        # Right column for output
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab("📊 Overview"):
                    summary_md = gr.HTML()
                    roles_md = gr.HTML()
                
                with gr.Tab("🎯 Skills & Learning"):
                    skills_md = gr.HTML()
                    learning_md = gr.HTML()
                
                with gr.Tab("💡 Projects"):
                    projects_md = gr.HTML()
                
                with gr.Tab("🎓 Certifications"):
                    cert_md = gr.HTML()

    submit_btn.click(
        fn=get_advice_from_agent,
        inputs=[user_bio, interest_area, resume_upload],
        outputs=[summary_md, roles_md, skills_md, learning_md, projects_md, cert_md]
    )

    gr.Examples(
        examples=[
            ["I am a software developer with 5 years of experience in Java, and I want to transition into a DevOps role.", "DevOps", None],
            ["I'm a final year marketing student fascinated by data. I know some basic Python and SQL and want a career that blends marketing with data analytics.", "AI / Data Science", None],
        ],
        inputs=[user_bio, interest_area, resume_upload]
    )

if __name__ == "__main__":
    demo.launch()