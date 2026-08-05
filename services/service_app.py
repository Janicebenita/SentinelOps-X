from fastapi import FastAPI

def create_service(name: str) -> FastAPI:
    app=FastAPI(title=name,version="1.0.0")
    @app.get("/health")
    def health(): return {"status":"ok","service":name,"production_action":"NOT_EXECUTED"}
    @app.get("/readiness")
    def readiness(): return {"ready":True,"service":name,"production_action":"NOT_EXECUTED"}
    return app
