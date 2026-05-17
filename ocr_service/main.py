import base64
import io
import cv2
import numpy as np
import pytesseract
from PIL import Image
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langdetect import detect, LangDetectException

app = FastAPI(title="DocMind OCR Service")

LANG_MAP = {"si": "sin", "ta": "tam", "en": "eng"}
DEFAULT_LANG = "sin+tam+eng"


def preprocess(pil_img: Image.Image) -> np.ndarray:
    img = np.array(pil_img.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.fastNlMeansDenoising(thresh, h=10)


def detect_language(text: str) -> str:
    if len(text.strip()) < 20:
        return DEFAULT_LANG
    try:
        lang = detect(text)
        return LANG_MAP.get(lang, DEFAULT_LANG)
    except LangDetectException:
        return DEFAULT_LANG


class OCRRequest(BaseModel):
    image_b64: str
    lang: str = DEFAULT_LANG


class LangRequest(BaseModel):
    text: str


@app.post("/ocr/image")
def ocr_image(req: OCRRequest):
    try:
        img_bytes = base64.b64decode(req.image_b64)
        pil_img = Image.open(io.BytesIO(img_bytes))
        processed = preprocess(pil_img)
        processed_pil = Image.fromarray(processed)
        text = pytesseract.image_to_string(
            processed_pil, lang=req.lang, config="--psm 6 --oem 3"
        ).strip()
        language = detect_language(text[:500]) if text else DEFAULT_LANG
        return {"text": text, "language": language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ocr/detect-lang")
def detect_lang_endpoint(req: LangRequest):
    return {"language": detect_language(req.text)}


@app.get("/health")
def health():
    return {"status": "ok"}