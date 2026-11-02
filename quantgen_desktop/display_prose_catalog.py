"""Whole authored UI messages; captured values and identifiers stay verbatim."""
import re


def cms_schedule_korean(text):
    """Match the complete known CMS coupon-detail grammar, not arbitrary notes."""
    number = r'[+-]?\d+(?:\.\d+)?'
    match = re.fullmatch(rf'(?P<leverage>{number})× spread, floor (?P<floor>{number}%), '
                         rf'cap (?P<cap>none|{number}%); (?P<schedule>.+)', text)
    if not match: return text
    rows = []
    for row in match['schedule'].split(', '):
        coupon = re.fullmatch(rf'(?P<tenor>{number}[ymd]): (?P<coupon>{number}%) '
                              rf'\(spread (?P<spread>{number}bp)\)', row)
        if not coupon: return text
        rows.append(f"{coupon['tenor']}: {coupon['coupon']} (스프레드 {coupon['spread']})")
    cap = '없음' if match['cap'] == 'none' else match['cap']
    return f"스프레드 {match['leverage']}배, 하한 {match['floor']}, 상한 {cap}; " + ', '.join(rows)

PAIRS = r'''
strong bullish|강한 상승 우위
bullish|상승 우위
neutral|중립
bearish|하락 우위
strong bearish|강한 하락 우위
Detail|상세
Leg|구성요소
Rationale|근거
Value · per 100|값 · 100당
Product|상품
Fair value · per 100|공정가치 · 100당
Issue price|발행가격
Participation|참여율
Sleeve|전략별 구성
Study decision|연구 판정
Day|요일
Mean return %|평균 수익률 %
Mean volume|평균 거래량
Vol %|변동성 %
Kimchi premium · %|김치 프리미엄 · %
Funding annualized · %|연율 펀딩 · %
Funding percentile|펀딩 백분위
BTC conditional vol · 365 days|BTC 조건부 변동성 · 365일
Premium z|프리미엄 z
Check|검사
Tests|검사 수
Violations|위반 수
Parity forward|패리티 선도가격
Future|선물
Basis · points|베이시스 · 포인트
Fair value|공정가치
Mispricing · bp of spot|가격 괴리 · 현물 대비 bp
Implied funding|내재 조달금리
KIS theoretical gap · points|KIS 이론가격 차이 · 포인트
ATM IV|ATM 내재 변동성
Model-free IV|모형 비의존 내재 변동성
SVI RMSE · vol points|SVI RMSE · 변동성 포인트
SVI rho|SVI ρ
Butterfly arbitrage free|버터플라이 차익거래 없음
IV reconciliation gap · vol points|내재 변동성 대조 차이 · 변동성 포인트
Box funding|박스 내재 조달금리
RND integral|위험중립 밀도 적분
Engine|엔진
Paths / sessions|경로 수 / 거래일
Mean P&L · bp|평균 손익 · bp
SE · bp|표준오차 · bp
CVaR95 · bp|CVaR95 · bp
Hedge volatility|헤지 변동성
Break-even realised vol|손익분기 실현 변동성
Identity slope / R²|항등식 기울기 / R²
GARCH nu|GARCH ν
GARCH persistence|GARCH 지속성
Converged|수렴 여부
At bound|경계 도달
Margin · per 100|마진 · 100당
Maturity · years|만기 · 년
Enhanced yield · simple|우대 수익률 · 단리
Coupon / year|연간 쿠폰
Risk|위험
Value · {currency}|값 · {currency}
Delta · per +1% spot|델타 · 현물 +1%당
Gamma · per +1% spot|감마 · 현물 +1%당
Vega · per vol point|베가 · 변동성 포인트당
DV01 · per -1bp|DV01 · -1bp당
2s10s DV01 · per +1bp|2s10s DV01 · +1bp당
Per-asset cap {cap}; {assets} independent sleeves; no portfolio gross cap. Theoretical total upper bound {bound}. Single-asset rules; multi-asset input is an unnormalized sum, not portfolio volatility targeting.|종목당 상한 {cap}; 독립 전략 {assets}개; 포트폴리오 총노출 상한 없음. 이론적 총 상한 {bound}. 단일 종목 규칙이며, 여러 종목 입력은 정규화하지 않은 합계로 포트폴리오 변동성 목표가 아닙니다.
OOS held gross exposure: mean {mean}, max {maximum} across {observations} observations. Uses each walk-forward origin's selected configuration, not the final winner for all dates.|OOS 보유 총노출: 관측 {observations}개에서 평균 {mean}, 최대 {maximum}. 모든 날짜에 마지막 최적 설정을 적용하는 대신 각 순차 전진 시작점에서 선택한 설정을 사용합니다.
Maximum OOS borrowing {borrowing} equity. Cash = 1 − sum(weights); negative cash is borrowed at {rate} per session (Lab assumption: 3% / 252). The 1× equal-weight daily-return benchmark is not exposure-matched.|최대 OOS 차입은 자기자본의 {borrowing}입니다. 현금 = 1 − sum(weights); 음수 현금은 거래일당 {rate}에 차입합니다 (Lab 가정: 3% / 252). 1× 동일 비중 일별 수익률 벤치마크는 노출을 일치시킨 비교가 아닙니다.
{source} · expiry {expiry} → {date} · as of {asof}|{source} · 만기 {expiry} → {date} · 기준일 {asof}
Session {session} · {strikes} strikes · rate {rate} ({source})|세션 {session} · 행사가 {strikes}개 · 금리 {rate} ({source})
Sleeve price basis: {basis} · study cards: {cards}|전략별 가격 기준: {basis} · 연구카드: {cards}
{cost} bp per side · in-sample descriptive results, not a new study decision.|편도 {cost} bp · 표본 내 기술통계이며 새로운 연구 판정이 아닙니다.
Index: {index} · prior-quarter variance AZ proxy {proxy} bp · GARCH converged={converged}|지수: {index} · 직전 분기 분산 AZ 대용값 {proxy} bp · GARCH 수렴={converged}
Public market analysis · no order submission · study cards: {cards}|공개 시장 분석 · 주문 제출 없음 · 연구카드: {cards}
Funding unavailable · insufficient or invalid funding history.|펀딩 조회 불가 · 이력이 부족하거나 유효하지 않습니다.
Weekday Bonferroni p={p} · weekend volume ratio={ratio}|요일 Bonferroni p={p} · 주말 거래량 비율={ratio}
Holdings unavailable · verify the configured read-only connection. No account values loaded.|보유 자산 조회 불가 · 설정된 읽기 전용 연결을 확인하세요. 계좌 수치를 불러오지 않았습니다.
Provider: {provider}|공급자: {provider}
{rows} rows · first 300 displayed|{rows}개 행 · 처음 300개 표시
Read-only market observations; no order or account operation.|시장 관측 조회 전용이며 주문이나 계좌 조작을 수행하지 않습니다.
Grid/DSR trials {grid}/{trials} · cumulative ledger configurations {count}|그리드/DSR 시행 {grid}/{trials} · 누적 원장 설정 {count}개
Walk-forward: {note} · last in-sample winner: {winner}|순차 전진: {note} · 마지막 표본 내 최적 설정: {winner}
Decision: {decision} · {reason}|판정: {decision} · {reason}
sources={sources} · {sessions} shared sessions · {cost} bp/side|출처={sources} · 공통 거래일 {sessions}개 · 편도 {cost} bp
Sessions · {start} → {end}|거래일 · {start} → {end}
Price vs 50-day SMA|가격과 50일 이동평균
Price vs 200-day SMA|가격과 200일 이동평균
3-month momentum|3개월 모멘텀
Volatility regime|변동성 상태
Price is {gap}% above its 50-day average.|가격은 50일 평균보다 {gap}% 높습니다.
Price is {gap}% below its 50-day average.|가격은 50일 평균보다 {gap}% 낮습니다.
Price is {gap}% above its 200-day average — the long trend is up.|가격은 200일 평균보다 {gap}% 높으며 장기 추세는 상승입니다.
Price is {gap}% below its 200-day average — the long trend is down.|가격은 200일 평균보다 {gap}% 낮으며 장기 추세는 하락입니다.
Price moved {change}% over the last 63 sessions.|최근 63개 거래일 동안 가격은 {change}% 변했습니다.
RSI {rsi} is overbought — stretched to the upside.|RSI {rsi}은 과매수이며 상승 방향으로 치우쳐 있습니다.
RSI {rsi} is oversold — stretched to the downside.|RSI {rsi}은 과매도이며 하락 방향으로 치우쳐 있습니다.
RSI {rsi} is in the neutral band.|RSI {rsi}은 중립 구간입니다.
MACD line is above its signal line by {gap}.|MACD 선은 신호선보다 {gap} 높습니다.
MACD line is below its signal line by {gap}.|MACD 선은 신호선보다 {gap} 낮습니다.
20-day volatility is {ratio}× its 100-day level — compressed.|20일 변동성은 100일 수준의 {ratio}배이며 축소되어 있습니다.
20-day volatility is {ratio}× its 100-day level — elevated.|20일 변동성은 100일 수준의 {ratio}배이며 확대되어 있습니다.
20-day volatility is {ratio}× its 100-day level — normal.|20일 변동성은 100일 수준의 {ratio}배이며 보통입니다.
Principal-protected note ({underlying})|원금보장형 상품 ({underlying})
Reverse convertible ({underlying})|역전환형 상품 ({underlying})
Dual-currency deposit {pair} K={strike}|이중통화 예금 {pair} K={strike}
CMS 10y-2y steepener note|CMS 10y-2y 스티프너 상품
Zero-coupon bond|무이표채
Coupon bond|이표채
Short put|풋 매도
Principal|원금
CMS 10y−2y coupons|CMS 10y−2y 쿠폰
{ccy} deposit|{ccy} 예금
Short {ccy} put|{ccy} 풋 매도
shares|주
base ccy units|기준통화 단위
contracts|계약
Underlying spot/forward|기초자산 현물/선도
{tenor} vanilla K={strike}|{tenor} 바닐라 K={strike}
{tenor} payer swap|{tenor} 고정금리 지급 스왑
{tenor} receiver swap|{tenor} 고정금리 수취 스왑
Bond futures|채권 선물
2s10s flattener: 10y receiver|2s10s 플래트너: 10y 고정금리 수취
2s10s flattener: 2y payer|2s10s 플래트너: 2y 고정금리 지급
{protection} of principal at {tenor}, DF {df} (zero {zero})|{tenor}에 원금의 {protection}, DF {df} (제로 금리 {zero})
{participation} × call K={strike} (fwd {forward}, vol {vol}) = {price} per 100 each|{participation} × 콜 K={strike} (선도 {forward}, 변동성 {vol}) = 각 100당 {price}
{coupon} annual, {tenor}; par rate {par}|연 {coupon}, {tenor}; 파 금리 {par}
K={strike} ({pct} of spot), vol {vol}, fwd {forward}; {units} units per 100|K={strike} (현물의 {pct}), 변동성 {vol}, 선도 {forward}; 100당 {units}단위
{yield} simple for {tenor} vs plain deposit {plain}; redeems {redemption}|{tenor} 단리 {yield}, 일반 예금 {plain} 대비; 상환 {redemption}
K={strike}, spot {spot}, fwd {forward}, vol {vol}; {units} {ccy} per 100|K={strike}, 현물 {spot}, 선도 {forward}, 변동성 {vol}; 100당 {units} {ccy}
100 at {tenor}, DF {df}|{tenor}에 100, DF {df}
note delta {delta} {ccy} per +1% spot = {units} shares; sell {quantity} to flatten|현물 +1%당 상품 델타 {delta} {ccy} = {units}주; 노출 중립화를 위해 {quantity} 매도
note delta {delta} {ccy} per +1% spot = {units} shares; buy {quantity} to flatten|현물 +1%당 상품 델타 {delta} {ccy} = {units}주; 노출 중립화를 위해 {quantity} 매수
note delta {delta} {ccy} per +1% spot = {units} base ccy units; sell {quantity} to flatten|현물 +1%당 상품 델타 {delta} {ccy} = 기준통화 {units}단위; 노출 중립화를 위해 {quantity} 매도
note delta {delta} {ccy} per +1% spot = {units} base ccy units; buy {quantity} to flatten|현물 +1%당 상품 델타 {delta} {ccy} = 기준통화 {units}단위; 노출 중립화를 위해 {quantity} 매수
note vega {vega} {ccy} per vol-pt vs {unit_vega} per unit; sell {quantity} shares of options|변동성 포인트당 상품 베가 {vega} {ccy}, 단위당 {unit_vega}; 옵션 {quantity}주 매도
note vega {vega} {ccy} per vol-pt vs {unit_vega} per unit; buy {quantity} shares of options|변동성 포인트당 상품 베가 {vega} {ccy}, 단위당 {unit_vega}; 옵션 {quantity}주 매수
note vega {vega} {ccy} per vol-pt vs {unit_vega} per unit; sell {quantity} base ccy units of options|변동성 포인트당 상품 베가 {vega} {ccy}, 단위당 {unit_vega}; 옵션 기준통화 {quantity}단위 매도
note vega {vega} {ccy} per vol-pt vs {unit_vega} per unit; buy {quantity} base ccy units of options|변동성 포인트당 상품 베가 {vega} {ccy}, 단위당 {unit_vega}; 옵션 기준통화 {quantity}단위 매수
note DV01 {dv01} {ccy} vs {per_mm} per 1mm payer; pay fixed on {notional}|상품 DV01 {dv01} {ccy}, 1mm 지급 스왑당 {per_mm}; 명목금액 {notional}의 고정금리 지급
note DV01 {dv01} {ccy} vs {per_mm} per 1mm payer; receive fixed on {notional}|상품 DV01 {dv01} {ccy}, 1mm 지급 스왑당 {per_mm}; 명목금액 {notional}의 고정금리 수취
sell {quantity} contracts at {dv01} DV01 each (alternative to the swap)|계약당 DV01 {dv01}의 선물 {quantity}계약 매도 (스왑의 대안)
buy {quantity} contracts at {dv01} DV01 each (alternative to the swap)|계약당 DV01 {dv01}의 선물 {quantity}계약 매수 (스왑의 대안)
note gains {amount} {ccy} per +1bp 2s10s steepening; receive 10y on {notional}|2s10s 스티프닝 +1bp당 상품 손익 {amount} {ccy}; 명목금액 {notional}의 10y 고정금리 수취
pay 2y on {notional} so the spread trade is DV01-neutral|스프레드 거래를 DV01 중립으로 만들기 위해 명목금액 {notional}의 2y 고정금리 지급
{tenor} {underlying} principal-protected note: {protection} protection, {participation}× participation in upside from {spot}; fair {fair} = zero {zero} + option {option}, distributor margin {margin} per 100. Single-curve, no issuer credit spread.|{tenor} {underlying} 원금보장형 상품: 보호 {protection}, {spot} 위 상승분에 {participation}배 참여; 공정가치 {fair} = 무이표채 {zero} + 옵션 {option}, 100당 판매자 마진 {margin}. 단일 곡선이며 발행자 신용 스프레드를 반영하지 않습니다.
{tenor} {underlying} reverse convertible: {coupon} coupon against a put at {strike_pct} of spot ({strike}); fair {fair} = bond {bond} − put {put}, margin {margin} per 100. Below {level} the holder takes the underlying at {conversion}. Single-curve, no issuer credit spread.|{tenor} {underlying} 역전환형 상품: 현물의 {strike_pct} ({strike}) 풋 매도에 대한 쿠폰 {coupon}; 공정가치 {fair} = 채권 {bond} − 풋 {put}, 100당 마진 {margin}. {level} 미만이면 보유자는 기초자산을 {conversion}에 인수합니다. 단일 곡선이며 발행자 신용 스프레드를 반영하지 않습니다.
{tenor} dual-currency deposit in {ccy}: enhanced yield {yield} against a plain {plain_ccy} deposit at {plain} (simple). If {pair} fixes below {strike} the {redemption} redemption is paid in {base} at {conversion}. Fair {fair}, margin {margin} per 100.|{tenor} {ccy} 이중통화 예금: 우대 수익률 {yield}, 일반 {plain_ccy} 예금 단리 {plain} 대비. {pair} 고시값이 {strike} 미만이면 상환액 {redemption}을 {conversion}에서 {base}로 지급합니다. 공정가치 {fair}, 100당 마진 {margin}.
{tenor} dual-currency deposit in {ccy}: enhanced yield {yield} against a plain {plain_ccy} deposit at {plain} (simple). If {pair} fixes below {strike} the {redemption} redemption is paid in {base} at {conversion}. Fair {fair}, margin {margin} per 100. Put premium {premium} per 100 covers only {covered} of the requested margin; margin reduced, no yield enhancement.|{tenor} {ccy} 이중통화 예금: 우대 수익률 {yield}, 일반 {plain_ccy} 예금 단리 {plain} 대비. {pair} 고시값이 {strike} 미만이면 상환액 {redemption}을 {conversion}에서 {base}로 지급합니다. 공정가치 {fair}, 100당 마진 {margin}. 100당 풋 프리미엄 {premium}이 요청 마진 중 {covered}만 충당하므로 마진을 축소했으며 수익률 우대가 없습니다.
{tenor} CMS steepener: coupon = clip({leverage} × (10y − 2y), {floor}, {cap}), first coupon {first}, average projected {average}; fair {fair} = principal {principal} + coupons {coupons}, margin {margin} per 100. WARNING: coupons are priced off the FORWARD curve with NO convexity adjustment (CMS forwards taken as unbiased), so the coupon leg is overstated; a replication-based CMS convexity correction is not applied.|{tenor} CMS 스티프너: 쿠폰 = clip({leverage} × (10y − 2y), {floor}, {cap}), 첫 쿠폰 {first}, 예상 평균 {average}; 공정가치 {fair} = 원금 {principal} + 쿠폰 {coupons}, 100당 마진 {margin}. 주의: 쿠폰은 볼록성 조정 없이 선도 곡선으로 평가합니다 (CMS 선도가 불편이라고 가정). 따라서 쿠폰 부분이 과대평가되며 복제에 기반한 CMS 볼록성 보정을 적용하지 않았습니다.
'''
