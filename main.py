from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool


class QuestionBase(BaseModel):
    question_text: str
    choices: List[ChoiceBase]

# connection to the DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
db_dependency = Annotated[Session, Depends(get_db)]

# API end points 

# Fetch a question
@app.get("/question/{question_id}")
async def get_question(question_id: int, db: db_dependency):
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

# Fetch all choices for a particular question
@app.get("/choice/{question_id}")
async def get_choices(question_id: int, db: db_dependency):
    choices = db.query(models.Choices).filter(models.Choices.question_id == question_id).all()
    if choices is None:
        raise HTTPException(status_code=404, detail="Choices not found")
    return choices

# Create a question and choices
@app.post("/question/")
async def create_question(question: QuestionBase, db: db_dependency):
    db_question = models.Question(question_text=question.question_text)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    for choice in question.choices:
        db_choice = models.Choices(choice_text=choice.choice_text, is_correct=choice.is_correct, question_id=db_question.id)
        db.add(db_choice)
    db.commit()
    
# Delete a question and associated choices
@app.delete("/question/{question_id}")
async def delete_question(question_id: int, db: db_dependency):
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    db.query(models.Choices).filter(models.Choices.question_id == question_id).delete()
    db.commit()
    db.delete(question)
    db.commit()

# Update a question and associated choices
@app.put("/question/{question_id}")
async def update_question(question_id: int, updated_question: QuestionBase, db: db_dependency):
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    # Update question text
    question.question_text = updated_question.question_text
    db.commit()

    # Delete existing choices
    db.query(models.Choices).filter(models.Choices.question_id == question_id).delete()
    db.commit()

    # Add updated choices
    for choice in updated_question.choices:
        db_choice = models.Choices(choice_text=choice.choice_text, is_correct=choice.is_correct, question_id=question.id)
        db.add(db_choice)
    db.commit()

    return {"detail": "Question and associated choices updated successfully"}
