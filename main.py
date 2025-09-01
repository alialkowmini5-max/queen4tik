import os, uuid, shutil, subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

# إخفاء الوثائق الافتراضية
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

BASE = Path(__file__).resolve().parent
WORK = BASE / "work"
WORK.mkdir(exist_ok=True)

# الصفحة الرئيسية: يقرأ index.html من نفس المجلد
@app.get("/", response_class=HTMLResponse)
def home():
    html_path = BASE / "index.html"
    if not html_path.exists():
        return HTMLResponse("<h1>index.html غير موجود</h1>", status_code=500)
    return html_path.read_text(encoding="utf-8")

def run_silent(cmd: list[str]) -> bool:
    # تشغيل الأمر بصمت وإرجاع True/False فقط
    try:
        p = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=False
        )
        return p.returncode == 0
    except Exception:
        return False

@app.post("/process")
def process(file: UploadFile = File(...)):
    # حفظ الملف الوارد مؤقتًا
    uid = uuid.uuid4().hex
    in_path  = WORK / f"in_{uid}.mp4"
    out_path = WORK / f"out_{uid}.mp4"

    try:
        with open(in_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # معالجة الفيديو (التفاصيل مخفية ولا تُعاد للمستخدم)
        ok = run_silent([
            "ffmpeg", "-y",
            "-itsscale", "2",
            "-i", str(in_path),
            "-c:v", "copy",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(out_path)
        ])

        if not ok or not out_path.exists():
            # رسالة عامة فقط بدون أي تفاصيل
            return JSONResponse({"error": "تعذر إتمام المعالجة، حاول مجددًا."}, status_code=500)

        # إعادة الملف الناتج للتنزيل
        headers = {"Content-Disposition": 'attachment; filename="output.mp4"'}
        return FileResponse(str(out_path), media_type="video/mp4", headers=headers)

    finally:
        # تنظيف الإدخال دائمًا
        try: os.remove(in_path)
        except: pass
        # ملاحظة: بإمكانك تنظيف ملفات الإخراج لاحقًا عبر مهمة مجدولة إذا رغبت
