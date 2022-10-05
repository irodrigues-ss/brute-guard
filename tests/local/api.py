import uvicorn

from datetime import datetime, timedelta

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import HTTPException

from brute_guard.sqlite3 import BruteGuard

app = FastAPI()

bg = BruteGuard(
    failure_time="-1 second",
    blocked_expires_at="+1 second",
    access_expires_at="+3 second",
    purge_time=timedelta(seconds=10),
    database_url="db.sqlite",
)
bg.control.create_tables()


class Body(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(body: Body):

    start = datetime.now()

    if bg.user.is_blocked(body.username):
        print(datetime.now() - start)
        raise HTTPException(status_code=403)

    if body.username == "teste" and body.password == "teste":
        bg.user.access(body.username, success=True)
        return {}

    bg.user.access(body.username, success=False)

    print(datetime.now() - start)
    raise HTTPException(status_code=401)


if __name__ == "__main__":

    # uvicorn.run('api:app', workers=1, port=8000)
    uvicorn.run("api:app", workers=4, port=8001)
