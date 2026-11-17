from math import isfinite

def ema(a,n):
    k=2/(n+1); out=[]; p=None
    for i,v in enumerate(a):
        p=v if p is None else v*k+p*(1-k); out.append(p if i>=n-1 else None)
    return out
def sma(a,n): return [None if i<n-1 else sum(a[i-n+1:i+1])/n for i in range(len(a))]
def rsi(a,n=14):
    out=[None]*len(a)
    for i in range(n,len(a)):
        g=l=0
        for j in range(i-n+1,i+1):
            d=a[j]-a[j-1]; g+=max(d,0); l+=max(-d,0)
        out[i]=100 if l==0 else 100-100/(1+g/l)
    return out
def pivots(d,s=3):
    h=[]; l=[]
    for i in range(s,len(d)-s):
        if all(d[i]["high"]>d[j]["high"] for j in range(i-s,i+s+1) if j!=i): h.append({"index":i,"price":d[i]["high"]})
        if all(d[i]["low"]<d[j]["low"] for j in range(i-s,i+s+1) if j!=i): l.append({"index":i,"price":d[i]["low"]})
    return h,l

def analyze_klines(symbol,interval,raw):
    if len(raw)<210: raise ValueError("At least 210 candles are required.")
    d=[{"time":int(x[0]),"open":float(x[1]),"high":float(x[2]),"low":float(x[3]),"close":float(x[4]),"volume":float(x[5])} for x in raw]
    c=[x["close"] for x in d]; last=d[-1]; price=last["close"]
    e20,e50,e100,e200=[ema(c,n) for n in (20,50,100,200)]; rv=rsi(c)
    ml=[a-b for a,b in zip(ema(c,12),ema(c,26))]; ms=ema(ml,9)
    tr=[x["high"]-x["low"] if i==0 else max(x["high"]-x["low"],abs(x["high"]-d[i-1]["close"]),abs(x["low"]-d[i-1]["close"])) for i,x in enumerate(d)]
    atr=sma(tr,14)[-1]; highs,lows=pivots(d); ph=highs[-1] if highs else None; pl=lows[-1] if lows else None
    ph2=highs[-2] if len(highs)>1 else None; pl2=lows[-2] if len(lows)>1 else None
    structure="SIDEWAYS"
    if ph and pl and ph2 and pl2:
        if ph["price"]>ph2["price"] and pl["price"]>pl2["price"]: structure="BULLISH STRUCTURE"
        elif ph["price"]<ph2["price"] and pl["price"]<pl2["price"]: structure="BEARISH STRUCTURE"
    bos="NONE"
    if ph and price>ph["price"]: bos="BULLISH BOS"
    elif pl and price<pl["price"]: bos="BEARISH BOS"
    prev=d[-8:-1]; hi=max(x["high"] for x in prev); lo=min(x["low"] for x in prev); sweep="NONE"
    if last["high"]>hi and price<hi: sweep="BUY-SIDE SWEEP"
    elif last["low"]<lo and price>lo: sweep="SELL-SIDE SWEEP"
    bull=bear=None
    for i in range(2,len(d)):
        if d[i]["low"]>d[i-2]["high"]: bull={"low":d[i-2]["high"],"high":d[i]["low"]}
        if d[i]["high"]<d[i-2]["low"]: bear={"low":d[i]["high"],"high":d[i-2]["low"]}
    ob=None
    for i in range(len(d)-2,max(0,len(d)-35),-1):
        a,b=d[i],d[i+1]
        if a["close"]<a["open"] and b["close"]>a["high"]: ob={"type":"BULLISH CANDLE PROXY","low":a["low"],"high":a["high"]}; break
        if a["close"]>a["open"] and b["close"]<a["low"]: ob={"type":"BEARISH CANDLE PROXY","low":a["low"],"high":a["high"]}; break
    rh=max(x["high"] for x in d[-100:]); rl=min(x["low"] for x in d[-100:]); mid=(rh+rl)/2
    volavg=sum(x["volume"] for x in d[-21:-1])/20; vr=last["volume"]/volavg if volavg else None
    eb=price>e20[-1]>e50[-1]>e100[-1]>e200[-1]; es=price<e20[-1]<e50[-1]<e100[-1]<e200[-1]; mb=ml[-1]>ms[-1]; r=rv[-1]
    sb=sum([eb,mb,structure=="BULLISH STRUCTURE",bos=="BULLISH BOS",sweep=="SELL-SIDE SWEEP",50<r<70])
    ss=sum([es,not mb,structure=="BEARISH STRUCTURE",bos=="BEARISH BOS",sweep=="BUY-SIDE SWEEP",30<r<50])
    direction="SIDEWAYS"
    if sb>=4 and sb>=ss+2: direction="BULLISH"
    elif ss>=4 and ss>=sb+2: direction="BEARISH"
    signal="NO TRADE"; entry=sl=t1=t2=t3=None
    if direction=="BULLISH" and atr and ph and pl:
        entry=price; sl=min(pl["price"],price-1.5*atr); risk=entry-sl
        if risk>0: signal="BUY"; t1=entry+risk; t2=entry+2*risk; t3=entry+3*risk
    elif direction=="BEARISH" and atr and ph and pl:
        entry=price; sl=max(ph["price"],price+1.5*atr); risk=sl-entry
        if risk>0: signal="SELL"; t1=entry-risk; t2=entry-2*risk; t3=entry-3*risk
    def clean(x): return round(x,10) if x is not None and isfinite(x) else None
    return {"symbol":symbol,"interval":interval,"lastPrice":clean(price),"marketDirection":direction,"signal":signal,"entry":clean(entry),"stopLoss":clean(sl),"takeProfit1":clean(t1),"takeProfit2":clean(t2),"takeProfit3":clean(t3),"riskReward":"1:3" if signal!="NO TRADE" else None,
    "indicators":{"rsi14":clean(r),"ema20":clean(e20[-1]),"ema50":clean(e50[-1]),"ema100":clean(e100[-1]),"ema200":clean(e200[-1]),"macd":clean(ml[-1]),"macdSignal":clean(ms[-1]),"atr14":clean(atr),"volumeVs20Average":clean(vr)},
    "smc":{"marketStructure":structure,"bosChochHint":bos,"liquiditySweepHint":sweep,"bullishFVG":bull,"bearishFVG":bear,"orderBlockProxy":ob,"premiumDiscount":"PREMIUM" if price>mid else "DISCOUNT","rangeHigh100":clean(rh),"rangeLow100":clean(rl),"rangeMidpoint":clean(mid),"fibonacci":{str(x):clean(rh-(rh-rl)*x) for x in (.236,.382,.5,.618,.786)}},
    "evidenceScore":{"bullish":sb,"bearish":ss,"max":6,"meaning":"Confirmation count, not a win probability."},"data":{"provider":"Binance Spot REST","candleCount":len(d),"lastCandleOpenTime":last["time"],"note":"Latest candle may still be forming; SMC labels are simplified OHLCV proxies."}}
