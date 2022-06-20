import asyncio
import base64
import json
import os.path
import uuid
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import calc
from _redis import redis_conn
from vtkmanager import _VTKProcess
from wsmanager import ConnectionManager
from config import conf

logger.add("./log/interface.log", rotation="500MB", encoding="utf-8", enqueue=True, compression="zip",
           retention="10 days")

app = FastAPI(title="三维重建")
origins = [
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()


# 获取心胸比AI坐标
class Series(BaseModel):
    PatientId: str
    StudyInstanceUID: str
    SeriesInstanceUID: str
    InstanceNumber: str


# 心胸比AI坐标接口
@app.post("/get_ctr")
async def get_ctr(s: Series):
    dcm_path = "/".join(
        [conf.get("app", "home"), s.PatientId, s.StudyInstanceUID, s.SeriesInstanceUID, s.InstanceNumber + ".dcm"])
    if os.path.exists(dcm_path):
        if redis_conn.exists(dcm_path):
            return json.loads(redis_conn.get(dcm_path))
        else:
            ctr = calc.get_ctr(dcm_path)
            redis_conn.set(dcm_path, json.dumps(ctr))
            redis_conn.expire(dcm_path, 180)
            return ctr
    else:
        raise HTTPException(
            status_code=1005,
            detail={'Error': '没有这个文件.'},
            headers={'X-Error': '没有这个文件.'}
        )


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    client_id = str(uuid.uuid4()).replace("-", "")
    p = _VTKProcess()
    await manager.connect(client_id, ws)
    await manager.send_client_id(client_id)
    try:
        while True:
            while redis_conn.llen(client_id + "base64") > 0:
                r = redis_conn.lpop(client_id + "base64")
                j = json.loads(r)
                await ws.send_json(j["attachment"])
                await ws.send_bytes(base64.b64decode(j["base64_data"]))
                await ws.send_json(j["subscription"])
            data = await asyncio.wait_for(ws.receive_json(), 60)
            receive = {
                "wslink": "1.0",
                "id": data['id'],
                "result": {
                    "result": "success"
                }
            }
            ids = data['id'].split(':')
            args = data["args"]
            if ids[0] == "rpc":
                method = data['method']
                # 加载数据
                if method == "myprotocol.loading":
                    ids = args[0]
                    p.initialize(client_id, ids["PatientId"], ids["StudyInstanceUID"], ids["SeriesInstanceUID"])
                # 切换VR显示参数
                if method == "myprotocol.switch":
                    p.switch_vr(args[0])
                # 添加事件
                if method == "viewport.image.push.observer.add":
                    receive["result"]["success"] = True
                    receive["result"]["viewId"] = "-1"
                    await ws.send_json(receive)
                if method == "viewport.image.push.observer.remove":
                    receive["result"]["success"] = True
                    receive["result"]["viewId"] = "-1"
                    await ws.send_json(receive)
                    await ws.close()
                # 设置原始窗口大小
                if method == "viewport.image.push.original.size":
                    p.SetWindowsSize(int(args[1]), int(args[2]))
                    await ws.send_json(receive)
                # 无效缓存
                if method == "viewport.image.push.invalidate.cache":
                    await ws.send_json(receive)
                # 调整窗口输出图像
                if method == "viewport.image.push":
                    # size = args[0]["size"]
                    # p.SetWindowsSize(int(size[0]), int(size[1]))
                    await ws.send_json(receive)
                # 图像质量调整
                if method == "viewport.image.push.quality":
                    p.SetQuality(int(args[1]))
                    await ws.send_json(receive)
                # 鼠标放大缩小
                if method == "viewport.mouse.zoom.wheel":
                    wheel = args[0]
                    if wheel['type'] == "StartMouseWheel":
                        p.Zoom(int(wheel['spinY']))
                    await ws.send_json(receive)
                # 鼠标移动
                if method == "viewport.mouse.interaction":
                    await ws.send_json(receive)
                    interaction = args[0]
                    p.mouseInteraction(interaction)

    except(asyncio.TimeoutError, WebSocketDisconnect):
        await ws.close()
        del p
        manager.disconnect(client_id)
        await manager.broadcast(f"Client #{client_id} left the chat")


if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8083, log_level="info", limit_max_requests=100, limit_concurrency=100)
    except Exception as e:
        logger.error(str(e))
        input("等待回车键退出。。。。。。。")
