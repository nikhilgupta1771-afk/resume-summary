import reflex as rx
import pypdf
import io
from google import genai
from pydantic import BaseModel, Field
GREEN_LIGHT_BG = "#29E361"
# ==========================================
# 1. DEFINE THE AI OUTPUT BLUEPRINT
# ==========================================
class InterviewQuestion(BaseModel):
    question: str = Field(description="A highly specific technical question.")
    why_it_matters: str = Field(description="Why the interviewer is asking this.")
    suggested_answer_framework: str = Field(description="Bullet points for the answer.")

class TailoredResume(BaseModel):
    summary: str
    highlighted_skills: list[str]
    mock_interview: list[InterviewQuestion]

# ==========================================
# 2. STATE MANAGEMENT (BACKEND LOGIC)
# ==========================================
class AppState(rx.State):
    api_key: str = ""
    job_description: str = ""
    is_loading: bool = False
    error_message: str = ""
    
    summary: str = ""
    highlighted_skills: list[str] = []
    mock_interview: list[dict[str, str]] = [] 

    @rx.event
    def set_api_key(self, value: str):
        self.api_key = value

    @rx.event
    def set_job_description(self, value: str):
        self.job_description = value
    
    @rx.event
    async def process_data(self, files: list[rx.UploadFile]):
        if not self.api_key:
            self.error_message = "Please enter your Gemini API Key."
            return
        if not files or not self.job_description:
            self.error_message = "Please upload a resume and job description."
            return
            
        self.is_loading = True
        self.error_message = ""
        yield
        
        try:
            file_data = await files[0].read()
            reader = pypdf.PdfReader(io.BytesIO(file_data))
            resume_text = "".join(page.extract_text() for page in reader.pages)
            
            client = genai.Client(api_key=self.api_key)
            prompt = f"Resume:\n{resume_text}\n\nJob Description:\n{self.job_description}"
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': TailoredResume,
                },
            )
            
            result = response.parsed
            self.summary = result.summary
            self.highlighted_skills = result.highlighted_skills
            self.mock_interview = [q.model_dump() for q in result.mock_interview]
            
        except Exception as e:
            self.error_message = str(e)
        finally:
            self.is_loading = False
            yield

# ==========================================
# 3. USER INTERFACE
# ==========================================
def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("🚀 AI Resume Copilot", size="8", mb="2"),
            
            # API Key Input
            rx.input(
                placeholder="Enter Gemini API Key", 
                type="password", 
                on_change=AppState.set_api_key,
                width="100%", max_width="400px"
            ),
            
            # Main Grid
            rx.grid(
                rx.upload(
                    rx.vstack(
                        rx.icon("upload", size=40, color="gray"),
                        rx.text("Drag and drop PDF resume"),
                    ),
                    id="resume_upload", max_files=1, accept={"application/pdf": [".pdf"]},
                    border="2px dashed var(--gray-alpha-5)", width="100%"
                ),
                rx.text_area(
                    placeholder="Paste the target Job Description here...",
                    on_change=AppState.set_job_description,
                    height="100%", width="100%",
                ),
                columns="2", spacing="4", width="100%", mt="6"
            ),
            
            rx.button(
                "Generate Tailored Profile", 
                on_click=AppState.process_data(rx.upload_files(upload_id="resume_upload")),
                loading=AppState.is_loading,
                size="4", mt="6"
            ),
            
            # Error/Results
            rx.cond(AppState.error_message != "", rx.callout(AppState.error_message, color_scheme="red")),
            
            rx.cond(
                AppState.summary != "",
                rx.vstack(
                    rx.heading("📝 Tailored Summary", size="6"),
                    rx.text(AppState.summary),
                    rx.heading("🎯 Skills", size="6"),
                    rx.flex(
                        rx.foreach(AppState.highlighted_skills, lambda skill: rx.badge(skill, m="1")),
                        wrap="wrap"
                    ),
                    width="100%"
                )
            ),
            width="100%", max_width="900px", padding="2em",
            background_color=GREEN_LIGHT_BG,
            border_radius="12px",
            box_shadow="0 4px 12px rgba(6, 78, 59, 0.08)", 
            border=f"1px solid rgba(16, 185, 129, 0.2)"
        )
    )

app = rx.App()
app.add_page(index)