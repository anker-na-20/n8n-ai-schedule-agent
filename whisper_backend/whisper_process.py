import os
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
import whisper

app = FastAPI(title="Voice to Text Service for AI Agent")

# Инициализируем модель Whisper при старте. 
# Для Mac отлично подходит 'base' или 'small' — они быстрые и точные для русского языка.
print("📥 Загрузка модели Whisper (может занять некоторое время при первом запуске)...")
model = whisper.load_model("base")
print("✅ Модель Whisper успешно загружена и готова к работе!")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    # Проверяем расширение файла
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in [".ogg", ".mp3", ".wav", ".m4a", ".oga"]:
        raise HTTPException(status_code=400, detail="Неподдерживаемый формат аудио")

    # Временный файл для сохранения входящего аудио
    temp_file_path = Path(f"temp_{file.filename}")
    
    try:
        # Сохраняем файл на диск
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Запускаем распознавание речи
        print(f"🎙 Распознаю файл: {file.filename}...")
        result = model.transcribe(str(temp_file_path), language="ru")
        text = result.get("text", "").strip()
        print(f"📝 Результат: {text}")
        
        return {"text": text}
        
    except Exception as e:
        print(f"❌ Ошибка при распознавании: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Обязательно удаляем временный файл
        if temp_file_path.exists():
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
