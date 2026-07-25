from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

templates_dir = Path(__file__).resolve().parent / "app" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

scope = {
    "type": "http",
    "method": "GET",
    "path": "/",
    "headers": [],
}
req = Request(scope)

try:
    print("Trying positional: (req, 'index.html', context)")
    resp = templates.TemplateResponse(req, "index.html", {"title": "TestPilot AI - Home"})
    print("Positional succeeded!")
except Exception as e:
    import traceback
    traceback.print_exc()

try:
    print("\nTrying keyword: (request=req, name='index.html', context=context)")
    resp = templates.TemplateResponse(request=req, name="index.html", context={"title": "TestPilot AI - Home"})
    print("Keyword succeeded!")
except Exception as e:
    import traceback
    traceback.print_exc()

try:
    print("\nTrying old: ('index.html', {'request': req, 'title': 'Home'})")
    resp = templates.TemplateResponse("index.html", {"request": req, "title": "TestPilot AI - Home"})
    print("Old signature succeeded!")
except Exception as e:
    import traceback
    traceback.print_exc()
