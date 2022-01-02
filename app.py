from sqlalchemy import sql
from sqlalchemy.sql.expression import except_all
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import String
from fastapi import FastAPI
import databases, sqlalchemy, datetime, uuid
from pydantic import BaseModel, Field
from typing import Any, List
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.routing import request_response
import boto3
import base64



## POSTGRES DATABASE
DATABASE_URL = "postgresql://postgres:admin@34.236.249.184:5432/MS_Imagenes"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

imags = sqlalchemy.Table(
    "py_imagenes",
    metadata,
    sqlalchemy.Column("idImg",sqlalchemy.String,primary_key=True),
    sqlalchemy.Column("base64",sqlalchemy.String),
    sqlalchemy.Column("testId",sqlalchemy.String),
    sqlalchemy.Column("resultado",sqlalchemy.String),
    sqlalchemy.Column("tiempo", sqlalchemy.String),
    sqlalchemy.Column("pregunta", sqlalchemy.String),
    sqlalchemy.Column("calificacion", sqlalchemy.String),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL
)
metadata.create_all(engine)

#MODELS

class ImgList(BaseModel):
    idImg : str
    base64 : str
    testId : str
    resultado : str
    tiempo : str
    pregunta : str
    calificacion : str

class TestList(BaseModel):
    response : str

class ImgEntry(BaseModel):    
    base64 : str = Field(..., example = "asdk9082189127jksajkdas")
    testId : str = Field(..., example = "5")
    tiempo : str = Field(..., example = "00:01")
    pregunta : str = Field(..., example = "Pregunta 1")
    calificacion : str = Field(..., example = "Excelente")

class TestEntry(BaseModel):
    img : str = Field(..., example = "hdasdklasdkla=base64")

app = FastAPI()

#DB CONNECT
@app.on_event("startup")
async def starup():
    await database.connect()

@app.on_event("shutdown")   
async def starup():
    await database.disconnect()

#CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#HOME
@app.get('/')
def read_root():
    return {"Welcome":"Welcome to my Rest API"}

#LISTAR TODAS LAS IMAGENES POR TEST ID
@app.get("/resultadosID/{testId2}")
async def find_all_imgs(testId2 : str):
    query = imags.select().where(imags.c.testId == testId2)
    return await database.fetch_all(query)

#LISTAR TODAS LAS IMAGENES
@app.get("/imagenes", response_model = List[ImgList])
async def find_all_imgs_testid():
    query = imags.select()
    return await database.fetch_all(query)

#GUARDAR IMAGEN
@app.post("/imagenes", response_model=ImgList)
async def register_img(imag: ImgEntry):
    gID = str(uuid.uuid1())
    gDate = str(datetime.datetime.now())
    query = imags.insert().values(
        idImg = gID,
        base64 = imag.base64,
        testId = imag.testId
    )

    await database.execute(query)
    return{
        "idImg":gID,
        **imag.dict(),
        "created_at": gDate
    }

#ANALIZAR IMAGEN
@app.post("/emotions" )
async def anlize_emotion(test: TestEntry ):    
    return {detect_faces(test.img)}

#ANALIZAR Y GUARDAR IMAGEN
@app.post("/emotionsaws")
async def register_img(imag: ImgEntry):
    gID = str(uuid.uuid1())
    gDate = str(datetime.datetime.now())
    query = imags.insert().values(
        idImg = gID,
        base64 = imag.base64,
        testId = imag.testId,
        resultado = detect_faces(imag.base64),
        tiempo = imag.tiempo,
        pregunta = imag.pregunta,
        calificacion = imag.calificacion,
    )

    await database.execute(query)
    return{
        "message": 'OK IMAGEN GUARDADA',
        "idImg":gID,
        "created_at": gDate
    }

## Rekognition Detect faces

emocionesDiccionario = {'CALM':'CALMADO','SURPRISED':'SORPRENDIDO','FEAR':'MIEDO','ANGRY':'ENOJADO','CONFUSED':'CONFUNDIDO','SAD':'TRISTE','HAPPY':'FELIZ','DISGUSTED':'DISGUSTADO'}
def detect_faces(photo):

    client = boto3.client('rekognition',
        aws_access_key_id="AKIAZ2HA54RRYNUCVXVO",
        aws_secret_access_key="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",
        region_name="us-east-1"

    )
    photo = base64.b64decode(photo[23:])
    response = client.detect_faces(
        Image={
            'Bytes': photo
        },
        Attributes=[
            'ALL'
        ]
    )

    for faceDetail in response['FaceDetails']:
        respuesta = []        
        for emotion in faceDetail['Emotions']:            
            respuesta.append([emotion['Type'] , float(emotion['Confidence'])])
            break
        # respuesta = str(faceDetail['Emotions']['Type']) + str(faceDetail['Emotions']['Confidence'])
    return str(emocionesDiccionario.get(str(respuesta[0][0]),"SIN EMOCIÓN") + " = " + str(float(respuesta[0][1]))[0:2] + "%")