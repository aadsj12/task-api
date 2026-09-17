from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from database import init_db, get_connection
from pydantic import BaseModel
'''import sqlite3'''
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()
init_db()

class TaskCreate(BaseModel):
    title: str | None = None

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

class UserAuth(BaseModel):
    email: str
    password: str

'''tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Finish assignment", "done": False},
    {"id": 3, "title": "Go to the gym", "done": True}


def init_db():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            done INTEGER NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM tasks")
    task_count = cursor.fetchone()[0]

    if task_count == 0:
        starter_tasks = [
            (1, "Buy groceries", 0),
            (2, "Finish assignment", 0),
            (3, "Go to the gym", 1)
        ]

        cursor.executemany(
            "INSERT INTO tasks (id, title, done) VALUES (?, ?, ?)",
            starter_tasks
        )

    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn
    '''

@app.get("/", summary="Get API information")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }


@app.get("/health", summary="Check API health")
def health():
    return {"status": "ok"}

@app.post("/auth/signup", status_code=201, summary="Sign up a new user")
def signup(user: UserAuth):
    try:
        response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password
        })

        return {
            "message": "User created successfully",
            "user_id": response.user.id
        }

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )

@app.get("/tasks", summary="Get all tasks")
def get_tasks():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM tasks ORDER BY id")
            rows = cursor.fetchall()

    return rows

@app.get("/tasks/{task_id}", summary="Get a task by ID")
def get_task(task_id: int):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM tasks WHERE id = %s",
                (task_id,)
            )
            row = cursor.fetchone()

    if row is None:
        return JSONResponse(
            status_code=404,
            content={"error": "Task not found"}
        )

    return row

@app.post("/tasks", status_code=201, summary="Create a new task")
def create_task(task: TaskCreate):
    if task.title is None or not task.title.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Title cannot be empty"}
        )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id",
                (task.title, False)
            )
            new_task_id = cursor.fetchone()["id"]

    return {
        "id": new_task_id,
        "title": task.title,
        "done": False
    }

@app.put("/tasks/{task_id}", summary="Update a task")
def update_task(task_id: int, updated_task: TaskUpdate):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM tasks WHERE id = %s",
                (task_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return JSONResponse(
                    status_code=404,
                    content={"error": "Task not found"}
                )

            if updated_task.title is None and updated_task.done is None:
                return JSONResponse(
                    status_code=400,
                    content={"error": "No fields to update"}
                )

            if updated_task.title is not None and not updated_task.title.strip():
                return JSONResponse(
                    status_code=400,
                    content={"error": "Title cannot be empty"}
                )

            new_title = (
                updated_task.title
                if updated_task.title is not None
                else row["title"]
            )

            new_done = (
                updated_task.done
                if updated_task.done is not None
                else row["done"]
            )

            cursor.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s",
                (new_title, new_done, task_id)
            )

    return {
        "id": task_id,
        "title": new_title,
        "done": new_done
    }

@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM tasks WHERE id = %s",
                (task_id,)
            )
            row = cursor.fetchone()

            if row is None:
                return JSONResponse(
                    status_code=404,
                    content={"error": "Task not found"}
                )

            cursor.execute(
                "DELETE FROM tasks WHERE id = %s",
                (task_id,)
            )

    return