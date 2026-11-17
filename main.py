import os, asyncio
import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .analysis import analyze_klines

load_dotenv()
B=os.getenv("BINANCE_BASE_URL","https://api.binance.com").rstrip("/")
F=os.getenv("BINANCE_FUTURES_BASE_URL","https://fapi.binance.com").rstrip("/")
CMC=os.getenv("CMC_API_KEY","")
origins=[x.strip() for x in os.getenv("ALLOWED_ORIGINS","http://localhost:3000").split(",") if x.strip()]
app=FastAPI(title="AI Trading Analysis API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=["GET"],allow_headers=["*"])

async def getj(c,url,params=None,headers=None):
    try:
        r=await c.get(url,params=params,headers=headers,timeout=15); r.raise_for_status(); return r.json()
    except httpx.HTTPError as e:
        raise HTTPException(502,detail=f"Market data provider unavailable: {str(e)[:160]}")

@app.get("/health")
async def health(): return {"status":"ok","cmc_configured":bool(CMC)}

@app.get("/api/markets")
async def markets(quote:str="USDT",limit:int=Query(500,ge=1,le=2000)):
    async with httpx.AsyncClient() as c:
        info,ticks=await asyncio.gather(getj(c,f"{B}/api/v3/exchangeInfo"),getj(c,f"{B}/api/v3/ticker/24hr"))
        valid={x["symbol"]:x for x in info["symbols"] if x.get("status")=="TRADING" and x.get("quoteAsset")==quote and x.get("isSpotTradingAllowed",True)}
        rows=[]
        for t in ticks:
            s=valid.get(t["symbol"])
            if s: rows.append({"symbol":t["symbol"],"baseAsset":s["baseAsset"],"quoteAsset":quote,"price":t["lastPrice"],"change24h":t["priceChangePercent"],"volume24h":t["quoteVolume"],"high24h":t["highPrice"],"low24h":t["lowPrice"],"marketCap":None,"cmcRank":None})
        source="not_configured"
        if CMC:
            try:
                j=await getj(c,"https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",{"start":1,"limit":5000,"convert":"USD"},{"X-CMC_PRO_API_KEY":CMC})
                by={}
                for coin in j.get("data",[]): by.setdefault(coin["symbol"].upper(),coin)
                for row in rows:
                    coin=by.get(row["baseAsset"].upper())
                    if coin:
                        row["marketCap"]=coin.get("quote",{}).get("USD",{}).get("market_cap"); row["cmcRank"]=coin.get("cmc_rank")
                source="available"
            except Exception: source="unavailable"
        rows.sort(key=lambda x:(x["cmcRank"] is None,x["cmcRank"] or 999999,x["symbol"]))
        return {"data":rows[:limit],"totalAvailable":len(rows),"marketCapSource":source,"note":"CMC symbol matching can be ambiguous."}

@app.get("/api/market/{symbol}")
async def market(symbol:str):
    async with httpx.AsyncClient() as c: return await getj(c,f"{B}/api/v3/ticker/24hr",{"symbol":symbol.upper()})

@app.get("/api/klines/{symbol}")
async def klines(symbol:str,interval:str="1h",limit:int=Query(500,ge=210,le=1000)):
    if interval not in {"15m","1h","4h","1d","1w"}: raise HTTPException(400,"Unsupported interval")
    async with httpx.AsyncClient() as c: data=await getj(c,f"{B}/api/v3/klines",{"symbol":symbol.upper(),"interval":interval,"limit":limit})
    return {"symbol":symbol.upper(),"interval":interval,"candles":data}

@app.get("/api/analyze/{symbol}")
async def analyze(symbol:str,interval:str="1h"):
    if interval not in {"15m","1h","4h","1d","1w"}: raise HTTPException(400,"Unsupported interval")
    async with httpx.AsyncClient() as c: raw=await getj(c,f"{B}/api/v3/klines",{"symbol":symbol.upper(),"interval":interval,"limit":500})
    try: return analyze_klines(symbol.upper(),interval,raw)
    except ValueError as e: raise HTTPException(422,str(e))

@app.get("/api/positioning/{symbol}")
async def positioning(symbol:str):
    s=symbol.upper()
    async with httpx.AsyncClient() as c:
        async def optional(path,params):
            try:
                r=await c.get(F+path,params=params,timeout=12); r.raise_for_status(); return r.json()
            except Exception: return None
        oi,fund,ratio=await asyncio.gather(optional("/fapi/v1/openInterest",{"symbol":s}),optional("/fapi/v1/premiumIndex",{"symbol":s}),optional("/futures/data/globalLongShortAccountRatio",{"symbol":s,"period":"1h","limit":1}))
    row=ratio[0] if isinstance(ratio,list) and ratio else None
    return {"source":"Binance USD-M Futures","openInterest":oi.get("openInterest") if oi else None,"fundingRate":fund.get("lastFundingRate") if fund else None,"nextFundingTime":fund.get("nextFundingTime") if fund else None,"longPercent":float(row["longAccount"])*100 if row else None,"shortPercent":float(row["shortAccount"])*100 if row else None,"longShortRatio":row.get("longShortRatio") if row else None,"note":"Long/short is futures account positioning, not the entire market. Unavailable fields are null."}
