"""Short, contextual orientation for research workflows; never changes a request."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget
from .chart_study import LocalLabel

# Purpose, one-line scope, and the three actual stages. Authored in both languages.
GUIDES = {
    'bonds': (
        ('금리가 바뀌면 채권 가격은 얼마나 달라질까요?', 'How does a rate change affect a bond?'),
        ('채권 조건으로 가격과 민감도를 계산하고, 금리 변화에 따른 손익을 살펴봐요.',
         'Use bond terms to calculate value and sensitivity, then inspect gains and losses under rate changes.'),
        (('채권 조건 입력','Enter bond terms'),('가격·위험 계산','Calculate value and risk'),('시나리오 비교','Compare scenarios'))),
    'rates': (
        ('기간에 따라 금리가 어떻게 달라질까요?', 'How do rates change across maturities?'),
        ('금리 곡선과 할인율을 만들고, 선택한 금리 모형의 결과를 확인해요.',
         'Build rate curves and discount factors, and examine the selected rate model.'),
        (('계산할 도구 선택','Choose a calculation'),('만기·금리 입력','Enter maturities and rates'),('곡선과 민감도 읽기','Read curves and sensitivities'))),
    'structuring': (
        ('상품의 조건이 손익을 어떻게 바꿀까요?', 'How do product terms change the payoff?'),
        ('구조화 상품의 조건과 가정을 정하고, 가격·손익·위험을 확인해요.',
         'Set structured-product terms and assumptions to inspect price, payoff and risk.'),
        (('상품·계산 선택','Choose a product'),('계약 조건 입력','Enter contract terms'),('손익과 가정 확인','Inspect payoff and assumptions'))),
    'fx': (
        ('환율과 금리 차이를 함께 살펴봐요', 'Explore exchange rates and rate differentials'),
        ('통화와 기간을 정해 환율 계약과 헤지의 가격·위험을 계산해요.',
         'Choose currencies and a horizon to examine FX contracts and hedging risk.'),
        (('통화·도구 선택','Choose currencies and a tool'),('환율·금리 입력','Enter FX rates and yields'),('가격·위험 비교','Compare value and risk'))),
    'derivatives': (
        ('파생상품 가격을 움직이는 요인은 무엇일까요?', 'What drives a derivative’s value?'),
        ('계약 조건과 변동성 가정을 바꿔 가격과 민감도가 어떻게 달라지는지 봐요.',
         'Vary contract terms and volatility assumptions to inspect value and sensitivity.'),
        (('계약·모형 선택','Choose a contract and model'),('조건·가정 입력','Enter terms and assumptions'),('가격·민감도 확인','Read value and sensitivities'))),
    'etf': (
        ('ETF의 구조와 위험을 알아봐요', 'Understand an ETF’s structure and risk'),
        ('ETF 자료와 선택한 분석 도구로 가격 흐름·구조·위험을 살펴봐요.',
         'Use ETF data and the selected tool to explore price behaviour, structure and risk.'),
        (('ETF·도구 선택','Choose an ETF and a tool'),('기간·조건 설정','Set the period and inputs'),('결과와 한계 확인','Read results and limitations'))),
    'krx': (
        ('국내 종목을 같은 기준으로 살펴봐요', 'Examine Korean stocks on a common basis'),
        ('국내 종목과 조회할 자료를 정하고 가격·지표를 확인해요.',
         'Choose a Korean listing and the data to inspect its prices and metrics.'),
        (('종목·자료 선택','Choose a stock and data'),('조회 조건 설정','Set the query'),('지표와 출처 확인','Read metrics and sources'))),
    'crypto': (
        ('크립토 시장의 움직임을 이해해요', 'Understand crypto market behaviour'),
        ('가격·변동성·펀딩 등 선택한 도구가 제공하는 자료를 비교해요.',
         'Compare the price, volatility or funding data available to the selected tool.'),
        (('자산·도구 선택','Choose an asset and tool'),('기간·가정 입력','Set period and assumptions'),('위험 요인 읽기','Read the risk factors'))),
    'macro': (
        ('경제 지표를 시장과 연결해 살펴봐요', 'Put economic indicators in market context'),
        ('금리·물가·성장 등 거시 자료의 수준과 변화를 함께 확인해요.',
         'Inspect levels and changes in macro data such as rates, inflation and growth.'),
        (('분석할 자료 선택','Choose the data'),('기간·조건 설정','Set the period and inputs'),('변화와 기준일 확인','Read changes and observation dates'))),
    'macro_records': (
        ('기록된 거시 자료를 확인해요', 'Explore recorded macro data'),
        ('선택한 기록 집합의 자료와 관측 기준을 확인해요.',
         'Inspect the selected record set and its observation basis.'),
        (('기록 집합 선택','Choose a record set'),('조회 조건 설정','Set the query'),('기록과 근거 읽기','Read records and evidence'))),
    'monte_carlo': (
        ('한 가지 예측 대신, 가능한 가격 범위를 봐요', 'Explore a range of possible prices'),
        ('종목·기간·모형을 정해 여러 가격 경로를 계산해요. 가정에 따른 시뮬레이션이며 미래 가격을 보장하지 않아요.',
         'Set an asset, horizon and model to simulate many paths. These are assumption-based scenarios, not guaranteed future prices.'),
        (('종목·가정 설정','Set the asset and assumptions'),('가격 경로 생성','Simulate price paths'),('분포·손실 위험 읽기','Read the distribution and loss risk'))),
    'strategy': (
        ('매매 아이디어를 검증 가능한 규칙으로 바꿔요', 'Turn an idea into a testable strategy'),
        ('정한 규칙을 과거 자료로 계산하고, 성과와 검증 근거를 함께 살펴봐요. 계산 완료와 검증 통과는 달라요.',
         'Evaluate rules on historical data and read performance alongside validation evidence. A completed calculation is not a validation pass.'),
        (('전략·조건 설정','Set strategy rules'),('계산 실행','Run the calculation'),('성과·검증 근거 확인','Read performance and evidence'))),
    'portfolio': (
        ('여러 자산을 함께 담았을 때의 위험을 봐요', 'Examine risk across a portfolio'),
        ('자산 구성과 조건을 정해 수익률·변동성·자산 간 관계를 살펴봐요.',
         'Set the asset mix and inputs to inspect returns, volatility and relationships between assets.'),
        (('자산·조건 설정','Choose assets and inputs'),('포트폴리오 분석','Analyse the portfolio'),('위험·가정 비교','Compare risk and assumptions'))),
    'signals': (
        ('여러 지표가 같은 이야기를 하고 있을까요?', 'Do different indicators agree?'),
        ('선택한 종목의 추세와 기술적 신호를 함께 읽어요. 참고용 분석이며 매수·매도 지시가 아니에요.',
         'Read trend and technical signals together. This is context, not an instruction to buy or sell.'),
        (('종목·기간 선택','Choose an asset and period'),('지표 분석','Analyse indicators'),('신호의 일치·차이 읽기','Compare agreement and divergence'))),
    'paper': (
        ('모의 환경에서 규칙의 작동을 확인해요', 'Observe your rules in a simulated environment'),
        ('실제 주문 없이 모의 실행과 기록을 확인해요. 모의 결과가 실거래 성과를 보장하지 않아요.',
         'Inspect simulated execution and records without live orders. Simulation results do not guarantee live performance.'),
        (('규칙·제한 확인','Review rules and limits'),('모의 실행','Run the simulation'),('기록·위험 확인','Inspect records and risk'))),
}


class WorkspaceGuide(QFrame):
    def __init__(self, key):
        super().__init__()
        self.setObjectName('workspaceGuide')
        self.setMaximumWidth(1100)
        column=QVBoxLayout(self);column.setContentsMargins(0,4,0,12);column.setSpacing(7)
        self.purpose=LocalLabel({},'workflowTitle');column.addWidget(self.purpose)
        self.scope=LocalLabel({},'caption');column.addWidget(self.scope)
        self.step_host=QWidget();self.steps_grid=QGridLayout(self.step_host)
        self.steps_grid.setContentsMargins(0,5,0,0);self.steps_grid.setSpacing(10)
        column.addWidget(self.step_host)
        self.steps=[]
        for i in range(3):
            host=QWidget();row=QHBoxLayout(host);row.setContentsMargins(0,0,0,0);row.setSpacing(8)
            number=LocalLabel({'ko':str(i+1),'en':str(i+1)},'workflowNumber')
            number.setAlignment(Qt.AlignmentFlag.AlignCenter);number.setFixedSize(20,20)
            title=LocalLabel({},'workflowStep');row.addWidget(number);row.addWidget(title,1)
            self.steps.append((host,title))
        self.set_key(key);self._reflow()

    def set_key(self,key):
        self.key=key
        purpose,scope,steps=GUIDES[key]
        for label,copy in ((self.purpose,purpose),(self.scope,scope),
                           *((self.steps[i][1],copy) for i,copy in enumerate(steps))):
            label.texts=dict(zip(('ko','en'),copy));label.sync()
        self.setAccessibleName(self.purpose.text())
        self.setAccessibleDescription(self.scope.text())
        self.updateGeometry()

    def _reserve_text_space(self):
        for label in (self.purpose,self.scope,*(title for _,title in self.steps)):label.sync()
        self.setAccessibleName(self.purpose.text())
        self.setAccessibleDescription(self.scope.text())

    def _reflow(self):
        columns=3 if self.width()>=650 else 1
        while self.steps_grid.count():self.steps_grid.takeAt(0)
        for i,(host,_) in enumerate(self.steps):
            self.steps_grid.addWidget(host,i//columns,i%columns,Qt.AlignmentFlag.AlignLeft)
        for col in range(4):self.steps_grid.setColumnStretch(col,int(col==columns))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if (event.size().width()>=650)!=(event.oldSize().width()>=650):self._reflow()

