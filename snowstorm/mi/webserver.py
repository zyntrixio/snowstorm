import psycopg2
from fastapi import APIRouter, FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from redis import StrictRedis

from snowstorm.mi.lloyds_stats import MI_LloydsStats
from snowstorm.settings import settings


class MI_Web_Core:
    def __init__(self) -> None:
        self.router = APIRouter()
        self.router.add_api_route("/", self.root, response_class=RedirectResponse)
        self.router.add_api_route("/livez", self.livez, response_class=PlainTextResponse)
        self.router.add_api_route("/readyz", self.readyz, response_class=PlainTextResponse)

        self.redirect = "/lbg"
        self.redis_dsn = settings.redis_dsn
        self.database_dsn = settings.database_dsn

    def root(self) -> RedirectResponse:
        return RedirectResponse(url=self.redirect)

    def livez(self) -> Response:
        return Response(
            status_code=status.HTTP_204_NO_CONTENT,
        )

    def readyz(self) -> Response:
        try:
            StrictRedis.from_url(self.redis_dsn).ping()
            with psycopg2.connect(self.database_dsn).cursor() as cur:
                cur.execute("SELECT 1;")
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except Exception:
            return HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot connect to Redis or Postgres"
            )


class MI_Web_Lloyds:
    def __init__(self) -> None:
        self.router = APIRouter()
        self.router.add_api_route("/lbg", self.lbg, response_class=HTMLResponse)
        self.router.add_api_route("/lbg/api", self.api, response_class=JSONResponse)

    def lbg(self, auth: str = None) -> FileResponse:
        if auth == settings.webserver_auth_token:
            return FileResponse("/app/frontend/index.html")
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Auth Token Missing or Invalid",
            )

    def api(self, auth: str = None) -> JSONResponse:
        if auth == settings.webserver_auth_token:
            stats = MI_LloydsStats()
            data = stats.run()
            return JSONResponse(data)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Auth Token Missing or Invalid",
            )


app = FastAPI()
app.mount("/assets", StaticFiles(directory="/app/frontend/assets"), name="assets")
app.mount("/images", StaticFiles(directory="/app/frontend/images"), name="images")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
essentials = MI_Web_Core()
lloyds = MI_Web_Lloyds()
app.include_router(essentials.router)
app.include_router(lloyds.router)
