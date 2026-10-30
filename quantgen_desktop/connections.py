"""Native connection status. Probes run only on explicit user action."""
from core.research.connections import ConnectionRequest
from .tools import ToolPane


class ConnectionsPane(ToolPane):
    def __init__(self):
        tools = [('presence', '설정 여부 확인 · 네트워크 조회 없음'), ('krx', 'KRX 접속 검사'),
                 ('ficc', 'FRED / Yahoo 접속 검사'), ('kis', 'KIS 자산 데이터 접속 검사'),
                 ('crypto', 'Upbit / Binance 공개 데이터 접속 검사')]
        super().__init__('데이터 연결', tools, [('configured', '기존 연결 사용')], {k: [] for k, _ in tools})
        self.run.setText('선택한 연결 확인')
        self.status.setText('설정 여부와 실제 응답을 구분합니다. 키 값은 표시하거나 저장하지 않습니다.')

    def make_request(self):
        return ConnectionRequest(self.tool.currentData())

    def show_result(self, output):
        self.clear_result()
        self.result_table('연결 상태', ['Provider', 'Status', '설정 이름 / 경로', '설명'], output.rows)
        if output.request.tool == 'presence':
            self.finished('CONFIGURED는 설정의 존재만 뜻합니다. 실제 접속 성공은 별도 검사로 확인하세요.')
        else:
            self.finished('읽기 전용 접속 검사 결과입니다. 계좌 조회·주문·연결 설정 변경은 수행하지 않습니다.')
        if not output.rows or any(r[1] == 'UNAVAILABLE' for r in output.rows):
            self.status.setText('검사 종료 · 응답 불가 항목이 있습니다.')
