from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
import io

env = Environment(loader=FileSystemLoader("app/templates"))

def build_resume_pdf(candidate: dict) -> io.BytesIO:
    template = env.get_template("resume_template.html")
    html_content = template.render(
        name=f"{candidate['basicInfo'].get('firstName', '')} {candidate['basicInfo'].get('lastName', '')}",
        email=candidate['basicInfo'].get('email', ''),
        role=candidate['basicInfo'].get('role', ''),
        description=candidate['basicInfo'].get('description', ''),
        education=candidate.get('education', []),
        skills=candidate.get('skills', []),
        projects=candidate.get('projects', []),
        awards=candidate.get('awards', []),
    )

    pdf_buffer = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer
