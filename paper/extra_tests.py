"""Formal crowding tests (Table: Does CFTC Crowding Predict Carry?) and Strategy C Bitcoin-exposure tests.
Run from the repo root: python paper/extra_tests.py"""
import importlib.util, pandas as pd, numpy as np, statsmodels.api as sm, statsmodels.formula.api as smf
spec=importlib.util.spec_from_file_location("sa","code/02_backtest_strategyA.py"); sa=importlib.util.module_from_spec(spec); spec.loader.exec_module(sa)
spot,rates,weekly=sa.load(); rx=sa.excess_returns(spot,rates)
diff=rates[sa.CCYS].sub(rates["USD"],axis=0)
w=pd.read_csv("output/strategyA/weights_carry.csv",index_col=0,parse_dates=True)[sa.CCYS]
crowd,z=sa.crowding_signal(weekly,w,w.index)
# panel: next-month rx on z, diff
d=pd.concat({"rx1":rx.shift(-1).stack(),"z":z.stack(),"diff":diff.stack()},axis=1).dropna()
d.index.names=["date","ccy"]; d=d.reset_index(); d=d[(d.date>="1999-04")&(d.date<="2026-07")]
d["rx1"]*=100; d["sgn"]=np.sign(d["diff"]); d["crx"]=d["sgn"]*d["rx1"]; d["cz"]=d["sgn"]*d["z"]
print("N",len(d), d.date.nunique())
def show(name,m): print(f"{name}: "+", ".join(f"{k} {m.params[k]:.3f} (t {m.tvalues[k]:.2f})" for k in m.params.index if k!="Intercept" and not k.startswith("C(")), f"N={int(m.nobs)}")
cl={"cov_type":"cluster","cov_kwds":{"groups":pd.factorize(d.date)[0]}}
show("P1 rx1~z+diff (cluster month)", smf.ols("rx1~z+diff",d).fit(**cl))
show("P2 + ccy FE", smf.ols("rx1~z+diff+C(ccy)",d).fit(**cl))
show("P3 + month FE (cross-sectional)", smf.ols("rx1~z+diff+C(date)",d).fit(cov_type="cluster",cov_kwds={"groups":pd.factorize(d.ccy)[0]}))
show("P3b month FE, HC1", smf.ols("rx1~z+diff+C(date)",d).fit(cov_type="HC1"))
show("P4 carry-signed: crx~cz", smf.ols("crx~cz",d).fit(**cl))
# interaction: crowding hurts high-rate currencies
show("P5 rx1~diff*z", smf.ols("rx1~diff*z",d).fit(**cl))
# portfolio continuous
a=pd.read_csv("output/strategyA/monthly_returns.csv",index_col=0,parse_dates=True)
y=a["Carry (net)"]*100; x=a["crowding"].shift(1)
pp=pd.concat({"y":y,"x":x},axis=1).dropna()
m=sm.OLS(pp.y,sm.add_constant(pp.x)).fit(cov_type="HAC",cov_kwds={"maxlags":3}); print("Port cont:",m.params.round(3).to_dict(),m.tvalues.round(2).to_dict(),len(pp))
# tail: worst 10% months
q=pp.y.quantile(0.1); pp["bad"]=(pp.y<=q).astype(int)
lg=sm.Logit(pp.bad,sm.add_constant(pp.x)).fit(disp=0); print("Logit tail:",lg.params.round(3).to_dict(),lg.tvalues.round(2).to_dict())
lp=sm.OLS(pp.bad,sm.add_constant(pp.x)).fit(cov_type="HAC",cov_kwds={"maxlags":3}); print("LPM tail:",lp.params.round(3).to_dict(),lp.tvalues.round(2).to_dict())
print("bad rate crowded vs not:", pp.bad[pp.x>1].mean(), pp.bad[pp.x<=1].mean(), (pp.x>1).sum())
# quantile regression
qr=smf.quantreg("y~x",pp).fit(q=0.1); print("QR10:",qr.params.round(3).to_dict(),qr.tvalues.round(2).to_dict())
# horizons 3,6 months ahead cumulative for portfolio
for h in (3,6,12):
    yh=y[::-1].rolling(h).sum()[::-1].shift(-0)  # sum t..t+h-1
    q2=pd.concat({"y":yh,"x":x},axis=1).dropna()
    m=sm.OLS(q2.y,sm.add_constant(q2.x)).fit(cov_type="HAC",cov_kwds={"maxlags":h+2}); print(f"h={h}:",round(m.params.x,3),round(m.tvalues.x,2),len(q2))

# ---- Strategy C exposure to Bitcoin
r = pd.read_csv("output/strategyC/daily_returns.csv", index_col=0, parse_dates=True)["Crypto carry (net)"].dropna()
px = pd.read_csv("data/clean/crypto_close_daily.csv", index_col=0, parse_dates=True)
b = px.filter(like="BTC").iloc[:, 0].pct_change()
d = pd.concat({"r": r, "b": b}, axis=1).dropna()
def hac(y, X, lags=5):
    return sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
m = hac(d.r, d.b); print("daily beta", round(m.params.b, 3), "t", round(m.tvalues.b, 2), "CI", m.conf_int().loc["b"].round(3).tolist())
X = pd.concat({f"b{l}": d.b.shift(l) for l in range(4)}, axis=1); dd = pd.concat([d.r, X], axis=1).dropna()
m = hac(dd.r, dd[X.columns]); print("lags sum", round(m.params[X.columns].sum(), 3), m.tvalues[X.columns].round(2).to_dict())
w = (1 + d).resample("W-SUN").prod() - 1; m = hac(w.r, w.b, 3); print("weekly beta", round(m.params.b, 3), "t", round(m.tvalues.b, 2), "CI", m.conf_int().loc["b"].round(3).tolist())
mo = (1 + d).resample("ME").prod() - 1; m = hac(mo.r, mo.b, 3); print("monthly beta", round(m.params.b, 3), "t", round(m.tvalues.b, 2))
d["dn"] = d.b.clip(upper=0); d["up"] = d.b.clip(lower=0); m = hac(d.r, d[["dn", "up"]]); print("down/up", m.params[["dn", "up"]].round(3).to_dict(), m.tvalues[["dn", "up"]].round(2).to_dict())
t5 = d[d.b <= d.b.quantile(0.05)]; print("BTC worst 5% days", len(t5), round(t5.b.mean() * 100, 2), round(t5.r.mean() * 100, 3), round(t5.r.mean() / t5.r.std() * np.sqrt(len(t5)), 2))
tw = w[w.b <= w.b.quantile(0.1)]; print("BTC worst 10% weeks", len(tw), round(tw.b.mean() * 100, 1), round(tw.r.mean() * 100, 2), round(tw.r.mean() / tw.r.std() * np.sqrt(len(tw)), 2))
rb = d.r.rolling(365).cov(d.b) / d.b.rolling(365).var(); print("rolling 1y beta", round(rb.min(), 2), round(rb.max(), 2), "| corr of abs moves", round(d.r.abs().corr(d.b.abs()), 2))
