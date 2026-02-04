import asyncio, json, queue, websockets
from app.extensions import socketio
from app.config import Config
from app.services.meeting_service import append_transcript

# XÓA: sessions = {}, session_transcripts = {} 
# (Giữ lại session_dict nếu cần quản lý queue worker riêng biệt, 
# nhưng ở đây ta chỉ cần lưu DB nên bỏ bớt cho sạch)

async def sm_worker(sid, audio_queue):
    headers = {"Authorization": f"Bearer {Config.SPEECHMATICS_API_KEY}"}
    final_buffer = ""

    async with websockets.connect(Config.SM_URL, extra_headers=headers) as ws:
        await ws.send(json.dumps({
            "message": "StartRecognition",
            "audio_format": {
                "type": "raw",
                "encoding": "pcm_s16le",
                "sample_rate": 16000
            },
            "transcription_config": {
                "language": "vi",
                "enable_partials": True,
                "max_delay": 3,
                "diarization": "speaker"
            }
        }))

        async def receive_loop():
            nonlocal final_buffer
            async for raw in ws:
                msg = json.loads(raw)
                msg_type = msg.get("message")

                if msg_type == "AddPartialTranscript":
                    text = msg.get("metadata", {}).get("transcript", "").strip()
                    if text:
                        socketio.emit("transcript_response",
                                      {"text": text, "is_final": False},
                                      room=sid)

                elif msg_type == "AddTranscript":
                    text = msg.get("metadata", {}).get("transcript", "").strip()
                    results = msg.get("results", [])

                    speaker = "Unknown"
                    if results and results[0].get("alternatives"):
                        speaker = results[0]["alternatives"][0].get("speaker", "Unknown")

                    if text:
                        final_buffer += (" " if final_buffer else "") + text

                    for r in results:
                        if r.get("type") == "punctuation" and r.get("is_eos"):
                            sentence = final_buffer.strip()
                            final_buffer = ""
                            if sentence:
                                line = f"Người {speaker}: {sentence}"
                                
                                # Gửi UI
                                socketio.emit("transcript_response",
                                              {"speaker": f"Người {speaker}",
                                               "text": sentence,
                                               "is_final": True},
                                              room=sid)
                                
                                # LƯU VÀO DATABASE (Mới thêm)
                                append_transcript(sid, line)

        recv_task = asyncio.create_task(receive_loop())

        loop = asyncio.get_running_loop()
        while True:
            chunk = await loop.run_in_executor(None, audio_queue.get)
            if chunk is None:
                await ws.close()
                break
            await ws.send(chunk)

        await recv_task