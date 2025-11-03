from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from gamelogic import MillionaireGame

app = FastAPI(title="Millionaire Game")
app.mount("/static", StaticFiles(directory="static"), name="static")
    
game_sessions = {}

class StartGameRequest(BaseModel):
    session_id: str
class AnswerRequest(BaseModel):
    session_id: str
    answer: int  
class SupportRequest(BaseModel):
    session_id: str
    support_type: str  # "fifty_fifty", "change_question", "ai_support"

@app.get("/", response_class=HTMLResponse)
async def root():
    with open('templates/home.html', 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/game-ai-la-trieu-phu", response_class=HTMLResponse)
async def game_page():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/api/start")
async def start_game(request: StartGameRequest):
    session_id = request.session_id
    game = MillionaireGame()
    game.start_game()
    game_sessions[session_id] = game
    
    state = game.get_current_state()
    
    return {
        "status": "success",
        "level": state['level'],
        "question": {
            "question": state['question'],
            "answer1": state['answers'][1],
            "answer2": state['answers'][2],
            "answer3": state['answers'][3],
            "answer4": state['answers'][4],
        },
        "supports": state['supports']
    }

@app.post("/api/answer")
async def check_answer(request: AnswerRequest):
    session_id = request.session_id
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    game = game_sessions[session_id]
    result = game.check_answer(request.answer)
    
    if result['status'] == 'won':
        return {
            "status": "won",
            "message": result['message'],
            "correct": True,
            "correct_answer": result['correct_answer']
        }
    elif result['status'] == 'correct':
        state = result['new_state']
        return {
            "status": "correct",
            "correct": True,
            "correct_answer": result['correct_answer'],
            "level": state['level'],
            "question": {
                "question": state['question'],
                "answer1": state['answers'][1],
                "answer2": state['answers'][2],
                "answer3": state['answers'][3],
                "answer4": state['answers'][4],
            },
            "supports": state['supports']
        }
    else:  # game_over
        return {
            "status": "game_over",
            "message": result['message'],
            "correct": False,
            "correct_answer": result['correct_answer'],
            "explanation": result['explanation']
        }

@app.post("/api/support")
async def use_support(request: SupportRequest):
    session_id = request.session_id
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    game = game_sessions[session_id]
    support_type = request.support_type
    
    if support_type == "fifty_fifty":
        result = game.use_fifty_fifty()
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        
        state = game.get_current_state()
        return {
            "status": "success",
            "support_type": "fifty_fifty",
            "removed_answers": result['removed_answers'],
            "supports": state['supports']
        }
    
    elif support_type == "change_question":
        result = game.use_change_question()
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        
        state = result['new_state']
        return {
            "status": "success",
            "support_type": "change_question",
            "level": state['level'],
            "question": {
                "question": state['question'],
                "answer1": state['answers'][1],
                "answer2": state['answers'][2],
                "answer3": state['answers'][3],
                "answer4": state['answers'][4],
            },
            "supports": state['supports']
        }
    
    elif support_type == "ai_support":
        result = game.use_ai_support()
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        
        state = game.get_current_state()
        return {
            "status": "success",
            "support_type": "ai_support",
            "ai_response": result['ai_response'],
            "supports": state['supports']
        }
    
    else:
        raise HTTPException(status_code=400, detail="Invalid support type")

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    game = game_sessions[session_id]
    state = game.get_current_state()
    
    return {
        "level": state['level'],
        "supports": state['supports']
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
