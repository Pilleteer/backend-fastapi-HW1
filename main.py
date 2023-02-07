from fastapi import FastAPI, HTTPException, Body
from datetime import date
from pymongo import MongoClient
from pydantic import BaseModel

DATABASE_NAME = "hotel"
COLLECTION_NAME = "reservation"
MONGO_DB_URL = "mongodb://localhost"
MONGO_DB_PORT = 27017


class Reservation(BaseModel):
    name : str
    start_date: date
    end_date: date
    room_id: int


client = MongoClient(f"{MONGO_DB_URL}:{MONGO_DB_PORT}")

db = client[DATABASE_NAME]

collection = db[COLLECTION_NAME]

app = FastAPI()


def room_avaliable(room_id: int, start_date: str, end_date: str):
    query={"room_id": room_id,
           "$or": 
                [{"$and": [{"start_date": {"$lte": start_date}}, {"end_date": {"$gte": start_date}}]},
                 {"$and": [{"start_date": {"$lte": end_date}}, {"end_date": {"$gte": end_date}}]},
                 {"$and": [{"start_date": {"$gte": start_date}}, {"end_date": {"$lte": end_date}}]}]
            }
    
    result = collection.find(query, {"_id": 0})
    list_cursor = list(result)

    return not len(list_cursor) > 0


@app.get("/reservation/by-name/{name}")
def get_reservation_by_name(name: str):
    res=list(collection.find({"name": name}, {"_id": 0}))
    return {"result": res}

@app.get("/reservation/by-room/{room_id}")
def get_reservation_by_room(room_id: int):
    res=list(collection.find({"room_id": room_id}, {"_id": 0}))
    return {"result": res}

@app.post("/reservation")
def reserve(reservation : Reservation):
    if reservation.room_id < 1 or reservation.room_id > 10:
        raise HTTPException(status_code=400, detail="Room id must be greater than 0 and less than 10")
    if reservation.start_date > reservation.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    reservelist = list(collection.find({"room_id": reservation.room_id}))
    if(not room_avaliable(reservation.room_id, str(reservation.start_date), str(reservation.end_date))):
        raise HTTPException(status_code=400, detail="Room is not avaliable")
    res= reservation.dict()
    res['start_date'] = str(res['start_date'])
    res['end_date'] = str(res['end_date'])
    collection.insert_one(res)
    return "Reservation inserted"
    

@app.put("/reservation/update")
def update_reservation(reservation: Reservation, new_start_date: date = Body(), new_end_date: date = Body()):
    if(new_start_date == "" and new_end_date == "") or (reservation.start_date == new_start_date and reservation.end_date == new_end_date):
        raise HTTPException(status_code=400, detail="No new date")
    if new_start_date > new_end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    if(not room_avaliable(reservation.room_id, str(new_start_date), str(new_end_date))):
        raise HTTPException(status_code=400, detail="Room is not avaliable")
    collection.update_one({"name": reservation.name}, {"$set": {"start_date": str(new_start_date), "end_date": str(new_end_date)}})
    return "Reservation updated"

@app.delete("/reservation/delete")
def cancel_reservation(reservation: Reservation):
    collection.delete_one({"name": reservation.name, "room_id": reservation.room_id, "start_date": str(reservation.start_date), "end_date": str(reservation.end_date)})
    return "Reservation deleted"